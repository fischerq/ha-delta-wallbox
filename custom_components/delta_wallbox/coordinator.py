"""Data update coordinator for the Delta Wallbox integration."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DeltaWallboxClient
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class DeltaWallboxDataUpdateCoordinator(DataUpdateCoordinator):
    """Polls the wallbox through the sync client in the executor."""

    def __init__(self, hass: HomeAssistant, client: DeltaWallboxClient):
        """Initialize."""
        self.client = client
        self.slave_id = client.device_id
        self.serial_number: str | None = None
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from the charger."""
        try:
            if self.serial_number is None:
                self.serial_number = await self.hass.async_add_executor_job(
                    self.client.read_serial
                )
            data = await self.hass.async_add_executor_job(self.client.read_state)
        except Exception as err:  # pymodbus raises a zoo of exception types
            raise UpdateFailed(f"Error communicating with the wallbox: {err}") from err
        data["charger_serial_number"] = self.serial_number
        return data
