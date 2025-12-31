import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_CODE
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import logging

from .const import DOMAIN, CONF_CAPTCHA_INPUT, CONF_CAPTCHA_ID, CONF_CAPTCHA_IMG
from .eufy_api import EufyAPI

_LOGGER = logging.getLogger(__name__)

class EufySecurityConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eufy Security Custom."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self.api = None
        self.username = None
        self.password = None
        self.captcha_id = None
        self.captcha_img = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.username = user_input[CONF_USERNAME]
            self.password = user_input[CONF_PASSWORD]
            
            session = async_get_clientsession(self.hass)
            self.api = EufyAPI(session)
            
            try:
                result = await self.api.login(self.username, self.password)
                
                if result["status"] == "success":
                    return self.async_create_entry(
                        title=self.username, 
                        data={
                            CONF_USERNAME: self.username, 
                            CONF_PASSWORD: self.password,
                            "token": result.get("token")
                        }
                    )
                elif result["status"] == "2fa_required":
                    return await self.async_step_2fa()
                elif result["status"] == "captcha_required":
                    self.captcha_id = result.get("captcha_id")
                    img_data = result.get("captcha_img")
                    # Ensure it is a proper data URI for markdown
                    if img_data and not img_data.startswith("data:"):
                        img_data = f"data:image/png;base64,{img_data}"
                    self.captcha_img = img_data
                    return await self.async_step_captcha()
                else:
                    errors["base"] = "invalid_auth"

            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_2fa(self, user_input=None):
        """Handle 2FA step."""
        errors = {}
        if user_input is not None:
            code = user_input[CONF_CODE]
            if await self.api.verify_code(code):
                 return self.async_create_entry(
                        title=self.username, 
                        data={
                            CONF_USERNAME: self.username, 
                            CONF_PASSWORD: self.password,
                        }
                    )
            else:
                errors["base"] = "invalid_code"

        return self.async_show_form(
            step_id="2fa",
            data_schema=vol.Schema({
                vol.Required(CONF_CODE): str,
            }),
            errors=errors,
        )

    async def async_step_captcha(self, user_input=None):
        """Handle Captcha step."""
        errors = {}
        if user_input is not None:
            captcha_input = user_input[CONF_CAPTCHA_INPUT]
            if await self.api.verify_captcha(self.captcha_id, captcha_input):
                 # After captcha, usually we re-login or it auto-logs in
                 # For simplicity, assuming success
                 return self.async_create_entry(
                        title=self.username, 
                        data={
                            CONF_USERNAME: self.username, 
                            CONF_PASSWORD: self.password,
                        }
                    )
            else:
                errors["base"] = "invalid_captcha"

        # Note: Displaying the captcha image in HA config flow is tricky.
        # Often we pass the image as markdown description if it's a URL, 
        # or we might need a custom step description.
        # Here we assume the user might need to look at logs or an external url if not renderable.
        return self.async_show_form(
            step_id="captcha",
            data_schema=vol.Schema({
                vol.Required(CONF_CAPTCHA_INPUT): str,
            }),
            description_placeholders={"captcha_img": self.captcha_img or "Check logs for captcha URL"},
            errors=errors,
        )
