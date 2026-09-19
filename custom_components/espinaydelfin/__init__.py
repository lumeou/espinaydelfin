import logging
import os
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .config_flow import EspinayDelfinConfigFlow
from .scraper import EspinayDelfinScraper
from .storage import JsonStorage

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Espina & Delfín from a config entry."""
    
    base_url = entry.data.get("base_url")
    username = entry.data.get("username")
    password = entry.data.get("password")

    # Create directory for storage in HA's config directory, respecting the persistent_directory hint
    integration_dir = os.path.dirname(os.path.abspath(__file__))
    storage_dir = os.path.join(integration_dir, "user_files")

    # Asegúrate de que la carpeta existe (o deja que tu código lo haga)
    os.makedirs(storage_dir, exist_ok=True)

    # We don't have the subscriber code yet, so we can't initialize storage 
    # until we've done at least one scrape.
    # We'll store the config in hass.data to allow access from services.
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "config": entry.data,
        "storage_dir": storage_dir,
        "entry": entry
    }

    # Initial sync to get subscriber info and establish storage
    try:
        scraper = EspinayDelfinScraper(
            base_url, 
            username, 
            password, 
            browser_ws_url=entry.data.get("browser_ws_url")
        )
        sub_info, invoices = await scraper.scrape_all()
        
        storage = JsonStorage(storage_dir, sub_info.subscriber_code)
        await storage.save(sub_info, invoices)
        
        _LOGGER.info("EspinayDelfin: Initial sync successful for subscriber %s", sub_info.subscriber_code)
    except Exception as e:
        _LOGGER.error("EspinayDelfin: Initial sync failed: %s", e)
        # We don't raise ConfigEntryNotReady here because the credentials 
        # might be correct but the site is temporarily down. 
        # The user can trigger sync manually via service.
        raise ConfigEntryNotReady(f"Initial sync failed: {e}")

    # Register services
    async def handle_sync_invoices(call: Any) -> None:
        """Service to manually trigger sync."""
        entry_id = entry.entry_id
        conf = hass.data[DOMAIN][entry_id]["config"]
        s_dir = hass.data[DOMAIN][entry_id]["storage_dir"]
        
        overwrite = call.data.get("overwrite", False)
        
        _LOGGER.info("EspinayDelfin: Manual sync triggered (overwrite=%s)", overwrite)
        
        try:
            scraper = EspinayDelfinScraper(
                conf["base_url"], 
                conf["username"], 
                conf["password"],
                browser_ws_url=conf.get("browser_ws_url")
            )
            sub_info, new_invoices = await scraper.scrape_all()
            
            storage = JsonStorage(s_dir, sub_info.subscriber_code)
            
            if overwrite:
                await storage.save(sub_info, new_invoices)
                _LOGGER.info("EspinayDelfin: Manual sync (OVERWRITE) successful.")
            else:
                await storage.update_incremental(sub_info, new_invoices)
                _LOGGER.info("EspinayDelfin: Manual sync (INCREMENTAL) successful.")
                
        except Exception as e:
            _LOGGER.error("EspinayDelfin: Manual sync failed: %s", e)

    hass.services.async_register(DOMAIN, "sync_invoices", handle_sync_invoices)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload Espina & Delfín from Home Assistant."""
    hass.services.async_remove(DOMAIN, "sync_invoices")
    
    del hass.data[DOMAIN][entry.entry_id]

    return True
