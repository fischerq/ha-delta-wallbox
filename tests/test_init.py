
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.delta_wallbox.const import (
    DOMAIN,
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SLAVE_ID,
)
from custom_components.delta_wallbox import (
    async_setup_entry,
    async_unload_entry,
    PLATFORMS,
)

MOCK_IP_ADDRESS = "1.2.3.4"
MOCK_PORT = 502
MOCK_SLAVE_ID = 1


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
            CONF_PORT: MOCK_PORT,
            CONF_SLAVE_ID: MOCK_SLAVE_ID,
        },
        entry_id="test_entry",
    )


@patch("custom_components.delta_wallbox.ModbusTcpClient")
@patch("custom_components.delta_wallbox.DeltaWallboxDataUpdateCoordinator")
async def test_async_setup_entry(mock_coordinator, mock_client, hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test a successful setup entry."""
    # Setup the mock coordinator
    mock_coord_instance = mock_coordinator.return_value
    mock_coord_instance.last_update_success = True
    mock_coord_instance.async_config_entry_first_refresh = AsyncMock()

    # Link the config entry to hass
    mock_config_entry.add_to_hass(hass)

    with patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward_setup:
        assert await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    # Verify client and coordinator were initialized correctly
    mock_client.assert_called_once_with(MOCK_IP_ADDRESS, port=MOCK_PORT)
    mock_coordinator.assert_called_once_with(hass, mock_client.return_value, MOCK_SLAVE_ID)

    # Verify coordinator is stored
    assert hass.data[DOMAIN][mock_config_entry.entry_id] == mock_coord_instance

    # Verify we refreshed the coordinator
    mock_coord_instance.async_config_entry_first_refresh.assert_awaited_once()

    # Verify platforms are being set up
    mock_forward_setup.assert_called_once_with(mock_config_entry, PLATFORMS)


@patch("custom_components.delta_wallbox.ModbusTcpClient")
@patch("custom_components.delta_wallbox.DeltaWallboxDataUpdateCoordinator")
async def test_setup_entry_not_ready(mock_coordinator, mock_client, hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test setup entry when the coordinator fails to refresh."""
    # Setup the mock coordinator to fail the first refresh
    mock_coord_instance = mock_coordinator.return_value
    mock_coord_instance.last_update_success = False
    mock_coord_instance.async_config_entry_first_refresh = AsyncMock()

    mock_config_entry.add_to_hass(hass)

    # Test for the exception
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, mock_config_entry)


async def test_async_unload_entry(hass: HomeAssistant, mock_config_entry: MockConfigEntry):
    """Test a successful unload entry."""
    # Mock the coordinator and its client
    mock_client = MagicMock()
    mock_coordinator = MagicMock()
    mock_coordinator.client = mock_client

    # Pre-populate hass.data as if setup was successful
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][mock_config_entry.entry_id] = mock_coordinator

    mock_config_entry.add_to_hass(hass)

    with patch.object(
        hass.config_entries, "async_forward_entry_unload", return_value=True
    ) as mock_forward_unload:
        assert await async_unload_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    # Verify platforms were unloaded
    assert mock_forward_unload.call_count == len(PLATFORMS)

    # Verify client was closed and data was popped
    mock_client.close.assert_called_once()
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]
