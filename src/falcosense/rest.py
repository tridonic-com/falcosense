"""REST (HTTPS) client for the FalcoSENSE device.

The device serves a self-signed certificate, so TLS verification is disabled by
default. The REST API is used for config-flow validation and the initial
snapshot of static information; live metadata arrives over MQTT.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

import aiohttp

from .const import (
    DEFAULT_HTTPS_PORT,
    REST_AUTHENTICATE_MQTT,
    REST_DEVICE_NAME,
    REST_RESET_TIME,
    REST_TIMEZONE,
    REST_VERSION,
)
from .exceptions import FalcoSenseAuthError, FalcoSenseConnectionError


class FalcoSenseRestClient:
    """Minimal async REST client for the FalcoSENSE device."""

    def __init__(
        self,
        host: str,
        token: str,
        session: aiohttp.ClientSession,
        *,
        port: int = DEFAULT_HTTPS_PORT,
        verify_ssl: bool = False,
        request_timeout: float = 10.0,
    ) -> None:
        """Initialize the REST client."""
        self._base = f"https://{host}:{port}"
        self._token = token
        self._session = session
        self._verify_ssl = verify_ssl
        self._timeout = aiohttp.ClientTimeout(total=request_timeout)

    async def _get(self, path: str) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.get(
                f"{self._base}/{path}",
                headers=headers,
                ssl=self._verify_ssl,
                timeout=self._timeout,
            ) as response:
                if response.status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                    raise FalcoSenseAuthError(f"Unauthorized for {path}")
                response.raise_for_status()
                data: dict[str, Any] = await response.json()
                return data
        except FalcoSenseAuthError:
            raise
        except aiohttp.ClientResponseError as err:
            raise FalcoSenseConnectionError(str(err)) from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise FalcoSenseConnectionError(str(err)) from err

    async def async_get_version(self) -> str | None:
        """Return the firmware/runtime version string."""
        data = await self._get(REST_VERSION)
        # Firmware 2.0.8 nested the key with a trailing space; 2.0.16 is flat.
        return data.get("version") or data.get("version ")

    async def async_get_device_name(self) -> str | None:
        """Return the device name."""
        data = await self._get(REST_DEVICE_NAME)
        return data.get("device_name") or data.get("device_name ")

    async def async_get_timezone(self) -> str | None:
        """Return the configured time zone."""
        data = await self._get(REST_TIMEZONE)
        timezone = data.get("timezone")
        if isinstance(timezone, dict):
            return timezone.get("timezone")
        return timezone

    async def async_get_reset_time(self) -> str | None:
        """Return the daily metadata reset time."""
        data = await self._get(REST_RESET_TIME)
        reset = data.get("reset_time")
        if isinstance(reset, dict):
            return reset.get("resetTime")
        return reset

    async def async_authenticate_mqtt(self, username: str, password: str = "") -> None:
        """Validate MQTT credentials, raising on failure."""
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with self._session.post(
                f"{self._base}/{REST_AUTHENTICATE_MQTT}",
                headers=headers,
                json={"username": username, "password": password},
                ssl=self._verify_ssl,
                timeout=self._timeout,
            ) as response:
                if response.status == HTTPStatus.OK:
                    return
                if response.status in (
                    HTTPStatus.BAD_REQUEST,
                    HTTPStatus.UNAUTHORIZED,
                    HTTPStatus.FORBIDDEN,
                ):
                    raise FalcoSenseAuthError("MQTT authentication rejected")
                response.raise_for_status()
        except FalcoSenseAuthError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise FalcoSenseConnectionError(str(err)) from err
