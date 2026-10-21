"""Shared entity helpers for the Delta Wallbox integration."""

from .const import DOMAIN


def device_info(coordinator) -> dict:
    """Device registry info shared by all entities."""
    return {
        "identifiers": {(DOMAIN, coordinator.slave_id)},
        "name": "Delta Wallbox",
        "manufacturer": "Delta",
        "model": "AC MAX",
        "serial_number": coordinator.serial_number,
    }
