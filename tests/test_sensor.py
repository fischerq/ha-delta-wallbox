
import pytest
from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.delta_wallbox.const import (
    DOMAIN,
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SLAVE_ID,
)
from custom_components.delta_wallbox.coordinator import DeltaWallboxDataUpdateCoordinator
from custom_components.delta_wallbox.sensor import (
    SENSOR_TYPES,
    DeltaWallboxSensor,
    async_setup_entry,
)

MOCK_SLAVE_ID = 1
MOCK_ENTRY_ID = "test_entry_id"


@pytest.fixture
def mock_coordinator(hass: HomeAssistant):
    """Mock DeltaWallboxDataUpdateCoordinator."""
    coordinator = MagicMock(spec=DeltaWallboxDataUpdateCoordinator)
    coordinator.hass = hass
    coordinator.slave_id = MOCK_SLAVE_ID
    # Populate with some mock data for all sensors
    coordinator.data = {desc.key: f"mock_{desc.key}" for desc in SENSOR_TYPES}
    coordinator.data["charging_power"] = 1500
    coordinator.data["soc"] = 80.5

    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=MOCK_ENTRY_ID,
        data={
            CONF_IP_ADDRESS: "1.2.3.4",
            CONF_PORT: 502,
            CONF_SLAVE_ID: MOCK_SLAVE_ID,
        },
    )
    coordinator.config_entry = mock_config_entry
    return coordinator


@pytest.fixture
def mock_config_entry_obj() -> MockConfigEntry:
    """Return a mock ConfigEntry object."""
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id=MOCK_ENTRY_ID,
        data={
            CONF_IP_ADDRESS: "1.2.3.4",
            CONF_PORT: 502,
            CONF_SLAVE_ID: MOCK_SLAVE_ID,
        },
        title="Delta Wallbox",
    )


async def test_async_setup_entry(
    hass: HomeAssistant, mock_coordinator, mock_config_entry_obj: MockConfigEntry
):
    """Test the sensor platform setup."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry_obj.entry_id] = mock_coordinator

    async_add_entities_mock = MagicMock()

    await async_setup_entry(hass, mock_config_entry_obj, async_add_entities_mock)

    async_add_entities_mock.assert_called_once()
    entities = async_add_entities_mock.call_args.args[0]
    assert len(entities) == len(SENSOR_TYPES)
    assert all(isinstance(e, DeltaWallboxSensor) for e in entities)


async def test_sensor_properties(hass: HomeAssistant, mock_coordinator):
    """Test properties of a DeltaWallboxSensor."""
    # Test a representative sensor
    description = next(d for d in SENSOR_TYPES if d.key == "charger_state")

    sensor = DeltaWallboxSensor(mock_coordinator, description)
    sensor.hass = hass

    # Test basic properties
    assert sensor.coordinator == mock_coordinator
    assert sensor.entity_description == description
    assert sensor.unique_id == f"{MOCK_SLAVE_ID}_{description.key}"

    # Test device info
    device_info = sensor.device_info
    assert device_info is not None
    assert device_info["identifiers"] == {(DOMAIN, MOCK_SLAVE_ID)}
    assert device_info["name"] == "Delta Wallbox"
    assert device_info["manufacturer"] == "Delta"

    # Test value property
    assert sensor.native_value == mock_coordinator.data.get(description.key)

    # Test another sensor with specific data
    power_desc = next(d for d in SENSOR_TYPES if d.key == "charging_power")
    power_sensor = DeltaWallboxSensor(mock_coordinator, power_desc)
    assert power_sensor.native_value == 1500
