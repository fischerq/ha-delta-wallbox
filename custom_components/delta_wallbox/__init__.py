"""The Delta Wallbox integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from pymodbus.client import ModbusTcpClient

from .const import DOMAIN, CONF_IP_ADDRESS, CONF_PORT, CONF_SLAVE_ID
from .coordinator import DeltaWallboxDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Delta Wallbox from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = ModbusTcpClient(
        entry.data[CONF_IP_ADDRESS],
        port=entry.data[CONF_PORT],
    )

    coordinator = DeltaWallboxDataUpdateCoordinator(
        hass,
        client=client,
        slave_id=entry.data[CONF_SLAVE_ID],
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok