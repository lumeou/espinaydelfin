import logging
import os
from typing import Any, Dict

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .scraper import EspinayDelfinScraper
from .storage import JsonStorage
from .coordinator import EspinayDelfinUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Espina & Delfín from a config entry."""
    
    base_url = entry.data.get("base_url")
    username = entry.data.get("username")
    password = entry.data.get("password")
    browser_ws_url = entry.data.get("browser_ws_url")

    # Create directory for storage in HA's config directory
    integration_dir = os.path.dirname(os.path.abspath(__file__))
    storage_dir = os.path.join(integration_dir, "user_files")
    os.makedirs(storage_dir, exist_ok=True)

    # Initialize Scraper and Storage
    scraper = EspinayDelfinScraper(
        base_url, 
        username, 
        password, 
        browser_ws_url=browser_ws_url
    )
    storage = JsonStorage(storage_dir, "initial_setup") # Placeholder until first scrape

    # Initialize Coordinator
    coordinator = EspinayDelfinUpdateCoordinator(
        hass,
        entry,
        scraper=scraper,
        storage=storage
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Perform initial sync to establish real storage path with subscriber code
    try:
        # We run a one-time scrape to get the subscriber_code
        sub_info, invoices = await scraper.scrape_all()
        
        # Re-initialize storage with the correct subscriber code
        real_storage = JsonStorage(storage_dir, sub_info.subscriber_code)
        await real_storage.save(sub_info, invoices)
        
        # Update coordinator with the real storage and the data we just got
        coordinator.storage = real_storage
        coordinator.subscriber_info = sub_info
        coordinator.invoices = invoices
        
        _LOGGER.info("EspinayDelfin: Initial sync successful for subscriber %s", sub_info.subscriber_code)
    except Exception as e:
        _LOGGER.error("EspinayDelfin: Initial sync failed: %s", e)
        raise ConfigEntryNotReady(f"Initial sync failed: {e}")

    # Register services
    async def handle_sync_invoices(call: Any) -> None:
        """Service to manually trigger sync."""
        conf = entry.data
        
        overwrite = call.data.get("overwrite", False)
        
        _LOGGER.info("EspinayDelfin: Manual sync triggered (overwrite=%s)", overwrite)
        
        try:
            scraper = EspinayDelfinScraper(
                conf["base_url"], 
                conf["username"], 
                conf["password"],
                browser_ws_url=conf.get("browser_ws_url")
            )
            # We use the coordinator to perform the sync, which handles storage and refreshing
            await coordinator.async_manual_sync(overwrite=overwrite)
                
        except Exception as e:
            _LOGGER.error("EspinayDelfin: Manual sync failed: %s", e)

    hass.services.async_register(DOMAIN, "sync_invoices", handle_sync_invoices)

    # Set up sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Espina & Delfín from Home Assistant."""
    # Descargar las plataformas asociadas a la entrada de configuración
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    
    if unload_ok:
        # Eliminar el servicio personalizado que hayas registrado (si aplica)
        hass.services.async_remove(DOMAIN, "sync_invoices")
        
        # Eliminar los datos almacenados para esta entrada
        # Se asume que hass.data[DOMAIN] es un diccionario que contiene entry.entry_id
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            del hass.data[DOMAIN][entry.entry_id]
    
    # 4. Retornar el resultado de la descarga de plataformas
    return unload_ok
