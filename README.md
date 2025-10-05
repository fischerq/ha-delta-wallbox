# Braiins Pool Home Assistant Integration

Monitor your Braiins Pool mining statistics directly within Home Assistant. 

## Setup

1.  **Obtain your API key for the Braiins Pool API.**\
    Follow the instructions in the Braiins Pool API documentation: [https://academy.braiins.com/en/braiins-pool/monitoring/#overview](https://academy.braiins.com/en/braiins-pool/monitoring/#overview)
1.  **Install the Integration.**\
    This integration is available through HACS (Home Assistant Community Store). Click the following button to add it to your Home Assistant: \
    [![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=braiins_pool)\
    \
    Alternatively add it manually with the following steps:
    1.  **Add this repository as a Custom Repository in HACS.**
        *   In HACS, go to the Integrations tab.
        *   Click on the three dots in the top right corner and select `Custom repositories`.
        *   Enter the URL of this repository (`https://github.com/fischerq/ha-braiins-pool/`) and select the category `Integration`.
        *   Click `Add`.
    1.  **Install the integration.**
        *   Search for "Braiins Pool" in the HACS Integrations tab.
        *   Click "Download" and restart Home Assistant.
1.  **Add the Braiins Pool integration.**
    *   Go to Settings -> Devices & Services -> Add Integration.
    *   Search for Braiins Pool` and select it.
    *   Enter your Braiins Pool API Key when prompted. Also enter the name of your Braiins Pool Reward Account (for display, not used for anything else yet).

## Provided Entities

This integration will create sensors for:

*   `today_reward`: Braiins Pool Today's Reward
    *   Also available as `today_reward_satoshi`: Braiins Pool Today's Reward Satoshi
*   `current_balance`: Braiins Pool Current Balance
    *   Also available as `current_balance_satoshi`: Braiins Pool Current Balance Satoshi
*   `all_time_reward`: Braiins Pool All Time Reward
    *   Also available as `all_time_reward_satoshi`: Braiins Pool All Time Reward Satoshi
*   `pool_5m_hash_rate`: Braiins Pool 5m Hash Rate
*   `ok_workers`: Braiins Pool Active Workers

## Implementation

Interaction with the Braiins Pool API is implemented in `api.py`.

Sensors are populated by parsing the [User Profile API](https://academy.braiins.com/en/braiins-pool/monitoring/#user-profile-api) endpoint.

Fetching or parsing the other API endpoints is not implemented yet. Feel free to contribute if you need it.

 Providing the data to Home Assistant in the correct format is implemented in `coordinator.py` and `sensor.py`. `config_flow.py` holds the configuration dialog.
