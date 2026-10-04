"""B-Control EM300 LR Energy Manager integration."""

from __future__ import annotations

from aiohttp import CookieJar
from homeassistant.const import CONF_HOST, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import EM300Client
from .coordinator import EM300ConfigEntry, EM300Coordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: EM300ConfigEntry) -> bool:
    """Set up the EM300 from a config entry."""
    # Own session: the device sets its session cookie on a bare IP, which the
    # shared session's cookie jar would reject.
    session = async_create_clientsession(
        hass, auto_cleanup=False, cookie_jar=CookieJar(unsafe=True)
    )
    entry.async_on_unload(session.close)
    client = EM300Client(
        session, entry.data[CONF_HOST], entry.data.get(CONF_PASSWORD, "")
    )
    coordinator = EM300Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EM300ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: EM300ConfigEntry) -> None:
    """Reload after the options (scan interval) changed."""
    await hass.config_entries.async_reload(entry.entry_id)
