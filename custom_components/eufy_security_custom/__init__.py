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
    from .const import CONF_WS_URL
    from .eufy_api import EufyWS
    
    ws_url = entry.data.get(CONF_WS_URL, "ws://localhost:3000")
    api = EufyWS(session, ws_url)
    
    # Store the API object for your platforms to access
    hass.data[DOMAIN][entry.entry_id] = api

    # Start the persistent connection
    # hass.async_create_task(api.connect_and_login(..., ...)) 
    # For now just storing it.
    
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
