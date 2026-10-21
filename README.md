# Delta Wallbox Home Assistant Integration

Integrate your Delta Wallbox with Home Assistant to monitor and control your EV charging.

## Setup

1.  **Install the Integration.**
    Add `https://github.com/fischerq/ha-delta-wallbox` as a custom repository in HACS (category Integration), or manually copy the `custom_components/delta_wallbox` directory to the `custom_components` directory of your Home Assistant installation.
2.  **Add the Delta Wallbox integration.**
    *   Go to Settings -> Devices & Services -> Add Integration.
    *   Search for "Delta Wallbox" and select it.
    *   Enter the IP address, port, and slave ID of your Delta Wallbox when prompted.

## Provided Entities

Read every 30 s from EVSE 1:

*   **Sensors:** Charger State, Charge State, Charging Power (W), Session Energy (Wh), Output Voltage, Output Current, Charging Time, Serial Number
*   **Number:** Charging Power Limit (W). It is written to holding register 1600 and read back on every poll.
*   **Switch:** Charging Enabled. Off suspends charging (register 1602) and keeps the cable locked; on resumes.

The entities are named `…delta_wallbox_charging_power`, `…delta_wallbox_charging_power_limit` and so on.

## Register map and verification

The addresses come from Delta's EVCS Modbus register table, as documented
for the AC MAX at <https://taphome.com/en/compatibility/delta-ac-max/>.
EVSE 1 registers are base + 1000: input 1001 charge state, 1005 power,
1019 session energy; holding 1600 power limit, 1602 suspend.

Check them on your unit before relying on the controls. Run the read-only
probe and compare with the wallbox app:

```bash
pip install "pymodbus>=3.10"
python3 scripts/probe.py 192.168.25.199 --device-id 1
```

If every value looks shifted by one register, set `REGISTER_OFFSET` in
`const.py` (some RS485 bridges use 1-based addresses).

## Development

```bash
pip install -r requirements.txt
pytest tests && black --check .
```

The tests run the real client against an in-memory Modbus fake
(`tests/fake_modbus.py`), including the full Home Assistant setup and
service calls.

## Implementation

Interaction with the Delta Wallbox is implemented using Modbus TCP. The `pymodbus` library is used to communicate with the wallbox.

The data is fetched periodically by the `coordinator.py` and provided to the entities in `sensor.py`, `number.py`, and `switch.py`. The configuration dialog is implemented in `config_flow.py`.
