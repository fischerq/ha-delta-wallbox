"""Synchronous Modbus client for the Delta AC MAX; call from an executor."""

from __future__ import annotations

import threading

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    CHARGE_STATE_MAP,
    CHARGER_STATE_MAP,
    NO_LIMIT,
    REG_CHARGE_STATE,
    REG_CHARGED_ENERGY,
    REG_CHARGER_SERIAL_NUMBER,
    REG_CHARGER_STATE,
    REG_CHARGING_POWER,
    REG_CHARGING_TIME,
    REG_EVSE_BLOCK_COUNT,
    REG_EVSE_BLOCK_START,
    REG_EVSE_CONDITION,
    REG_OUTPUT_CURRENT,
    REG_OUTPUT_VOLTAGE,
    REG_POWER_LIMIT,
    REG_SUSPEND_CHARGING,
    REGISTER_OFFSET,
    SERIAL_LENGTH,
)


def _u32(regs: list[int], i: int) -> int:
    return (regs[i] << 16) | regs[i + 1]


class DeltaWallboxClient:
    """Reads EVSE 1 in two requests and writes the power limit / suspend flag."""

    def __init__(self, host: str, port: int, device_id: int, client=None):
        self.device_id = device_id
        self._client = client or ModbusTcpClient(host, port=port)
        self._lock = threading.Lock()

    def close(self) -> None:
        self._client.close()

    def _read(self, kind: str, address: int, count: int) -> list[int]:
        fn = getattr(self._client, f"read_{kind}_registers")
        result = fn(
            address=address + REGISTER_OFFSET, count=count, device_id=self.device_id
        )
        if result.isError():
            raise ModbusException(f"read {kind} {address}+{count} failed: {result}")
        return list(result.registers)

    def _write(self, address: int, values: list[int]) -> None:
        result = self._client.write_registers(
            address=address + REGISTER_OFFSET, values=values, device_id=self.device_id
        )
        if result.isError():
            raise ModbusException(f"write {address}={values} failed: {result}")

    def read_serial(self) -> str:
        with self._lock:
            regs = self._read("input", REG_CHARGER_SERIAL_NUMBER, SERIAL_LENGTH)
        chars = []
        for r in regs:
            if r == 0:
                break
            chars.append(chr(r & 0xFF))
        return "".join(chars).strip()

    def read_state(self) -> dict:
        """One poll: charger state, EVSE 1 measurements, current power limit."""
        with self._lock:
            charger = self._read("input", REG_CHARGER_STATE, 1)[0]
            evse = self._read("input", REG_EVSE_BLOCK_START, REG_EVSE_BLOCK_COUNT)
            limit_regs = self._read("holding", REG_POWER_LIMIT, 3)

        def at(reg):
            return reg - REG_EVSE_BLOCK_START

        limit = _u32(limit_regs, 0)
        charge_state = evse[at(REG_CHARGE_STATE)]
        return {
            "charger_state": CHARGER_STATE_MAP.get(charger, str(charger)),
            "evse_condition": evse[at(REG_EVSE_CONDITION)],
            "charge_state": CHARGE_STATE_MAP.get(charge_state, str(charge_state)),
            "charging": charge_state == 3,
            "output_voltage": _u32(evse, at(REG_OUTPUT_VOLTAGE)) / 10,
            "charging_power": _u32(evse, at(REG_CHARGING_POWER)),
            "output_current": _u32(evse, at(REG_OUTPUT_CURRENT)) / 100,
            "charging_time": _u32(evse, at(REG_CHARGING_TIME)),
            "charged_energy": _u32(evse, at(REG_CHARGED_ENERGY)),
            "power_limit": None if limit == NO_LIMIT else limit,
            "suspended": bool(limit_regs[2]),
        }

    def set_power_limit(self, watts: int | None) -> None:
        """Set the charging power limit in W; None removes the limit."""
        value = NO_LIMIT if watts is None else int(watts)
        if not 0 <= value <= NO_LIMIT:
            raise ValueError(f"invalid power limit {watts}")
        with self._lock:
            self._write(REG_POWER_LIMIT, [value >> 16, value & 0xFFFF])

    def set_suspended(self, suspended: bool) -> None:
        with self._lock:
            self._write(REG_SUSPEND_CHARGING, [1 if suspended else 0])
