
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusIOException
from pymodbus.pdu import ModbusResponse

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.delta_wallbox.coordinator import (
    DeltaWallboxDataUpdateCoordinator,
)


@pytest.fixture
def mock_modbus_client():
    """Mock the ModbusTcpClient."""
    client = MagicMock(spec=ModbusTcpClient)
    client.is_socket_open.return_value = True
    return client


class MockModbusResponse(ModbusResponse):
    def __init__(self, registers):
        self.registers = registers

    def isError(self):
        return False

    def get_register(self, address, count=1):
        if count == 1:
            return self.registers[address]
        return self.registers[address : address + count]

    def get_registers(self, address, count):
        return self.registers[address : address + count]


async def test_successful_update(hass: HomeAssistant, mock_modbus_client):
    """Test successful data update."""
    # Prepare a mock response with some data
    mock_registers = [0] * 200  # A list of 200 registers, all zero
    mock_registers[1] = 1  # Charger State: Idle
    mock_registers[10:30] = [ord(c) for c in "TEST_SERIAL_NUMBER"] + [0] * (20 - len("TEST_SERIAL_NUMBER"))
    mock_registers[110] = 5 # EVSE State: Charging

    mock_response = MockModbusResponse(mock_registers)
    mock_modbus_client.read_input_registers.return_value = mock_response

    coordinator = DeltaWallboxDataUpdateCoordinator(hass, mock_modbus_client, 1)

    await coordinator._async_update_data()

    assert coordinator.data["charger_state"] == 1
    assert coordinator.data["serial_number"] == "TEST_SERIAL_NUMBER"
    assert coordinator.data["evse_state"] == 5


async def test_update_modbus_error(hass: HomeAssistant, mock_modbus_client):
    """Test data update failure due to Modbus error."""
    error_response = MagicMock(spec=ModbusResponse)
    error_response.isError.return_value = True
    mock_modbus_client.read_input_registers.return_value = error_response

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
    assert coordinator._decode_u64([0x0001, 0x0002, 0x0003, 0x0004]) == 281479271743492

    # Test f32 decoding (IEEE 754 float)
    # Value for 1.0 is 0x3f800000 -> registers [0x3f80, 0x0000]
    assert coordinator._decode_f32([0x3F80, 0x0000]) == 1.0
