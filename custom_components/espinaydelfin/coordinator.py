import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .models import Invoice, SubscriberInfo
from .scraper import EspinayDelfinScraper
from .storage import JsonStorage

_LOGGER = logging.getLogger(__name__)

class EspinayDelfinUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage periodic updates for Espina & Delfín."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: config_entries.ConfigEntry,
        scraper: EspinayDelfinScraper,
        storage: JsonStorage,
        update_interval: timedelta = timedelta(hours=24),
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            DOMAIN,
            name="EspinayDelfinScraper",
            update_interval=update_interval,
        )
        self.entry = entry
        self.scraper = scraper
        self.storage = storage
        self.subscriber_info: Optional[SubscriberInfo] = None
        self.invoices: List[Invoice] = []

    async def _async_update_data(self) -> None:
        """Fetch new data from the scraper and update storage."""
        try:
            _LOGGER.info("EspinayDelfin: Starting periodic sync...")
            sub_info, new_invoices = await self.scraper.scrape_all()
            
            # Update storage incrementally
            await self.storage.update_incremental(sub_info, new_invoices)
            
            # Load the final state from storage to ensure consistency
            updated_sub_info, updated_invoices = await self.storage.load()
            
            if updated_sub_info is None:
                raise UpdateFailed("Could not load subscriber info from storage after update.")

            self.subscriber_info = updated_sub_info
            self.invoices = updated_invoices
            
            _LOGGER.info("EspinayDelfin: Periodic sync successful. Found %d invoices.", len(self.invoices))

        except Exception as err:
            _LOGGER.error("EspinayDelfin: Periodic sync failed: %s", err)
            raise UpdateFailed(f"Error communicating with service: {err}") from err

    async def async_manual_sync(self, overwrite: bool = False) -> None:
        """Manually trigger a sync, optionally overwriting history."""
        try:
            _LOGGER.info("EspinayDelfin: Manual sync triggered (overwrite=%s)", overwrite)
            sub_info, new_invoices = await self.scraper.scrape_all()
            
            if overwrite:
                await self.storage.save(sub_info, new_invoices)
                _LOGGER.info("EspinayDelfin: Manual sync (OVERWRITE) successful.")
            else:
                await self.storage.update_incremental(sub_info, new_invoices)
                _LOGGER.info("EspinayDelfin: Manual sync (INCREMENTAL) successful.")

            # Force a refresh of the coordinator data after manual sync
            await self.async_request_refresh()
            
        except Exception as err:
            _LOGGER.error("EspinayDelfin: Manual sync failed: %s", err)
            raise
