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
    REG_EVSE_COUNT,
    REG_SERIAL_NUMBER,
    REG_MODEL,
    REG_EVSE_STATE,
    REG_EV_CONNECTED,
    REG_CHARGING_TIME,
    REG_CHARGING_POWER,
    REG_CHARGED_ENERGY,
    REG_SOC,
    REG_EV_MAX_POWER,
    REG_EV_MIN_POWER,
    REG_P1_VOLTAGE,
    REG_P2_VOLTAGE,
    REG_P3_VOLTAGE,
    REG_P1_CURRENT,
    REG_P2_CURRENT,
    REG_P3_CURRENT,
    REG_GRID_FREQUENCY,
    REG_GRID_TOTAL_POWER,
    REG_GRID_P1_POWER,
    REG_GRID_P2_POWER,
    REG_GRID_P3_POWER,
    REG_ERROR_CODE,
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
                _LOGGER.warning(
                    "Modbus error reading address %d: %s", address, result
                )
                return None
            return result.registers
        except Exception as ex:
            _LOGGER.warning("Error reading address %d: %s", address, ex)
            return None

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
        regs = await self._read_register(register, 1)
        # TODO: read up to max_count registers, stop when a register is 0
        return "".join([chr(c) for c in regs if c != 0]) if regs else ""

    async def _async_update_data(self):
        """Fetch data from the charger."""
        _LOGGER.debug("Fetching data from the charger")
        try:
            if not self.client.is_socket_open():
                _LOGGER.debug("Connecting to the charger")
                self.client.connect()

            data = {}
            # Charger-Level Sensors
            data["charger_state"] = await self._read_u16(REG_CHARGER_STATE)
            _LOGGER.debug(f"Charger state: {data['charger_state']}")
#            data["evse_count"] = await self._read_u16(REG_EVSE_COUNT)
#            _LOGGER.debug(f"EVSE count: {data['evse_count']}")
#            data["serial_number"] = await self._read_string(REG_SERIAL_NUMBER, 20)
#            _LOGGER.debug(f"Serial number: {data['serial_number']}")
            data["model"] = await self._read_string(REG_MODEL, 20)
            _LOGGER.debug(f"Model: {data['model']}")

#            # EVSE-Level Sensors
#            data["evse_state"] = await self._read_u16(REG_EVSE_STATE)
#            _LOGGER.debug(f"EVSE state: {data['evse_state']}")
#            data["ev_connected"] = await self._read_u16(REG_EV_CONNECTED)
#            _LOGGER.debug(f"EV connected: {data['ev_connected']}")
#            data["charging_time"] = await self._read_u32(REG_CHARGING_TIME)
#            _LOGGER.debug(f"Charging time: {data['charging_time']}")
#            data["charging_power"] = await self._read_u32(REG_CHARGING_POWER)
#            _LOGGER.debug(f"Charging power: {data['charging_power']}")
#            data["charged_energy"] = await self._read_u32(REG_CHARGED_ENERGY)
#            _LOGGER.debug(f"Charged energy: {data['charged_energy']}")

#            soc_raw = await self._read_u16(REG_SOC)
#            data["soc"] = soc_raw / 10.0
#            _LOGGER.debug(f"SOC: {data['soc']}")

#            data["ev_max_power"] = await self._read_u32(REG_EV_MAX_POWER)
#            _LOGGER.debug(f"EV max power: {data['ev_max_power']}")
#            data["ev_min_power"] = await self._read_u32(REG_EV_MIN_POWER)
#            _LOGGER.debug(f"EV min power: {data['ev_min_power']}")
 #           data["p1_voltage"] = await self._read_u32(REG_P1_VOLTAGE)
 #           _LOGGER.debug(f"P1 voltage: {data['p1_voltage']}")
 #           data["p2_voltage"] = await self._read_u32(REG_P2_VOLTAGE)
 #           _LOGGER.debug(f"P2 voltage: {data['p2_voltage']}")
 #           data["p3_voltage"] = await self._read_u32(REG_P3_VOLTAGE)
 #           _LOGGER.debug(f"P3 voltage: {data['p3_voltage']}")
 #           data["p1_current"] = await self._read_u32(REG_P1_CURRENT)
 #           _LOGGER.debug(f"P1 current: {data['p1_current']}")
 #           data["p2_current"] = await self._read_u32(REG_P2_CURRENT)
 #           _LOGGER.debug(f"P2 current: {data['p2_current']}")
  #          data["p3_current"] = await self._read_u32(REG_P3_CURRENT)
  #          _LOGGER.debug(f"P3 current: {data['p3_current']}")

 #           grid_freq_raw = await self._read_u16(REG_GRID_FREQUENCY)
 #           data["grid_frequency"] = grid_freq_raw / 100.0
 #           _LOGGER.debug(f"Grid frequency: {data['grid_frequency']}")

#            data["grid_total_power"] = await self._read_f32(REG_GRID_TOTAL_POWER)
#            _LOGGER.debug(f"Grid total power: {data['grid_total_power']}")
 #           data["grid_p1_power"] = await self._read_f32(REG_GRID_P1_POWER)
 #           _LOGGER.debug(f"Grid P1 power: {data['grid_p1_power']}")
 #           data["grid_p2_power"] = await self._read_f32(REG_GRID_P2_POWER)
 #           _LOGGER.debug(f"Grid P2 power: {data['grid_p2_power']}")
 #           data["grid_p3_power"] = await self._read_f32(REG_GRID_P3_POWER)
 #           _LOGGER.debug(f"Grid P3 power: {data['grid_p3_power']}")
 #           data["error_code"] = await self._read_u64(REG_ERROR_CODE)
 #           _LOGGER.debug(f"Error code: {data['error_code']}")

            _LOGGER.debug(f"Returning data: {data}")
            return data

        except (ConnectionException, ModbusIOException) as ex:
            raise UpdateFailed(f"Error communicating with Modbus device: {ex}") from ex
        except Exception as ex:
            _LOGGER.error("An unexpected error occurred: %s", ex)
            raise UpdateFailed(f"An unexpected error occurred: {ex}") from ex

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