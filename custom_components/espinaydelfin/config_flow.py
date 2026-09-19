import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.helpers.config_flow import ConfigFlowResult

from .const import DOMAIN, DEFAULT_BASE_URL, DEFAULT_BROWSERLESS_URL

class EspinayDelfinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Espina & Delfín."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> "ConfigFlowResult":
        """Handle the initial step."""

        errors = {}

        if user_input is not None:
            # Validate input
            username = user_input["username"]
            password = user_input["password"]
            base_url = user_input["base_url"]
            browserless_url = user_input.get("browserless_url", "")

            await self.async_set_unique_id(username.lower())
            self._abort_if_unique_id_configured()

            # In a real integration, we would verify credentials here using the scraper.
            # For now, we assume they are valid if provided.
            
            return self.async_create_entry(
                title=f"Cuenta de suministro Espina y Delfín ({username})",
                data={
                    "username": username,
                    "password": password,
                    "base_url": base_url,
                    "browserless_url": browserless_url,
                },
            )

        # Display the form
        data_schema = vol.Schema({
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("base_url", default=DEFAULT_BASE_URL): str,
            vol.Required("browserless_url", default=DEFAULT_BROWSERLESS_URL): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
