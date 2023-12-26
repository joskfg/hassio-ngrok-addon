from homeassistant import config_entries
from .const import (CONF_HA_LOCAL_IP_ADDRESS,CONF_HA_LOCAL_PORT,CONF_HA_LOCAL_PROTOCOL,CONF_NGROK_AUTH_TOKEN,CONF_NGROK_DOMAIN,CONF_NGROK_INSTALL_DIR,CONF_NGROK_OS_VERSION,DEFAULT_HA_LOCAL_PROTOCOL,DEFAULT_NGROK_INSTALL_DIR,DEFAULT_NGROK_OS_VERSION,DOMAIN)
from homeassistant.const import (CONF_SCAN_INTERVAL)
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

class NgrokFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="NGrok", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NGROK_AUTH_TOKEN, default='token'): str,
                    vol.Required(CONF_NGROK_DOMAIN): str,
                    vol.Optional(CONF_HA_LOCAL_IP_ADDRESS, default='localhost'): str,
                    vol.Required(CONF_HA_LOCAL_PORT, default=8123): int,
                    vol.Required(CONF_HA_LOCAL_PROTOCOL, default=DEFAULT_HA_LOCAL_PROTOCOL): vol.In(['http', 'https']),
                    vol.Required(CONF_NGROK_OS_VERSION, default=DEFAULT_NGROK_OS_VERSION): vol.In(['Mac OS X', 'Linux', 'Mac (32-Bit)', 'Windows (32-Bit)', 'Linux (ARM)', 'Linux (32-Bit)', 'FreeBSD (64-Bit)', 'FreeBSD (32-Bit)']),
                    vol.Optional(CONF_NGROK_INSTALL_DIR, default=DEFAULT_NGROK_INSTALL_DIR): str,
                }
            ),
            errors=errors,
        )