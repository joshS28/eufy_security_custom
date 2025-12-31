"""The Eufy Security Custom integration."""
import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_USERNAME, CONF_PASSWORD
from .eufy_api import EufyAPI
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [] # Add platforms like "camera", "sensor" here later

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Eufy Security Custom component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Eufy Security Custom from a config entry."""
    session = async_get_clientsession(hass)
    api = EufyAPI(session)
    
    # Store the API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = api

    # Perform initial login/connection checks if needed
    # await api.connect()

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
