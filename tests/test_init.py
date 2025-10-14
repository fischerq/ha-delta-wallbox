"""Tests for the Delta Wallbox integration."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components.delta_wallbox import (
    async_setup_entry,
    async_unload_entry,
    PLATFORMS,
)
from custom_components.delta_wallbox.const import DOMAIN

from tests.const import MOCK_IP_ADDRESS, MOCK_PORT, MOCK_SLAVE_ID

from tests.common import MockConfigEntry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "ip_address": MOCK_IP_ADDRESS,
            "port": MOCK_PORT,
            "slave_id": MOCK_SLAVE_ID,
        },
    )


@patch("custom_components.delta_wallbox.ModbusTcpClient")
@patch("custom_components.delta_wallbox.DeltaWallboxDataUpdateCoordinator")
async def test_async_setup_entry(
    mock_coordinator, mock_client, hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test a successful setup entry."""
    # Setup the mock coordinator
    mock_coord_instance = mock_coordinator.return_value
    mock_coord_instance.last_update_success = True
    mock_coord_instance.async_config_entry_first_refresh = AsyncMock()

    # Link the config entry to hass
    mock_config_entry.add_to_hass(hass)

    with patch.object(
        hass.config_entries, "async_forward_entry_setups"
    ) as mock_forward_setup:
        assert await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    # Verify client and coordinator were initialized correctly
    mock_client.assert_called_once_with(MOCK_IP_ADDRESS, port=MOCK_PORT)
    mock_coordinator.assert_called_once_with(
        hass, client=mock_client.return_value, slave_id=MOCK_SLAVE_ID
    )

    # Verify coordinator is stored
    assert hass.data[DOMAIN][mock_config_entry.entry_id] == mock_coord_instance

    # Verify we refreshed the coordinator
    mock_coord_instance.async_config_entry_first_refresh.assert_awaited_once()

    # Verify platforms are being set up
    mock_forward_setup.assert_called_once_with(mock_config_entry, PLATFORMS)


@patch("custom_components.delta_wallbox.ModbusTcpClient")
@patch("custom_components.delta_wallbox.DeltaWallboxDataUpdateCoordinator")
async def test_setup_entry_not_ready(
    mock_coordinator, mock_client, hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
    """Test setup entry when the coordinator fails to refresh."""
    # Setup the mock coordinator to fail the first refresh
    mock_coord_instance = mock_coordinator.return_value
    mock_coord_instance.last_update_success = False
    mock_coord_instance.async_config_entry_first_refresh = AsyncMock(
        side_effect=ConfigEntryNotReady
    )

    mock_config_entry.add_to_hass(hass)

    # Test for the exception
    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, mock_config_entry)


async def test_async_unload_entry(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
):
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
        hass.config_entries, "async_unload_platforms", return_value=True
    ) as mock_forward_unload:
        assert await async_unload_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

    # Verify platforms were unloaded
    mock_forward_unload.assert_called_once_with(mock_config_entry, PLATFORMS)

    # Verify client was closed and data was popped
    assert not hass.data[DOMAIN]