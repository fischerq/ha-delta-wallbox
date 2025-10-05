import pytest
from unittest.mock import patch, MagicMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.braiins_pool.const import DOMAIN, CONF_REWARDS_ACCOUNT_NAME
from custom_components.braiins_pool.coordinator import BraiinsDataUpdateCoordinator
from custom_components.braiins_pool import async_setup_entry, async_unload_entry

MOCK_API_KEY = "test_api_key_456"
MOCK_REWARDS_ACCOUNT_NAME = "My Pool Account"
MOCK_ENTRY_ID = "mock_entry_1"


@pytest.fixture
def mock_config_entry():
    """Mock a config entry."""
    return MagicMock(
        data={
            CONF_API_KEY: MOCK_API_KEY,
            CONF_REWARDS_ACCOUNT_NAME: MOCK_REWARDS_ACCOUNT_NAME,
        },
        entry_id=MOCK_ENTRY_ID,
        title=MOCK_REWARDS_ACCOUNT_NAME,
    )


@patch("custom_components.braiins_pool.BraiinsPoolApiClient")
@patch(
    "custom_components.braiins_pool.BraiinsDataUpdateCoordinator.async_config_entry_first_refresh",
    return_value=None,
)  # Mock first refresh
@patch(
    "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
)  # Further mock sensor setup
async def test_async_setup_entry(
    mock_forward_setup,
    mock_first_refresh,
    MockBraiinsPoolApiClient,
    hass: HomeAssistant,
    mock_config_entry,
):
    """Test successful setup of the integration."""
    # Mock the API client instance
    mock_api_client_instance = MockBraiinsPoolApiClient.return_value

    success = await async_setup_entry(hass, mock_config_entry)
    await hass.async_block_till_done()

    assert success is True
    MockBraiinsPoolApiClient.assert_called_once_with(
        async_get_clientsession(hass), MOCK_API_KEY
    )

    # Check that coordinator is created and stored
    assert MOCK_ENTRY_ID in hass.data[DOMAIN]
    coordinator = hass.data[DOMAIN][MOCK_ENTRY_ID]
    assert isinstance(coordinator, BraiinsDataUpdateCoordinator)
    assert coordinator.api_client == mock_api_client_instance

    mock_first_refresh.assert_called_once()
    mock_forward_setup.assert_called_once_with(mock_config_entry, ["sensor"])


@patch("homeassistant.config_entries.ConfigEntries.async_unload_platforms")
async def test_async_unload_entry(
    mock_unload_platforms,
    hass: HomeAssistant,
    mock_config_entry,
):
    """Test successful unload of the integration."""
    # Pre-populate hass.data as if setup was successful
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = MagicMock()  # Mock coordinator
    mock_unload_platforms.return_value = True

    success = await async_unload_entry(hass, mock_config_entry)
    await hass.async_block_till_done()

    assert success is True
    mock_unload_platforms.assert_called_once_with(mock_config_entry, ["sensor"])
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]
