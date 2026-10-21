"""Constants for the Delta Wallbox integration."""

DOMAIN = "delta_wallbox"

# Configuration
CONF_IP_ADDRESS = "ip_address"
CONF_PORT = "port"
CONF_SLAVE_ID = "slave_id"

DEFAULT_PORT = 502
# Fast enough for PV-surplus control (the energy controller runs every 60 s).
DEFAULT_SCAN_INTERVAL = 30

# Register map of the Delta AC MAX (Basic: Modbus RTU via a TCP bridge,
# Smart: Modbus TCP), from Delta's EVCS Modbus register table as documented
# at https://taphome.com/en/compatibility/delta-ac-max/ — EVSE 1 registers
# are the base register + 1000. Addresses are protocol (0-based) addresses.
# Verify on the device with scripts/probe.py; REGISTER_OFFSET shifts every
# read and write if the bridge turns out to be 1-based.
REGISTER_OFFSET = 0

# Input registers — charger
REG_CHARGER_STATE = 100  # u16: 0 not ready, 1 operational, 2 faulted
REG_CHARGER_SERIAL_NUMBER = 110  # string, one ASCII char per register
SERIAL_LENGTH = 20

# Input registers — EVSE 1
REG_EVSE_BLOCK_START = 1000
REG_EVSE_BLOCK_COUNT = 21  # 1000..1020
REG_EVSE_CONDITION = 1000  # u16 OCPP status
REG_CHARGE_STATE = 1001  # u16
REG_OUTPUT_VOLTAGE = 1003  # u32, 0.1 V
REG_CHARGING_POWER = 1005  # u32, W
REG_OUTPUT_CURRENT = 1007  # u32, 0.01 A
REG_CHARGING_TIME = 1017  # u32, s
REG_CHARGED_ENERGY = 1019  # u32, Wh (current session)

# Holding registers — EVSE 1
REG_POWER_LIMIT = 1600  # i32, W; 0xFFFFFFFF = no limit
REG_SUSPEND_CHARGING = 1602  # 1 = pause, 0 = resume
NO_LIMIT = 0xFFFFFFFF

CHARGER_STATE_MAP = {0: "not_ready", 1: "operational", 2: "faulted"}
CHARGE_STATE_MAP = {
    0: "not_started",
    1: "connected_waiting",
    2: "starting",
    3: "charging",
    4: "suspended",
    5: "completed",
    6: "completed_by_user",
    7: "error",
}
