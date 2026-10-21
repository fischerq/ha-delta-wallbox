"""Tests for the synchronous Delta AC MAX Modbus client."""

import pytest

from custom_components.delta_wallbox.client import DeltaWallboxClient
from custom_components.delta_wallbox.const import NO_LIMIT

from .fake_modbus import FakeModbus, charging_scenario


@pytest.fixture
def fake():
    f = FakeModbus()
    charging_scenario(f)
    return f


def test_read_state_decodes_evse_block(fake):
    data = DeltaWallboxClient("h", 502, 1, client=fake).read_state()
    assert data["charger_state"] == "operational"
    assert data["charge_state"] == "charging"
    assert data["charging"] is True
    assert data["charging_power"] == 7400
    assert data["output_voltage"] == 230.1
    assert data["output_current"] == 32.0
    assert data["charging_time"] == 1800
    assert data["charged_energy"] == 3200
    assert data["power_limit"] is None  # 0xFFFFFFFF = no limit
    assert data["suspended"] is False


def test_serial_stops_at_nul(fake):
    assert DeltaWallboxClient("h", 502, 1, client=fake).read_serial() == "DELTA123"


def test_power_limit_written_as_two_registers_and_read_back(fake):
    client = DeltaWallboxClient("h", 502, 1, client=fake)
    client.set_power_limit(11000)
    assert fake.writes[-1] == (1600, [0, 11000])
    assert client.read_state()["power_limit"] == 11000
    client.set_power_limit(70000)
    assert fake.writes[-1] == (1600, [1, 70000 - 65536])
    assert client.read_state()["power_limit"] == 70000


def test_none_removes_the_limit(fake):
    client = DeltaWallboxClient("h", 502, 1, client=fake)
    client.set_power_limit(None)
    assert fake.writes[-1] == (1600, [NO_LIMIT >> 16, NO_LIMIT & 0xFFFF])


def test_negative_limit_rejected(fake):
    with pytest.raises(ValueError):
        DeltaWallboxClient("h", 502, 1, client=fake).set_power_limit(-5)


def test_suspend_and_resume(fake):
    client = DeltaWallboxClient("h", 502, 1, client=fake)
    client.set_suspended(True)
    assert fake.writes[-1] == (1602, [1])
    assert client.read_state()["suspended"] is True
    client.set_suspended(False)
    assert client.read_state()["suspended"] is False


def test_errors_raise(fake):
    client = DeltaWallboxClient("h", 502, 1, client=fake)
    fake.fail = True
    with pytest.raises(Exception):
        client.read_state()
    with pytest.raises(Exception):
        client.set_power_limit(1000)
