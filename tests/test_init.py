"""End-to-end tests: real config entry, real platforms, fake Modbus."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.delta_wallbox.client import DeltaWallboxClient
from custom_components.delta_wallbox.const import DOMAIN

from .const import MOCK_IP_ADDRESS, MOCK_PORT, MOCK_SLAVE_ID
from .fake_modbus import FakeModbus, charging_scenario


@pytest.fixture
def fake():
    f = FakeModbus()
    charging_scenario(f)
    return f


@pytest.fixture
async def entry(hass: HomeAssistant, fake):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "ip_address": MOCK_IP_ADDRESS,
            "port": MOCK_PORT,
            "slave_id": MOCK_SLAVE_ID,
        },
    )
    entry.add_to_hass(hass)

    def make_client(host, port, device_id):
        return DeltaWallboxClient(host, port, device_id, client=fake)

    with patch(
        "custom_components.delta_wallbox.DeltaWallboxClient", side_effect=make_client
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry


def entity_id(hass, domain, key):
    from homeassistant.helpers import entity_registry as er

    return er.async_get(hass).async_get_entity_id(
        domain, DOMAIN, f"{MOCK_SLAVE_ID}_{key}"
    )


async def test_setup_creates_entities_with_live_values(hass: HomeAssistant, entry):
    assert entry.state is ConfigEntryState.LOADED
    power = hass.states.get(entity_id(hass, "sensor", "charging_power"))
    assert power.state == "7400"
    assert power.attributes["unit_of_measurement"] == "W"
    assert (
        hass.states.get(entity_id(hass, "sensor", "charge_state")).state == "charging"
    )
    assert hass.states.get(entity_id(hass, "switch", "charging_enabled")).state == "on"


async def test_set_power_limit_writes_register_1600(hass: HomeAssistant, entry, fake):
    eid = entity_id(hass, "number", "power_limit")
    await hass.services.async_call(
        "number", "set_value", {"entity_id": eid, "value": 4200}, blocking=True
    )
    await hass.async_block_till_done()
    assert (1600, [0, 4200]) in fake.writes
    assert float(hass.states.get(eid).state) == 4200


async def test_switch_off_suspends(hass: HomeAssistant, entry, fake):
    eid = entity_id(hass, "switch", "charging_enabled")
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": eid}, blocking=True
    )
    await hass.async_block_till_done()
    assert (1602, [1]) in fake.writes
    assert hass.states.get(eid).state == "off"


async def test_failed_write_raises(hass: HomeAssistant, entry, fake):
    from homeassistant.exceptions import HomeAssistantError

    fake.fail = True
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id(hass, "number", "power_limit"), "value": 1000},
            blocking=True,
        )


async def test_unload_closes_client(hass: HomeAssistant, entry, fake):
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert fake.closed


async def test_device_offline_retries(hass: HomeAssistant):
    offline = FakeModbus()
    offline.fail = True
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "ip_address": MOCK_IP_ADDRESS,
            "port": MOCK_PORT,
            "slave_id": MOCK_SLAVE_ID,
        },
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.delta_wallbox.DeltaWallboxClient",
        side_effect=lambda h, p, d: DeltaWallboxClient(h, p, d, client=offline),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.SETUP_RETRY
