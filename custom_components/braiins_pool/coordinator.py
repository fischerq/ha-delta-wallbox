"""Data update coordinator for the Braiins Pool integration."""

import aiohttp
import asyncio
from datetime import timedelta, datetime, timezone
from decimal import Decimal
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging

from .api import BraiinsPoolApiClient
from .const import (
    DOMAIN,
    CONF_API_KEY,
    SATOSHIS_PER_BTC,
)

_LOGGER = logging.getLogger(__name__)


# Import the actual API client
class BraiinsDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinate updates from the Braiins Pool API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_client: BraiinsPoolApiClient,
        update_interval: timedelta,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api_client = api_client

    async def _async_update_data(self) -> dict:
        """Fetch data from the API."""
        _LOGGER.debug("Fetching and processing data for Braiins Pool integration.")
        processed_data: dict = {}
        today = datetime.now(timezone.utc).date()

        try:
            user_profile_data = await self.api_client.get_user_profile()
            # user_profile_data is already processed by the API client
            # and contains Decimal types for monetary values.

            processed_data["user_profile_data"] = (
                user_profile_data  # Store raw data for debugging or future use
            )

            # Directly use the values, assuming api_client returns them with correct types or defaults
            # The .get() with a default is a fallback, though api_client should handle defaults.
            current_balance = user_profile_data.get("current_balance", Decimal("0"))
            today_reward = user_profile_data.get("today_reward", Decimal("0"))
            all_time_reward = user_profile_data.get("all_time_reward", Decimal("0"))
            ok_workers = user_profile_data.get("ok_workers", 0)  # int
            pool_5m_hash_rate = user_profile_data.get("pool_5m_hash_rate", 0.0)  # float

            processed_data["current_balance"] = current_balance
            processed_data["today_reward"] = today_reward
            processed_data["all_time_reward"] = all_time_reward
            processed_data["ok_workers"] = ok_workers
            processed_data["pool_5m_hash_rate"] = pool_5m_hash_rate

            # Calculate satoshi values
            processed_data["current_balance_satoshi"] = int(
                current_balance * SATOSHIS_PER_BTC
            )
            processed_data["today_reward_satoshi"] = int(
                today_reward * SATOSHIS_PER_BTC
            )
            processed_data["all_time_reward_satoshi"] = int(
                all_time_reward * SATOSHIS_PER_BTC
            )

            return processed_data
        except Exception as err:  # Catch any exception during fetching or processing
            _LOGGER.error(
                "Error fetching or processing data from Braiins Pool API: %s", err
            )
            # Set default values using appropriate types
            processed_data["current_balance"] = Decimal("0")
            processed_data["today_reward"] = Decimal("0")
            processed_data["all_time_reward"] = Decimal("0")
            processed_data["ok_workers"] = 0
            processed_data["current_balance_satoshi"] = 0
            processed_data["today_reward_satoshi"] = 0
            processed_data["all_time_reward_satoshi"] = 0
            processed_data["pool_5m_hash_rate"] = 0.0
            # Store the raw (empty or partial) data if an error occurred after fetching user_profile_data
            processed_data["user_profile_data"] = (
                user_profile_data if "user_profile_data" in locals() else {}
            )
            raise UpdateFailed(f"Error updating data: {err}")
