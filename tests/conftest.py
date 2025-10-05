# tests/conftest.py
import pytest

# Enable pytest_homeassistant_custom_component fixtures
pytest_plugins = "pytest_homeassistant_custom_component"


# Automatically enable custom integrations for all tests
@pytest.fixture(autouse=True)
async def auto_enable_custom_integrations(enable_custom_integrations):
    yield


# The hass_config fixture is used by pytest-homeassistant-custom-component
# to configure the Home Assistant instance before it's fully set up.
# We provide "UTC" as the time_zone, which should be universally available.
@pytest.fixture
def hass_config():
    """Provide configuration for the Home Assistant Core instance."""
    return {"time_zone": "UTC"}
