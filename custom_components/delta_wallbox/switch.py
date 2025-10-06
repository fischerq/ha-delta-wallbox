"""Switch platform for the Delta Wallbox integration."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_START_STOP_CHARGING
from .coordinator import DeltaWallboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="charging",
        name="Charging",
        icon="mdi:flash",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        DeltaWallboxSwitch(coordinator, description) for description in SWITCH_TYPES
    ]
    async_add_entities(entities)


class DeltaWallboxSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Delta Wallbox switch."""

    def __init__(self, coordinator: DeltaWallboxDataUpdateCoordinator, description: SwitchEntityDescription):
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.slave_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.slave_id)},
            "name": "Delta Wallbox",
            "manufacturer": "Delta",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.get("charging_power", 0) > 0

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        client = self.coordinator.client
        try:
            await self.hass.async_add_executor_job(
                client.write_register, REG_START_STOP_CHARGING, 1, unit=self.coordinator.slave_id
            )
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(f"Error turning on charging: {e}")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        client = self.coordinator.client
        try:
            await self.hass.async_add_executor_job(
                client.write_register, REG_START_STOP_CHARGING, 0, unit=self.coordinator.slave_id
            )
            await self.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(f"Error turning off charging: {e}")
