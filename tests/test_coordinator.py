"""Tests for the Delta Wallbox coordinator."""

from homeassistant.core import HomeAssistant

from custom_components.delta_wallbox.client import DeltaWallboxClient
from custom_components.delta_wallbox.coordinator import (
    DeltaWallboxDataUpdateCoordinator,
)

from .fake_modbus import FakeModbus, charging_scenario


async def test_update_reads_serial_once_and_state_every_time(hass: HomeAssistant):
    fake = FakeModbus()
    charging_scenario(fake)
    coordinator = DeltaWallboxDataUpdateCoordinator(
        hass, DeltaWallboxClient("h", 502, 1, client=fake)
    )
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.data["charging_power"] == 7400
    assert coordinator.data["charger_serial_number"] == "DELTA123"

    fake.input[110] = ord("X")
    await coordinator.async_refresh()
    assert coordinator.data["charger_serial_number"] == "DELTA123"


async def test_update_failure_marks_unavailable(hass: HomeAssistant):
    fake = FakeModbus()
    fake.fail = True
    coordinator = DeltaWallboxDataUpdateCoordinator(
        hass, DeltaWallboxClient("h", 502, 1, client=fake)
    )
    await coordinator.async_refresh()
    assert coordinator.last_update_success is False
