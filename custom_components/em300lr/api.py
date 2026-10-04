"""Minimal async client for the B-Control EM300 LR web service.

Protocol (firmware 2.04):
  GET  /start.php                 -> session cookie + {"serial", "auth_mode", "authentication"}
  POST /start.php login=&password -> only needed if "authentication" is false
  GET  /mum-webservice/data.php   -> all OBIS values, or {"authentication": false}
                                     once the session has expired
The session is kept and only renewed when the device reports it as expired.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import aiohttp

from .const import REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class EM300Error(Exception):
    """Base error."""


class EM300ConnectionError(EM300Error):
    """Device not reachable or returned garbage."""


class EM300AuthError(EM300Error):
    """Login rejected."""


class EM300Client:
    """Talks to one EM300 LR."""

    def __init__(
        self, session: aiohttp.ClientSession, host: str, password: str = ""
    ) -> None:
        self._session = session
        self._base = f"http://{host}"
        self._password = password
        self._logged_in = False
        self.serial: str | None = None
        self.app_version: str | None = None

    async def _request(
        self, method: str, path: str, data: dict[str, str] | None = None
    ) -> dict[str, Any]:
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT.total_seconds()):
                async with self._session.request(
                    method, f"{self._base}{path}", data=data
                ) as resp:
                    resp.raise_for_status()
                    # Device sends JSON as text/html and sometimes a trailing '#'
                    text = (await resp.text()).strip().rstrip("#")
        except (aiohttp.ClientError, TimeoutError) as err:
            raise EM300ConnectionError(f"{method} {path} failed: {err}") from err
        try:
            return json.loads(text)
        except ValueError as err:
            raise EM300ConnectionError(f"Invalid JSON from {path}") from err

    async def login(self) -> dict[str, Any]:
        """Open a session; returns the start.php info."""
        info = await self._request("GET", "/start.php")
        self.serial = str(info.get("serial") or info.get("ieq_serial") or "")
        self.app_version = info.get("app_version")
        if not info.get("authentication"):
            info = await self._request(
                "POST",
                "/start.php",
                {"login": self.serial, "password": self._password},
            )
            if not info.get("authentication"):
                raise EM300AuthError("Login rejected (check password)")
        if not self.serial:
            raise EM300ConnectionError("No serial in start.php response")
        self._logged_in = True
        _LOGGER.debug("Session opened for EM300 %s", self.serial)
        return info

    async def fetch(self) -> dict[str, Any]:
        """Return all values; renews the session only when needed."""
        if not self._logged_in:
            await self.login()
        data = await self._request("GET", "/mum-webservice/data.php")
        if data.get("authentication") is False:
            _LOGGER.debug("Session expired, logging in again")
            self._logged_in = False
            await self.login()
            data = await self._request("GET", "/mum-webservice/data.php")
            if data.get("authentication") is False:
                raise EM300AuthError("Session rejected after re-login")
        return data
