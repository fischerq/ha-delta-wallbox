"""Number platform for the Delta Wallbox integration."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_SET_POWER_LIMIT
from .coordinator import DeltaWallboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

NUMBER_TYPES: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key="power_limit",
        name="Power Limit",
        icon="mdi:car-speed-limiter",
        native_unit_of_measurement=UnitOfPower.WATT,
        entity_category=EntityCategory.CONFIG,
        native_min_value=0,
        native_max_value=22000,  # Assuming a max of 22kW
        native_step=100,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        DeltaWallboxNumber(coordinator, description) for description in NUMBER_TYPES
    ]
    async_add_entities(entities)


class DeltaWallboxNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Delta Wallbox number."""

    def __init__(self, coordinator: DeltaWallboxDataUpdateCoordinator, description: NumberEntityDescription):
        """Initialize the number."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.slave_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.slave_id)},
            "name": "Delta Wallbox",
            "manufacturer": "Delta",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the number."""
        # This assumes the power limit is not readable from the device.
        # The value is stored locally in the entity.
        return getattr(self, "_attr_native_value", None)

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        client = self.coordinator.client
        try:
            await self.hass.async_add_executor_job(
                client.write_register,
                REG_SET_POWER_LIMIT,
                int(value),
                unit=self.coordinator.slave_id,
            )
            self._attr_native_value = value
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error(f"Error setting power limit: {e}")
