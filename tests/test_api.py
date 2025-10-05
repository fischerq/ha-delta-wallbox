import aiohttp
import asyncio
import json
import logging
import pytest
from aiohttp import ClientError
from datetime import timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from custom_components.braiins_pool.api import (
    BraiinsPoolApiClient,
    BraiinsPoolApiException,
)

logging.basicConfig(level=logging.DEBUG)
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def api_client_fixture():
    mock_session = AsyncMock()
    mock_session.get = MagicMock()
    api_key = "test_api_key"
    client = BraiinsPoolApiClient(mock_session, api_key)
    return client, mock_session, api_key


class JustAMockResponse:
    def __init__(
        self,
        status=200,
        json_data=None,
        text_data="",
        message="",
        raise_json_error_type=None,
        headers=None,
    ):  # Add raise_json_error_type
        self.status = status
        self._json_data = json_data if json_data is not None else {}
        if json_data is not None and text_data == "":
            self._text_data = json.dumps(json_data)
        else:
            self._text_data = text_data
        self.message = message
        self.headers = headers or {}  # Add headers attribute
        self._raise_json_error_type = raise_json_error_type  # Store it
        self.raise_for_status = MagicMock()
        if status >= 400:
            mock_request_info = MagicMock()
            mock_request_info.url = "mock://url"
            mock_request_info.method = "GET"
            mock_request_info.headers = {}

            self.raise_for_status.side_effect = aiohttp.ClientResponseError(
                request_info=mock_request_info,
                history=tuple(),
                status=status,
                message=message or f"Mock HTTP error {status}",
                headers=None,
            )

    async def json(self):
        if self._raise_json_error_type:  # Check if we need to raise
            if self._raise_json_error_type == aiohttp.ContentTypeError:
                # ContentTypeError needs request_info and history, mock them simply
                mock_request_info = MagicMock()
                mock_request_info.url = "mock://url"
                mock_request_info.method = "GET"
                mock_request_info.headers = {}
                raise self._raise_json_error_type(
                    request_info=mock_request_info, history=tuple()
                )
            # For JSONDecodeError, the constructor takes msg, doc, pos
            raise self._raise_json_error_type("Mocked JSON decode error", "doc", 0)
        return self._json_data

    async def text(self):
        return self._text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


