"""Config flow for Delta Wallbox integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_IP_ADDRESS,
    CONF_PORT,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
)

_LOGGER = logging.getLogger(__name__)


class DeltaWallboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Delta Wallbox."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_IP_ADDRESS]}-{user_input[CONF_SLAVE_ID]}"
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Delta Wallbox {user_input[CONF_IP_ADDRESS]}", data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_IP_ADDRESS): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_SLAVE_ID): int,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return super().async_get_options_flow(config_entry)