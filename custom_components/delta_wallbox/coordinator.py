"""Data update coordinator for the Delta Wallbox integration."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException, ModbusIOException

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    REG_CHARGER_STATE,
    REG_CHARGER_SERIAL_NUMBER,
)

_LOGGER = logging.getLogger(__name__)


class DeltaWallboxDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Delta Wallbox."""

    def __init__(self, hass: HomeAssistant, client: ModbusTcpClient, slave_id: int):
        """Initialize."""
        self.client = client
        self.slave_id = slave_id
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _read_register(self, address, count=1):
        """Read a register from the modbus device."""
        _LOGGER.debug(
            "Reading %d registers from address %d (device_id: %d)",
            count,
            address,
            self.slave_id,
        )
        try:
            result = await self.client.read_input_registers(
                address=address - 1, count=count, device_id=self.slave_id
            )
            if result.isError():
                raise UpdateFailed(f"Modbus error reading address {address}: {result}")
            return result.registers
        except (ConnectionException, ModbusIOException) as ex:
            raise UpdateFailed(f"Error communicating with Modbus device: {ex}") from ex

    async def _read_u16(self, register):
        """Read a 16-bit unsigned integer from a register."""
        regs = await self._read_register(register, 1)
        return regs[0] if regs else 0

    async def _read_u32(self, register):
        """Read a 32-bit unsigned integer from two registers."""
        regs = await self._read_register(register, 2)
        return self._decode_u32(regs) if regs else 0

    async def _read_u64(self, register):
        """Read a 64-bit unsigned integer from four registers."""
        regs = await self._read_register(register, 4)
        return self._decode_u64(regs) if regs else 0

    async def _read_f32(self, register):
        """Read a 32-bit float from two registers."""
        regs = await self._read_register(register, 2)
        return self._decode_f32(regs) if regs else 0.0

    async def _read_string(self, register, max_count):
        """Read a string from a number of registers."""
        result = ""
        for i in range(max_count):
            regs = await self._read_register(register + i, 1)
            if not regs or regs[0] == 0:
                break
            result += chr(regs[0])
        return result

    async def _async_update_data(self):
        """Fetch data from the charger."""
        _LOGGER.debug("Fetching data from the charger")
        if not self.client.is_socket_open():
            _LOGGER.debug("Connecting to the charger")
            self.client.connect()

        data = {}
        # Charger-Level Sensors
        data["charger_state"] = await self._read_u16(REG_CHARGER_STATE)
        _LOGGER.debug(f"Charger state: {data['charger_state']}")
        data["charger_serial_number"] = await self._read_string(
            REG_CHARGER_SERIAL_NUMBER, 20
        )
        _LOGGER.debug(f"Serial number: {data['charger_serial_number']}")

        _LOGGER.debug(f"Returning data: {data}")
        return data

    def _decode_u32(self, registers):
        """Decode a 32-bit unsigned integer from two registers."""
        return (registers[0] << 16) | registers[1]

    def _decode_u64(self, registers):
        """Decode a 64-bit unsigned integer from four registers."""
        return (
            (registers[0] << 48)
            | (registers[1] << 32)
            | (registers[2] << 16)
            | registers[3]
        )

    def _decode_f32(self, registers):
        """Decode a 32-bit float from two registers."""
        import struct

        return struct.unpack(">f", struct.pack(">HH", registers[0], registers[1]))[0]