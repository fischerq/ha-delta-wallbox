"""Switch platform for the Delta Wallbox integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DeltaWallboxDataUpdateCoordinator
from .entity import device_info

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="charging_enabled",
        name="Charging Enabled",
        icon="mdi:flash",
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DeltaWallboxSwitch(coordinator, description) for description in SWITCH_TYPES
    )


class DeltaWallboxSwitch(CoordinatorEntity, SwitchEntity):
    """On = charging allowed; off = suspended (holding register 1602).

    Suspending keeps the cable locked; the car resumes when switched on.
    """

    def __init__(
        self,
        coordinator: DeltaWallboxDataUpdateCoordinator,
        description: SwitchEntityDescription,
    ):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.slave_id}_{description.key}"
        self._attr_device_info = device_info(coordinator)

    @property
    def is_on(self) -> bool | None:
        """Return true unless the charger reports it is suspended."""
        suspended = self.coordinator.data.get("suspended")
        return None if suspended is None else not suspended

    async def _set_suspended(self, suspended: bool) -> None:
        try:
            await self.hass.async_add_executor_job(
                self.coordinator.client.set_suspended, suspended
            )
        except Exception as err:
            raise HomeAssistantError(f"Wallbox suspend/resume failed: {err}") from err
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        """Resume charging."""
        await self._set_suspended(False)

    async def async_turn_off(self, **kwargs) -> None:
        """Suspend charging."""
        await self._set_suspended(True)
