
import pytest
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.delta_wallbox.const import (
    DOMAIN,
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SLAVE_ID,
)

MOCK_IP_ADDRESS = "1.2.3.4"
MOCK_PORT = 502
MOCK_SLAVE_ID = 1


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Mock async_setup_entry to bypass actual setup."""
    with patch(
        "custom_components.delta_wallbox.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


async def test_config_flow_user_step(hass: HomeAssistant):
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # Test successful submission
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
            CONF_PORT: MOCK_PORT,
            CONF_SLAVE_ID: MOCK_SLAVE_ID,
        },
    )
    await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Delta Wallbox {MOCK_IP_ADDRESS}"
    assert result2["data"] == {
        CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
        CONF_PORT: MOCK_PORT,
        CONF_SLAVE_ID: MOCK_SLAVE_ID,
    }
    assert (
        result2["result"].unique_id
        == f"{MOCK_IP_ADDRESS}-{MOCK_SLAVE_ID}"
    )


async def test_config_flow_already_configured(hass: HomeAssistant):
    """Test config flow when an entry with the same unique ID already exists."""
    # Create a mock entry first
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=f"{MOCK_IP_ADDRESS}-{MOCK_SLAVE_ID}",
        data={
            CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
            CONF_PORT: MOCK_PORT,
            CONF_SLAVE_ID: MOCK_SLAVE_ID,
        },
        title=f"Delta Wallbox {MOCK_IP_ADDRESS}",
    )
    mock_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # Try to configure a new flow with the same details
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_IP_ADDRESS: MOCK_IP_ADDRESS,
            CONF_PORT: MOCK_PORT,
            CONF_SLAVE_ID: MOCK_SLAVE_ID,
        },
    )
    assert result2["type"] == data_entry_flow.FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
