"""API client for Braiins Pool."""

import logging
import aiohttp
import json
from decimal import Decimal

API_HEADERS = {"Pool-Auth-Token": "{}", "Accept": "application/json"}
API_URL_POOL_STATS = "https://pool.braiins.com/stats/json/{}"
API_URL_USER_PROFILE = "https://pool.braiins.com/accounts/profile/json/{}/"
API_URL_DAILY_REWARDS = "https://pool.braiins.com/accounts/rewards/json/{}"
API_URL_DAILY_HASHRATE = "https://pool.braiins.com/accounts/hash_rate_daily/json/{}/{}"
API_URL_BLOCK_REWARDS = (
    "https://pool.braiins.com/accounts/block_rewards/json/{}?from={}&to={}"
)
API_URL_WORKERS = "https://pool.braiins.com/accounts/workers/json/{}/"
API_URL_PAYOUTS = "https://pool.braiins.com/accounts/payouts/json/{}?from={}&to={}"
DEFAULT_COIN = "btc"


_LOGGER = logging.getLogger(__name__)


class BraiinsPoolApiException(Exception):
    """Base exception for Braiins Pool API."""


class BraiinsPoolAuthError(BraiinsPoolApiException):
    """Authentication error."""


class BraiinsPoolApiClient:
    """API client for Braiins Pool."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        """Initialize."""
        self._session = session
        self._api_key = api_key

    async def _request(self, url: str):
        """
        Helper method to perform API requests to the Braiins Pool API.

        Args:
            url (str): The full URL of the API endpoint to request.

        Returns:
            dict: The JSON response from the API.

        Raises:
            BraiinsPoolApiException: If an API error or non-JSON response occurs.
        """
        headers = {k: v.format(self._api_key) for k, v in API_HEADERS.items()}
        _LOGGER.debug("Making API request to: %s, Headers: %s", url, headers)
        try:
            async with self._session.get(url, headers=headers) as response:
                _LOGGER.debug(
                    "Received API response: Status: %s, Headers: %s",
                    response.status,
                    response.headers,
                )
                response_text = await response.text()
                _LOGGER.debug("API Response Body: %s", response_text)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                try:
                    return json.loads(response_text)
                except (aiohttp.ContentTypeError, json.JSONDecodeError) as json_err:
                    _LOGGER.error(
                        "API request to %s returned non-JSON response (status: %s). Response text: %s",
                        url,
                        response.status,
                        response_text,
                    )
                    raise BraiinsPoolApiException(
                        f"API returned non-JSON response. Status: {response.status}, Body: {response_text}"
                    ) from json_err
        except aiohttp.ClientResponseError as err:
            if (
                err.status == 403
            ):  # Changed from 401 to 403 based on common API practices for forbidden access with valid key format but insufficient permissions
                _LOGGER.error(
                    "Braiins Pool API Authentication Error: Invalid API key or insufficient permissions."
                )
                raise BraiinsPoolAuthError("Invalid API key") from err
            # Other ClientResponseErrors (e.g. 401, 500)
            _LOGGER.error(
                "Error fetching data from Braiins Pool API: Status %s, Message: %s",
                err.status,
                err.message,
            )
            raise BraiinsPoolApiException(
                f"API error {err.status}: {err.message}"
            ) from err
        except aiohttp.ClientError as err:
            raise err
        except (
            BraiinsPoolAuthError
        ):  # Specific handler to re-raise without logging again
            raise
        except (
            BraiinsPoolApiException
        ):  # Specific handler to re-raise without logging again
            raise
        except Exception as err:
            _LOGGER.error(
                "An unexpected error occurred during API request to %s: %s", url, err
            )
            raise err

    async def get_user_profile(self, coin=DEFAULT_COIN):
        """Fetch user profile from Braiins Pool API."""
        url = API_URL_USER_PROFILE.format(coin)
        data = await self._request(url)
        processed_data = {}
        if coin == "btc" and "btc" in data:
            btc_data = data["btc"]
            processed_data["current_balance"] = Decimal(
                btc_data.get("current_balance", "0")
            )
            processed_data["today_reward"] = Decimal(btc_data.get("today_reward", "0"))
            processed_data["all_time_reward"] = Decimal(
                btc_data.get("all_time_reward", "0")
            )
            processed_data["ok_workers"] = int(btc_data.get("ok_workers", 0))
            processed_data["pool_5m_hash_rate"] = float(
                btc_data.get("hash_rate_5m", "0")
            )
        return processed_data

    async def get_account_stats(self):
        """Fetch account statistics from Braiins Pool API. Not parsed yet."""
        url = API_URL_POOL_STATS.format(DEFAULT_COIN)
        return await self._request(url)

    async def get_daily_rewards(self):
        """Fetch daily rewards from Braiins Pool API. Not parsed yet."""
        url = API_URL_DAILY_REWARDS.format(DEFAULT_COIN)
        return await self._request(url)

    async def get_daily_hashrate(self, group="user", coin=DEFAULT_COIN):
        """Fetch daily hashrate from Braiins Pool API. Not parsed yet."""
        url = API_URL_DAILY_HASHRATE.format(group, coin)
        return await self._request(url)

    async def get_block_rewards(self, from_date: str, to_date: str, coin=DEFAULT_COIN):
        """Fetch block rewards from Braiins Pool API. Not parsed yet."""
        url = API_URL_BLOCK_REWARDS.format(coin, from_date, to_date)
        return await self._request(url)

    async def get_workers(self, coin=DEFAULT_COIN):
        """Fetch worker data from Braiins Pool API. Not parsed yet."""
        url = API_URL_WORKERS.format(coin)
        return await self._request(url)

    async def get_payouts(self, from_date: str, to_date: str, coin=DEFAULT_COIN):
        """Fetch payouts data from Braiins Pool API. Not parsed yet."""
        url = API_URL_PAYOUTS.format(coin, from_date, to_date)
        return await self._request(url)
