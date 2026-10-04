"""Diagnostics for the EM300 LR."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .coordinator import EM300ConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EM300ConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), {CONF_PASSWORD}),
        "options": dict(entry.options),
        "app_version": coordinator.client.app_version,
        "data": coordinator.data,
    }
