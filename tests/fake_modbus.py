"""In-memory stand-in for pymodbus' ModbusTcpClient."""


class Result:
    def __init__(self, registers=None, error=False):
        self.registers = registers or []
        self._error = error

    def isError(self):  # noqa: N802 - pymodbus API
        return self._error


class FakeModbus:
    def __init__(self):
        self.input = {}
        self.holding = {1600: 0xFFFF, 1601: 0xFFFF, 1602: 0}
        self.writes = []
        self.fail = False
        self.closed = False

    def _read(self, table, address, count):
        if self.fail:
            return Result(error=True)
        return Result([table.get(address + i, 0) for i in range(count)])

    def read_input_registers(self, address, count, device_id):
        return self._read(self.input, address, count)

    def read_holding_registers(self, address, count, device_id):
        return self._read(self.holding, address, count)

    def write_registers(self, address, values, device_id):
        self.writes.append((address, list(values)))
        if self.fail:
            return Result(error=True)
        for i, v in enumerate(values):
            self.holding[address + i] = v
        return Result()

    def close(self):
        self.closed = True


def charging_scenario(fake: FakeModbus) -> None:
    """A car charging at 7.4 kW, 3.2 kWh into the session."""
    fake.input.update({100: 1, 1000: 3, 1001: 3})
    fake.input.update({1003: 0, 1004: 2301, 1005: 0, 1006: 7400, 1007: 0, 1008: 3200})
    fake.input.update({1017: 0, 1018: 1800, 1019: 0, 1020: 3200})
    for i, ch in enumerate("DELTA123"):
        fake.input[110 + i] = ord(ch)
