"""Tests for the EM300 LR integration."""

import json

import aiohttp
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.em300lr.api import EM300Client
from custom_components.em300lr.const import DOMAIN

from .conftest import DATA, HOST, START


async def test_config_flow(hass: HomeAssistant, em300_mock) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PASSWORD: ""}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "72102414"
    assert result["title"] == "BControlEM300"


async def test_config_flow_cannot_connect(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"http://{HOST}/start.php", exc=aiohttp.ClientError)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PASSWORD: ""}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_setup_entities(hass: HomeAssistant, em300_mock) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="72102414", data={CONF_HOST: HOST, CONF_PASSWORD: ""}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    reg = er.async_get(hass)
    entities = er.async_entries_for_config_entry(reg, entry.entry_id)
    assert len(entities) == 59
    enabled = sorted(e.entity_id for e in entities if not e.disabled)
    assert enabled == [
        "sensor.bcontrolem300_active_energy_minus",
        "sensor.bcontrolem300_active_energy_plus",
        "sensor.bcontrolem300_active_power_minus",
        "sensor.bcontrolem300_active_power_plus",
    ]
    # disabled ones keep the old template entity_ids too
    assert reg.async_get("sensor.bcontrolem300_l1_voltage")
    assert reg.async_get("sensor.bcontrolem300_power_factor")

    state = hass.states.get("sensor.bcontrolem300_active_power_minus")
    assert float(state.state) == 2302.9
    assert state.attributes["unit_of_measurement"] == "W"
    energy = hass.states.get("sensor.bcontrolem300_active_energy_plus")
    assert energy.attributes["state_class"] == "total_increasing"
    assert energy.attributes["unit_of_measurement"] == "Wh"


class _FakeResp:
    def __init__(self, payload):
        self._text = json.dumps(payload)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    async def text(self):
        return self._text


class _FakeSession:
    """Serves start.php always, data.php from a queue."""

    def __init__(self, data_responses):
        self.data_responses = list(data_responses)
        self.calls = []

    def request(self, method, url, data=None):
        self.calls.append((method, url.rsplit("/", 1)[-1]))
        if url.endswith("start.php"):
            return _FakeResp(START)
        return _FakeResp(self.data_responses.pop(0))


async def test_session_reused_and_renewed() -> None:
    session = _FakeSession([DATA, DATA, {"authentication": False}, DATA])
    client = EM300Client(session, HOST)

    await client.fetch()
    await client.fetch()
    # login only once for two polls
    assert [c[1] for c in session.calls] == ["start.php", "data.php", "data.php"]

    session.calls.clear()
    data = await client.fetch()  # expired -> re-login -> retry
    assert data["status"] == 0
    assert [c[1] for c in session.calls] == ["data.php", "start.php", "data.php"]
