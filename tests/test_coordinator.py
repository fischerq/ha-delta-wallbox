import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusIOException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.delta_wallbox.coordinator import (
    DeltaWallboxDataUpdateCoordinator,
)
from custom_components.delta_wallbox.const import (
    REG_CHARGER_STATE,
    REG_CHARGER_SERIAL_NUMBER,
)


@pytest.fixture
def mock_modbus_client():
    """Mock the ModbusTcpClient."""
    client = MagicMock(spec=ModbusTcpClient)
    client.is_socket_open.return_value = True
    return client


async def test_successful_update(hass: HomeAssistant, mock_modbus_client):
    """Test successful data update."""
    # Prepare a mock response with some data
    mock_registers = [0] * 200  # A list of 200 registers, all zero
    mock_registers[REG_CHARGER_STATE - 1] = 1  # Charger State: Idle
    mock_registers[
        REG_CHARGER_SERIAL_NUMBER - 1 : REG_CHARGER_SERIAL_NUMBER - 1 + 20
    ] = [ord(c) for c in "TEST_SERIAL_NUMBER"] + [0] * (
        20 - len("TEST_SERIAL_NUMBER")
    )

    async def mock_read_input_registers(address, count, device_id):
        response = MagicMock()
        response.isError.return_value = False
        response.registers = mock_registers[address : address + count]
        return response

    mock_modbus_client.read_input_registers = AsyncMock(
        side_effect=mock_read_input_registers
    )

    coordinator = DeltaWallboxDataUpdateCoordinator(hass, mock_modbus_client, 1)

    data = await coordinator._async_update_data()

    assert data["charger_state"] == 1
    assert data["charger_serial_number"] == "TEST_SERIAL_NUMBER"


async def test_update_modbus_error(hass: HomeAssistant, mock_modbus_client):
    """Test data update failure due to Modbus error."""
    error_response = MagicMock()
    error_response.isError.return_value = True

    async def mock_read_input_registers(address, count, device_id):
        return error_response

    mock_modbus_client.read_input_registers = AsyncMock(
        side_effect=mock_read_input_registers
    )

    coordinator = DeltaWallboxDataUpdateCoordinator(hass, mock_modbus_client, 1)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_update_connection_error(hass: HomeAssistant, mock_modbus_client):
    """Test data update failure due to connection error."""
    mock_modbus_client.read_input_registers.side_effect = ConnectionException(
        "Failed to connect"
    )

    coordinator = DeltaWallboxDataUpdateCoordinator(hass, mock_modbus_client, 1)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_decoding_helpers(hass: HomeAssistant, mock_modbus_client):
    """Test the data decoding helper functions."""
    coordinator = DeltaWallboxDataUpdateCoordinator(hass, mock_modbus_client, 1)

    # Test u32 decoding
    assert coordinator._decode_u32([0x0001, 0x0002]) == 65538

    # Test u64 decoding
    assert (
        coordinator._decode_u64([0x0001, 0x0002, 0x0003, 0x0004])
        == 281483566841860
    )

    # Test f32 decoding (IEEE 754 float)
    # Value for 1.0 is 0x3f800000 -> registers [0x3f80, 0x0000]
    assert coordinator._decode_f32([0x3F80, 0x0000]) == 1.0


async def test_read_string(hass: HomeAssistant, mock_modbus_client):
    """Test the read_string helper function."""
    coordinator = DeltaWallboxDataUpdateCoordinator(hass, mock_modbus_client, 1)

    # Prepare a mock response with a null-terminated string
    mock_registers = [ord(c) for c in "TEST"] + [0] + [ord(c) for c in "EXTRA"]

    async def mock_read_input_registers(address, count, device_id):
        response = MagicMock()
        response.isError.return_value = False
        response.registers = [mock_registers[address + 1]]
        return response

    mock_modbus_client.read_input_registers = AsyncMock(
        side_effect=mock_read_input_registers
    )

    result = await coordinator._read_string(0, 20)
    assert result == "TEST"