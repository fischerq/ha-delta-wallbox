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

    async def _async_update_data(self):
        """Fetch data from the charger."""
        try:
            if not self.client.is_socket_open():
                self.client.connect()

            # Read all registers in one go to minimize traffic
            result = await self.client.read_input_registers(
                address=0, count=130, slave=self.slave_id
            )
            if result.isError():
                raise UpdateFailed(f"Modbus error: {result}")

            data = {}
            # Charger-Level Sensors
            data["charger_state"] = result.get_register(REG_CHARGER_STATE)
            data["evse_count"] = result.get_register(REG_EVSE_COUNT)
            data["serial_number"] = "".join(
                [
                    chr(c)
                    for c in result.get_registers(REG_SERIAL_NUMBER, 20)
                    if c != 0
                ]
            )
            data["model"] = "".join(
                [chr(c) for c in result.get_registers(REG_MODEL, 20) if c != 0]
            )

            # EVSE-Level Sensors
            data["evse_state"] = result.get_register(REG_EVSE_STATE)
            data["ev_connected"] = result.get_register(REG_EV_CONNECTED)
            data["charging_time"] = self._decode_u32(
                result.get_registers(REG_CHARGING_TIME, 2)
            )
            data["charging_power"] = self._decode_u32(
                result.get_registers(REG_CHARGING_POWER, 2)
            )
            data["charged_energy"] = self._decode_u32(
                result.get_registers(REG_CHARGED_ENERGY, 2)
            )
            data["soc"] = result.get_register(REG_SOC) / 10.0
            data["ev_max_power"] = self._decode_u32(
                result.get_registers(REG_EV_MAX_POWER, 2)
            )
            data["ev_min_power"] = self._decode_u32(
                result.get_registers(REG_EV_MIN_POWER, 2)
            )
            data["p1_voltage"] = self._decode_u32(
                result.get_registers(REG_P1_VOLTAGE, 2)
            )
            data["p2_voltage"] = self._decode_u32(
                result.get_registers(REG_P2_VOLTAGE, 2)
            )
            data["p3_voltage"] = self._decode_u32(
                result.get_registers(REG_P3_VOLTAGE, 2)
            )
            data["p1_current"] = self._decode_u32(
                result.get_registers(REG_P1_CURRENT, 2)
            )
            data["p2_current"] = self._decode_u32(
                result.get_registers(REG_P2_CURRENT, 2)
            )
            data["p3_current"] = self._decode_u32(
                result.get_registers(REG_P3_CURRENT, 2)
            )
            data["grid_frequency"] = result.get_register(REG_GRID_FREQUENCY) / 100.0
            data["grid_total_power"] = self._decode_f32(
                result.get_registers(REG_GRID_TOTAL_POWER, 2)
            )
            data["grid_p1_power"] = self._decode_f32(
                result.get_registers(REG_GRID_P1_POWER, 2)
            )
            data["grid_p2_power"] = self._decode_f32(
                result.get_registers(REG_GRID_P2_POWER, 2)
            )
            data["grid_p3_power"] = self._decode_f32(
                result.get_registers(REG_GRID_P3_POWER, 2)
            )
            data["error_code"] = self._decode_u64(
                result.get_registers(REG_ERROR_CODE, 4)
            )
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
