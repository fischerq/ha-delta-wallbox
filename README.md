# Delta Wallbox Home Assistant Integration

Integrate your Delta Wallbox with Home Assistant to monitor and control your EV charging.

## Setup

1.  **Install the Integration.**
    This integration is not yet available in HACS. To install it, you will need to manually copy the `custom_components/delta_wallbox` directory to the `custom_components` directory of your Home Assistant installation.
2.  **Add the Delta Wallbox integration.**
    *   Go to Settings -> Devices & Services -> Add Integration.
    *   Search for "Delta Wallbox" and select it.
    *   Enter the IP address, port, and slave ID of your Delta Wallbox when prompted.

## Provided Entities

This integration will create the following entities:

*   **Sensors:**
    *   Charger State
    *   EVSE Count
    *   Serial Number
    *   Model
    *   EVSE State
    *   EV Connected
    *   Charging Time
    *   Charging Power
    *   Charged Energy
    *   State of Charge
    *   EV Max Power
    *   EV Min Power
    *   Phase 1 Voltage
    *   Phase 2 Voltage
    *   Phase 3 Voltage
    *   Phase 1 Current
    *   Phase 2 Current
    *   Phase 3 Current
    *   Grid Frequency
    *   Grid Total Power Consumption
    *   Grid Phase 1 Power
    *   Grid Phase 2 Power
    *   Grid Phase 3 Power
    *   Error Code
*   **Number:**
    *   Power Limit
*   **Switch:**
    *   Charging

## Implementation

Interaction with the Delta Wallbox is implemented using Modbus TCP. The `pymodbus` library is used to communicate with the wallbox.

The data is fetched periodically by the `coordinator.py` and provided to the entities in `sensor.py`, `number.py`, and `switch.py`. The configuration dialog is implemented in `config_flow.py`.
