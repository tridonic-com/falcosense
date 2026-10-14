"""MQTT (WebSocket over TLS) client for the FalcoSENSE device.

The device runs its own broker; no external broker is required. It is reached
over a TLS WebSocket on ``MQTT_WEBSOCKET_PATH``. Authentication uses the API
token as the username with **no password** (an empty password is rejected).
"""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
from collections.abc import Callable

import aiomqtt

from .const import (
    DEFAULT_MQTT_PORT,
    MQTT_WEBSOCKET_PATH,
    REQUEST_ANNOTATIONS_PAYLOAD,
    SUBSCRIBE_TOPICS,
    TOPIC_ALL_METADATA,
    TOPIC_ANNOTATIONS,
    TOPIC_AREAS_STATUS,
    TOPIC_FRAME_DEBUG,
    TOPIC_GET_ANNOTATIONS,
    TOPIC_LINES_STATUS,
    TOPIC_RUNTIME_STATUS,
    TOPIC_SOLUTION_INFO,
)
from .models import FalcoSenseState
from .parser import (
    apply_all_metadata,
    apply_annotations,
    apply_areas_status,
    apply_lines_status,
    apply_runtime_status,
    apply_solution_info,
)

_LOGGER = logging.getLogger(__name__)

_RECONNECT_INTERVAL = 10.0


def _insecure_tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


class FalcoSenseMqttClient:
    """Maintain a live subscription to the device's MQTT broker."""

    def __init__(
        self,
        host: str,
        token: str,
        state: FalcoSenseState,
        on_update: Callable[[], None],
        *,
        port: int = DEFAULT_MQTT_PORT,
        identifier: str = "homeassistant-falcosense",
    ) -> None:
        """Initialize the MQTT client."""
        self._host = host
        self._token = token
        self._state = state
        self._on_update = on_update
        self._port = port
        self._identifier = identifier
        self._task: asyncio.Task[None] | None = None
        self.connected = asyncio.Event()
        self.metadata_received = asyncio.Event()

    async def async_start(self) -> None:
        """Start the background reconnect loop."""
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def async_stop(self) -> None:
        """Stop the background loop and wait for it to finish."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        self.connected.clear()

    async def _run(self) -> None:
        while True:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                raise
            except aiomqtt.MqttError as err:
                self.connected.clear()
                _LOGGER.debug("MQTT connection lost, reconnecting: %s", err)
                await asyncio.sleep(_RECONNECT_INTERVAL)

    async def _connect_and_listen(self) -> None:
        client = aiomqtt.Client(
            hostname=self._host,
            port=self._port,
            username=self._token,
            password=None,
            transport="websockets",
            websocket_path=MQTT_WEBSOCKET_PATH,
            tls_context=_insecure_tls_context(),
            identifier=self._identifier,
        )
        async with client:
            for topic in SUBSCRIBE_TOPICS:
                await client.subscribe(topic)
            # Annotations (shape geometry) are only published on request.
            await client.publish(TOPIC_GET_ANNOTATIONS, REQUEST_ANNOTATIONS_PAYLOAD)
            self.connected.set()
            async for message in client.messages:
                self._handle_message(str(message.topic), message.payload)

    def _handle_message(self, topic: str, payload: object) -> None:
        if topic == TOPIC_FRAME_DEBUG:
            # Raw JPEG; read on demand by the camera, so no listener notification.
            if isinstance(payload, (bytes, bytearray)):
                self._state.camera_frame = bytes(payload)
            return
        if not isinstance(payload, (bytes, bytearray, str)):
            return
        try:
            data = json.loads(payload)
        except (ValueError, TypeError):
            _LOGGER.debug("Ignoring non-JSON payload on %s", topic)
            return
        if not isinstance(data, dict):
            return
        if topic == TOPIC_ALL_METADATA:
            apply_all_metadata(self._state, data)
            self.metadata_received.set()
        elif topic == TOPIC_ANNOTATIONS:
            apply_annotations(self._state, data)
        elif topic == TOPIC_AREAS_STATUS:
            apply_areas_status(self._state, data)
        elif topic == TOPIC_LINES_STATUS:
            apply_lines_status(self._state, data)
        elif topic == TOPIC_RUNTIME_STATUS:
            apply_runtime_status(self._state, data)
        elif topic == TOPIC_SOLUTION_INFO:
            apply_solution_info(self._state, data)
        else:
            return
        self._on_update()
