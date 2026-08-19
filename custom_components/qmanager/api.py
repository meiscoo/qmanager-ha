"""Thin async client for a QManager instance running on a Quectel modem."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    ENDPOINT_CELL_SCAN_START,
    ENDPOINT_CELL_SCAN_STATUS,
    ENDPOINT_FETCH_DATA,
    ENDPOINT_LOGIN,
    ENDPOINT_SEND_COMMAND,
)

_LOGGER = logging.getLogger(__name__)


class QManagerError(Exception):
    """Base error for QManager API problems."""


class QManagerAuthError(QManagerError):
    """Raised when login fails (bad password) or the session can't be renewed."""


class QManagerConnectionError(QManagerError):
    """Raised when the modem can't be reached at all."""


class QManagerApiClient:
    """Talks to a single QManager instance over HTTP(S), handling cookie login."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        password: str,
        use_ssl: bool = False,
    ) -> None:
        self._session = session
        self._password = password
        scheme = "https" if use_ssl else "http"
        self._base_url = f"{scheme}://{host}:{port}"
        self._logged_in = False

    async def async_login(self) -> None:
        """Authenticate and obtain a qm_session cookie."""
        try:
            resp = await self._session.post(
                self._base_url + ENDPOINT_LOGIN,
                json={"password": self._password},
                timeout=aiohttp.ClientTimeout(total=15),
            )
        except aiohttp.ClientError as err:
            raise QManagerConnectionError(str(err)) from err

        async with resp:
            try:
                data = await resp.json(content_type=None)
            except (aiohttp.ContentTypeError, ValueError) as err:
                raise QManagerConnectionError(
                    f"Unexpected login response ({resp.status})"
                ) from err

            if resp.status != 200 or not data.get("success"):
                self._logged_in = False
                _LOGGER.debug(
                    "QManager login failed: status=%s body=%r", resp.status, data
                )
                raise QManagerAuthError(data.get("detail", "Login failed"))

        self._logged_in = True

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        retry_on_auth_fail: bool = True,
    ) -> dict[str, Any]:
        if not self._logged_in:
            await self.async_login()

        try:
            resp = await self._session.request(
                method,
                self._base_url + endpoint,
                json=json,
                timeout=aiohttp.ClientTimeout(total=20),
            )
        except aiohttp.ClientError as err:
            raise QManagerConnectionError(str(err)) from err

        async with resp:
            if resp.status == 401 and retry_on_auth_fail:
                self._logged_in = False
                await self.async_login()
                return await self._request(
                    method, endpoint, json=json, retry_on_auth_fail=False
                )

            if resp.status == 401:
                raise QManagerAuthError("Session rejected after re-login")

            try:
                data = await resp.json(content_type=None)
            except (aiohttp.ContentTypeError, ValueError) as err:
                raise QManagerConnectionError(
                    f"Unexpected response ({resp.status}) from {endpoint}"
                ) from err

            if resp.status >= 500:
                raise QManagerConnectionError(
                    f"QManager returned {resp.status} for {endpoint}"
                )

            return data

    async def async_get_status(self) -> dict[str, Any]:
        """Return the cached ModemStatus blob from the poller."""
        return await self._request("GET", ENDPOINT_FETCH_DATA)

    async def async_send_at_command(self, command: str) -> str:
        """Send a raw AT command and return the modem's response text."""
        data = await self._request(
            "POST", ENDPOINT_SEND_COMMAND, json={"command": command}
        )
        if not data.get("success"):
            raise QManagerError(data.get("detail", "AT command failed"))
        return data.get("response", "")

    async def async_start_cell_scan(self) -> None:
        """Kick off the cell scanner daemon."""
        data = await self._request("POST", ENDPOINT_CELL_SCAN_START)
        if not data.get("success"):
            raise QManagerError(data.get("detail", "Failed to start cell scan"))

    async def async_get_cell_scan_status(self) -> dict[str, Any]:
        """Return the current cell scan status/results."""
        return await self._request("GET", ENDPOINT_CELL_SCAN_STATUS)
