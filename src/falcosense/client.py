"""High-level FalcoSENSE client combining the REST and MQTT APIs."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import aiohttp

from .models import FalcoSenseState
from .mqtt import FalcoSenseMqttClient
from .rest import FalcoSenseRestClient

_CONNECT_TIMEOUT = 15.0


class FalcoSense:
    """Facade that validates, connects and exposes live device state."""

    def __init__(
        self,
        host: str,
        token: str,
        session: aiohttp.ClientSession,
        *,
        verify_ssl: bool = False,
    ) -> None:
        """Initialize the client."""
        self._host = host
        self._token = token
        self.state = FalcoSenseState()
        self._rest = FalcoSenseRestClient(host, token, session, verify_ssl=verify_ssl)
        self._mqtt = FalcoSenseMqttClient(host, token, self.state, self._notify)
        self._listeners: list[Callable[[], None]] = []

    async def async_validate(self) -> str:
        """Validate connectivity and credentials, returning the device name.

        Raises :class:`FalcoSenseConnectionError` or
        :class:`FalcoSenseAuthError` on failure.
        """
        await self._rest.async_authenticate_mqtt(self._token)
        device = self.state.device
        device.firmware_version = await self._rest.async_get_version()
        device.name = await self._rest.async_get_device_name()
        device.timezone = await self._rest.async_get_timezone()
        device.reset_time = await self._rest.async_get_reset_time()
        if not device.name:
            device.name = self._host
        return device.name

    async def async_connect(self) -> None:
        """Start the MQTT subscription and wait for the first connection."""
        await self._mqtt.async_start()
        try:
            async with asyncio.timeout(_CONNECT_TIMEOUT):
                await self._mqtt.connected.wait()
        except TimeoutError:
            # Keep retrying in the background; metadata will arrive once up.
            pass

    async def async_disconnect(self) -> None:
        """Stop the MQTT subscription."""
        await self._mqtt.async_stop()

    def add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a listener invoked on every state update.

        Returns a function that removes the listener.
        """
        self._listeners.append(callback)

        def remove() -> None:
            self._listeners.remove(callback)

        return remove

    def _notify(self) -> None:
        for callback in list(self._listeners):
            callback()
