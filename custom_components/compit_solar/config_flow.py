import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from compit_inext_api.connector import CompitApiConnector

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class CompitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            connector = CompitApiConnector(session)
            try:
                # Weryfikacja danych logowania
                success = await connector.init(user_input[CONF_EMAIL], user_input[CONF_PASSWORD], lang="en")
                if success:
                    return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)
                else:
                    errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Nieoczekiwany błąd podczas weryfikacji logowania do chmury")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors
        )