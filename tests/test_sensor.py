import pytest
from unittest.mock import MagicMock, patch

import pytest
from unittest.mock import MagicMock, patch

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.entity_component import (
    async_update_entity,
)  # For potential future use
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)  # Module level import

from custom_components.braiins_pool.const import (
    DOMAIN,
    CONF_REWARDS_ACCOUNT_NAME,
    SATOSHIS_PER_BTC,
)
from custom_components.braiins_pool.sensor import SENSOR_TYPES, BraiinsPoolSensor
from custom_components.braiins_pool.coordinator import BraiinsDataUpdateCoordinator

MOCK_API_KEY = "test_api_key_789"
MOCK_REWARDS_ACCOUNT_NAME = "My Miner Sensors"
MOCK_ENTRY_ID = "sensor_entry_1"


@pytest.fixture
def mock_config_entry_data():
    """Provide mock config entry data."""
    return {
        CONF_API_KEY: MOCK_API_KEY,
        CONF_REWARDS_ACCOUNT_NAME: MOCK_REWARDS_ACCOUNT_NAME,
    }


@pytest.fixture
def mock_coordinator(hass, mock_config_entry_data):
    """Mock BraiinsDataUpdateCoordinator."""
    coordinator = MagicMock(spec=BraiinsDataUpdateCoordinator)
    coordinator.hass = hass
    coordinator.data = {  # Mock some data for sensors
        "today_reward": 0.001,
        "current_balance": 0.05,
        "all_time_reward": 1.23,
        "pool_5m_hash_rate": 5000,
        "ok_workers": 2,
        "today_reward_satoshi": 100000,  # 0.001 * SATOSHIS_PER_BTC
        "current_balance_satoshi": 5000000,  # 0.05 * SATOSHIS_PER_BTC
        "all_time_reward_satoshi": 123000000,  # 1.23 * SATOSHIS_PER_BTC
    }
    coordinator.config_entry = MagicMock(spec=ConfigEntry)
    coordinator.config_entry.data = mock_config_entry_data
    coordinator.config_entry.entry_id = MOCK_ENTRY_ID
    return coordinator


@pytest.fixture
def mock_config_entry_obj(mock_config_entry_data):
    """Returns a mock ConfigEntry object"""
    entry = MagicMock(spec=ConfigEntry)
    entry.data = mock_config_entry_data
    entry.entry_id = MOCK_ENTRY_ID
    entry.title = MOCK_REWARDS_ACCOUNT_NAME
    return entry


async def test_sensor_creation_and_device_info(
    hass: HomeAssistant, mock_coordinator, mock_config_entry_obj
):
    """Test sensor creation and device info."""

    # Store coordinator in hass.data as sensor.py expects
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][MOCK_ENTRY_ID] = mock_coordinator

    entities = []
    async_add_entities_mock = MagicMock(side_effect=lambda x: entities.extend(x))

    # Simulate setup from sensor.py's async_setup_entry
    # We directly create sensors here for testing their properties
    sensors_to_create = [
        BraiinsPoolSensor(mock_coordinator, description, mock_config_entry_obj)
        for description in SENSOR_TYPES
    ]
    async_add_entities_mock(
        sensors_to_create
    )  # Call the mock to populate entities list

    assert len(entities) == len(SENSOR_TYPES)

    for entity in entities:
        assert isinstance(entity, BraiinsPoolSensor)
        assert entity.coordinator == mock_coordinator
        assert entity.unique_id == f"{MOCK_ENTRY_ID}_{entity.entity_description.key}"

        # Check device_info
        device_info = entity.device_info
        assert device_info is not None
        assert device_info["identifiers"] == {(DOMAIN, MOCK_ENTRY_ID)}
        assert device_info["name"] == MOCK_REWARDS_ACCOUNT_NAME
        assert device_info["manufacturer"] == "Braiins"

        # Check native value
        assert entity.native_value == mock_coordinator.data.get(
            entity.entity_description.key
        )


async def test_sensor_keyerror_fix(
    hass: HomeAssistant, mock_coordinator, mock_config_entry_obj
):
    """Test that the KeyError during setup is fixed.
    This is implicitly tested by test_sensor_creation_and_device_info
    if it runs without a KeyError. This test explicitly calls the setup
    function that was failing.
    """
    from custom_components.braiins_pool.sensor import (
        async_setup_entry as sensor_async_setup_entry,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][
        mock_config_entry_obj.entry_id
    ] = mock_coordinator  # Ensure coordinator is there

    async_add_entities_mock = MagicMock()

    try:
        await sensor_async_setup_entry(
            hass, mock_config_entry_obj, async_add_entities_mock
        )
    except KeyError as e:
        pytest.fail(f"KeyError should not occur: {e}")

    async_add_entities_mock.assert_called_once()
    # Further assertions can be made on the entities passed to async_add_entities_mock if needed


@pytest.mark.usefixtures()
def test_sensor_types_attributes():
    """Test the attributes of SENSOR_TYPES, including new Satoshi sensors."""
    # SensorDeviceClass and SensorStateClass are now imported at module level

    monetary_btc_sensors = ["today_reward", "current_balance", "all_time_reward"]
    monetary_satoshi_sensors = [
        "today_reward_satoshi",
        "current_balance_satoshi",
        "all_time_reward_satoshi",
    ]

    for description in SENSOR_TYPES:
        if description.key in monetary_btc_sensors:
            assert (
                description.device_class == SensorDeviceClass.MONETARY
            ), f"Sensor {description.key} should have MONETARY device class"
            assert (
                description.state_class == SensorStateClass.TOTAL
            ), f"Sensor {description.key} should have TOTAL state class"
            assert (
                description.native_unit_of_measurement == "BTC"
            ), f"Sensor {description.key} should have BTC unit"
        elif description.key in monetary_satoshi_sensors:
            assert (
                description.device_class == SensorDeviceClass.MONETARY
            ), f"Sensor {description.key} should have MONETARY device class"
            assert (
                description.state_class == SensorStateClass.TOTAL
            ), f"Sensor {description.key} should have TOTAL state class"
            assert (
                description.native_unit_of_measurement == "Satoshi"
            ), f"Sensor {description.key} should have Satoshi unit"
        elif description.key == "pool_5m_hash_rate":
            assert (
                description.device_class == SensorDeviceClass.DATA_RATE
            ), f"Sensor {description.key} should have DATA_RATE device class"
            assert (
                description.state_class == SensorStateClass.MEASUREMENT
            ), f"Sensor {description.key} should have MEASUREMENT state class"
        elif description.key == "ok_workers":
            assert (
                description.state_class == SensorStateClass.MEASUREMENT
            ), f"Sensor {description.key} should have MEASUREMENT state class"
            # Assuming no specific device_class for ok_workers
            assert (
                description.device_class is None
            ), f"Sensor {description.key} should have None device class"
        else:
            # General assertion for any other sensors if they shouldn't be MONETARY/TOTAL
            if description.device_class:  # only assert if device_class is not None
                assert (
                    description.device_class != SensorDeviceClass.MONETARY
                ), f"Sensor {description.key} should not have MONETARY device class unless specified"
            if description.state_class:  # only assert if state_class is not None
                assert (
                    description.state_class != SensorStateClass.TOTAL
                ), f"Sensor {description.key} should not have TOTAL state class unless specified"