def mock_response_factory(
    status=200,
    json_data=None,
    text_data="",
    message="",
    raise_json_error_type=None,
    headers=None,
):  # Add raise_json_error_type
    return JustAMockResponse(
        status=status,
        json_data=json_data,
        text_data=text_data,
        message=message,
        raise_json_error_type=raise_json_error_type,
        headers=headers,
    )  # Pass it


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_user_profile_success(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    # Simulate raw API response data that get_user_profile expects
    raw_api_data = {
        "btc": {
            "current_balance": "1.23",
            "today_reward": "0.10000000",  # 8 decimal places
            "all_time_reward": "10.50000000",  # 8 decimal places
            "ok_workers": "5",
            "hash_rate_5m": "12345.67",  # As a string from API
        }
    }
    # Expected processed data after get_user_profile handles it
    expected_processed_data = {
        "current_balance": Decimal("1.23"),
        "today_reward": Decimal("0.10000000"),
        "all_time_reward": Decimal("10.50000000"),
        "ok_workers": 5,
        "pool_5m_hash_rate": 12345.67,  # float
    }

    mock_session.get.return_value = mock_response_factory(json_data=raw_api_data)
    processed_data = (
        await api_client.get_user_profile()
    )  # Renamed 'data' to 'processed_data' for clarity

    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/accounts/profile/json/btc/",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    assert processed_data == expected_processed_data
    mock_logger.debug.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_account_stats_success(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_data = {"test": "data"}
    mock_session.get.return_value = mock_response_factory(json_data=mock_data)
    # get_account_stats now calls _request and returns the raw response from _request
    data = await api_client.get_account_stats()

    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/stats/json/btc",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    assert data == mock_data
    mock_logger.debug.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_request_returns_non_json_response_content_type_error(
    mock_logger, api_client_fixture
):
    api_client, mock_session, _ = api_client_fixture

    # Simulate API returning a non-JSON response (e.g., HTML error page)
    # but with a 200 OK status.
    mock_response_obj = mock_response_factory(
        status=200,
        text_data="<html><body>Error</body></html>",
        raise_json_error_type=aiohttp.ContentTypeError,
    )
    mock_session.get.return_value = mock_response_obj

    with pytest.raises(BraiinsPoolApiException) as excinfo:
        # Use any method that calls _request, e.g., get_account_stats
        await api_client.get_account_stats()

    assert "API returned non-JSON response" in str(excinfo.value)
    assert "Status: 200" in str(excinfo.value)  # Changed to capital S
    assert "<html><body>Error</body></html>"[:100] in str(
        excinfo.value
    )  # Check if part of the text is in the exception

    mock_logger.error.assert_called_once()
    # Check that the logger was called with a message containing the problematic URL and response snippet
    args, _ = mock_logger.error.call_args
    assert "API request to" in args[0]
    assert "returned non-JSON response" in args[0]
    assert "<html><body>Error</body></html>"[:500] in args[3]  # Full snippet logged


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_request_returns_non_json_response_json_decode_error(
    mock_logger, api_client_fixture
):
    api_client, mock_session, _ = api_client_fixture

    # Simulate API returning malformed JSON
    mock_response_obj = mock_response_factory(
        status=200,
        text_data="{malformed_json",
        raise_json_error_type=json.JSONDecodeError,  # Use json.JSONDecodeError here
    )

    mock_session.get.return_value = mock_response_obj

    with pytest.raises(BraiinsPoolApiException) as excinfo:
        await api_client.get_account_stats()

    assert "API returned non-JSON response" in str(excinfo.value)
    assert "Status: 200" in str(excinfo.value)  # Changed to capital S
    assert "{malformed_json"[:100] in str(excinfo.value)

    # Check for debug logs
    assert any(
        call.args[0] == "Making API request to: %s, Headers: %s"
        for call in mock_logger.debug.call_args_list
    ), "Request URL and headers not logged at DEBUG level"
    assert any(
        call.args[0] == "Received API response: Status: %s, Headers: %s"
        for call in mock_logger.debug.call_args_list
    ), "Response status and headers not logged at DEBUG level"
    assert any(
        call.args[0] == "API Response Body: %s" and call.args[1] == "{malformed_json"
        for call in mock_logger.debug.call_args_list
    ), "Response body not logged at DEBUG level or content mismatch"

    mock_logger.error.assert_called_once()
    args, kwargs = (
        mock_logger.error.call_args
    )  # Use kwargs if format specifiers are named
    assert (
        args[0]
        == "API request to %s returned non-JSON response (status: %s). Response text: %s"
    )
    assert args[1] == "https://pool.braiins.com/stats/json/btc"  # Expected URL
    assert args[2] == 200  # Expected status
    assert args[3] == "{malformed_json"  # Expected response text


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_account_stats_401(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_response_obj = mock_response_factory(
        status=401, text_data="Unauthorized", message="Unauthorized"
    )
    mock_session.get.return_value = mock_response_obj

    with pytest.raises(BraiinsPoolApiException):  # Changed from ClientError
        await api_client.get_account_stats()

    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/stats/json/btc",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    mock_response_obj.raise_for_status.assert_called_once()
    mock_logger.error.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_account_stats_other_error(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_response_obj = mock_response_factory(
        status=500, text_data="Server Error", message="Server Error"
    )
    mock_session.get.return_value = mock_response_obj

    with pytest.raises(BraiinsPoolApiException):  # Changed from ClientError
        await api_client.get_account_stats()

    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/stats/json/btc",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    mock_response_obj.raise_for_status.assert_called_once()
    mock_logger.error.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_daily_rewards_success(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_data = {"btc": {"daily_rewards": [{"total_reward": "0.12345"}]}}
    mock_session.get.return_value = mock_response_factory(json_data=mock_data)
    data = await api_client.get_daily_rewards()
    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/accounts/rewards/json/btc",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    assert data == mock_data
    mock_logger.debug.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_daily_rewards_401(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_response_obj = mock_response_factory(
        status=401, text_data="Unauthorized", message="Unauthorized"
    )
    mock_session.get.return_value = mock_response_obj

    with pytest.raises(BraiinsPoolApiException):  # Changed from ClientError
        await api_client.get_daily_rewards()

    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/accounts/rewards/json/btc",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    mock_response_obj.raise_for_status.assert_called_once()
    mock_logger.error.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_daily_rewards_client_error(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    expected_url = "https://pool.braiins.com/accounts/rewards/json/btc"
    mock_session.get.side_effect = ClientError("Network issue")

    with pytest.raises(
        ClientError
    ) as excinfo:  # This should still be ClientError as it's a direct network error
        await api_client.get_daily_rewards()

    assert "Network issue" in str(excinfo.value)
    mock_session.get.assert_called_once_with(
        expected_url, headers={"Pool-Auth-Token": api_key, "Accept": "application/json"}
    )
    mock_logger.debug.assert_called()
    mock_logger.error.assert_not_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_daily_hashrate_success(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_data = {"test": "daily_hashrate_data"}
    mock_session.get.return_value = mock_response_factory(json_data=mock_data)
    data = await api_client.get_daily_hashrate()
    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/accounts/hash_rate_daily/json/user/btc",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    assert data == mock_data
    mock_logger.debug.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_block_rewards_success(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_data = {"test": "block_rewards_data"}
    from_date = "2023-10-01"
    to_date = "2023-10-07"
    mock_session.get.return_value = mock_response_factory(json_data=mock_data)
    data = await api_client.get_block_rewards(from_date, to_date)
    mock_session.get.assert_called_once_with(
        f"https://pool.braiins.com/accounts/block_rewards/json/btc?from={from_date}&to={to_date}",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    assert data == mock_data
    mock_logger.debug.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_workers_success(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_data = {"test": "workers_data"}
    mock_session.get.return_value = mock_response_factory(json_data=mock_data)
    data = await api_client.get_workers()
    mock_session.get.assert_called_once_with(
        "https://pool.braiins.com/accounts/workers/json/btc/",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    assert data == mock_data
    mock_logger.debug.assert_called()


@patch("custom_components.braiins_pool.api._LOGGER")
async def test_get_payouts_success(mock_logger, api_client_fixture):
    api_client, mock_session, api_key = api_client_fixture
    mock_data = {"test": "payouts_data"}
    from_date = "2023-10-01"
    to_date = "2023-10-07"
    mock_session.get.return_value = mock_response_factory(json_data=mock_data)
    data = await api_client.get_payouts(from_date, to_date)
    mock_session.get.assert_called_once_with(
        f"https://pool.braiins.com/accounts/payouts/json/btc?from={from_date}&to={to_date}",
        headers={"Pool-Auth-Token": api_key, "Accept": "application/json"},
    )
    assert data == mock_data
    mock_logger.debug.assert_called()
