"""Sensor entities for the Braiins Pool integration."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfDataRate
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_REWARDS_ACCOUNT_NAME
from .coordinator import BraiinsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="today_reward",
        name="Braiins Pool Today's Reward",
        icon="mdi:bitcoin",
        native_unit_of_measurement="BTC",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
    ),
    SensorEntityDescription(
        key="current_balance",
        name="Braiins Pool Current Balance",
        icon="mdi:wallet-outline",
        native_unit_of_measurement="BTC",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
    ),
    SensorEntityDescription(
        key="all_time_reward",
        name="Braiins Pool All Time Reward",
        icon="mdi:medal-outline",
        native_unit_of_measurement="BTC",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
    ),
    SensorEntityDescription(
        key="pool_5m_hash_rate",
        name="Braiins Pool 5m Hash Rate",
        icon="mdi:gauge",
        native_unit_of_measurement="Gh/s",  # API specifies Gh/s
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DATA_RATE,
    ),
    SensorEntityDescription(
        key="ok_workers",
        name="Braiins Pool Active Workers",
        icon="mdi:worker",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="today_reward_satoshi",
        name="Braiins Pool Today's Reward Satoshi",
        icon="mdi:bitcoin",
        native_unit_of_measurement="Satoshi",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
    ),
    SensorEntityDescription(
        key="current_balance_satoshi",
        name="Braiins Pool Current Balance Satoshi",
        icon="mdi:wallet-outline",
        native_unit_of_measurement="Satoshi",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
    ),
    SensorEntityDescription(
        key="all_time_reward_satoshi",
        name="Braiins Pool All Time Reward Satoshi",
        icon="mdi:medal-outline",
        native_unit_of_measurement="Satoshi",
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.MONETARY,
    ),
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    coordinator: BraiinsDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    rewards_account_name = config_entry.data.get(CONF_REWARDS_ACCOUNT_NAME)

    entities = [
        BraiinsPoolSensor(coordinator, description, config_entry)
        for description in SENSOR_TYPES
    ]
    async_add_entities(entities)


class BraiinsPoolSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Braiins Pool sensor."""

    def __init__(
        self, coordinator, entity_description, config_entry
    ):  # Add config_entry
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._config_entry = config_entry
        self._attr_name = entity_description.name
        self._attr_unique_id = (
            f"{self._config_entry.entry_id}_{self.entity_description.key}"
        )

    @property
    def device_info(self):
        """Return device information."""
        account_name = self._config_entry.data.get(
            CONF_REWARDS_ACCOUNT_NAME, "Braiins Pool"
        )
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": account_name,
            "manufacturer": "Braiins",
            "entry_type": "service",  # Or remove if not applicable
        }

    @property
    def native_value(self):
        """Return the state of the sensor, handling potential missing data."""
        return self.coordinator.data.get(self.entity_description.key, None)
