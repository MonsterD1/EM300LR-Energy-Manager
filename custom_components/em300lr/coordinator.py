"""Data update coordinator for the EM300 LR."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EM300AuthError, EM300Client, EM300Error
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type EM300ConfigEntry = ConfigEntry[EM300Coordinator]


class EM300Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """One request per interval for all entities."""

    config_entry: EM300ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: EM300ConfigEntry, client: EM300Client
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.fetch()
        except EM300AuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except EM300Error as err:
            raise UpdateFailed(str(err)) from err
