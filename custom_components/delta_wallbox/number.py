"""Number platform for the Delta Wallbox integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfPower
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DeltaWallboxDataUpdateCoordinator
from .entity import device_info

NUMBER_TYPES: tuple[NumberEntityDescription, ...] = (
    NumberEntityDescription(
        key="power_limit",
        name="Charging Power Limit",
        icon="mdi:car-speed-limiter",
        native_unit_of_measurement=UnitOfPower.WATT,
        native_min_value=0,
        native_max_value=22000,
        native_step=100,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DeltaWallboxNumber(coordinator, description) for description in NUMBER_TYPES
    )


class DeltaWallboxNumber(CoordinatorEntity, NumberEntity):
    """The charging power limit (holding register 1600), read back each poll.

    Unknown while the charger reports "no limit".
    """

    def __init__(
        self,
        coordinator: DeltaWallboxDataUpdateCoordinator,
        description: NumberEntityDescription,
    ):
        """Initialize the number."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.slave_id}_{description.key}"
        self._attr_device_info = device_info(coordinator)

    @property
    def native_value(self) -> float | None:
        """Return the limit the charger currently reports."""
        return self.coordinator.data.get("power_limit")

    async def async_set_native_value(self, value: float) -> None:
        """Write the limit, then refresh so the read-back value shows."""
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.client.set_power_limit, int(value)
            )
        except Exception as err:
            raise HomeAssistantError(
                f"Setting the wallbox limit failed: {err}"
            ) from err
        await self.coordinator.async_request_refresh()
