from typing import Any, Dict, List, Optional

from homeassistant import config_entries
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import EspinayDelfinUpdateCoordinator

async def async_setup_entry(
    hass: Any,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors for the entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        EspinayDelfinInvoicesSensor(hass, entry, coordinator),
        EspinayDelfinConsumptionSensor(hass, entry, coordinator),
    ]

    async_add_entities(sensors)

class EspinayDelfinInvoicesSensor(CoordinatorEntity, SensorEntity):
    """Represents the Espina & Delfín invoices data."""

    def __init__(
        self,
        hass: Any,
        entry: config_entries.ConfigEntry,
        coordinator: EspinayDelfinUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._coordinator = coordinator
        
        self._name = "Invoices"
        self._unique_id = f"{entry.entry_id}_invoices"
        self._attr_name = "Espina & Delfín Invoices"
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_native_unit_of_measurement = "€"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}

        sub_info = self.coordinator.subscriber_info
        invoices = self.coordinator.invoices

        subscriber_dict = sub_info.to_dict() if sub_info else {}
        invoices_list = [inv.to_ha_dict() for inv in invoices]

        return {
            "subscriber_info": subscriber_dict,
            "invoices": invoices_list,
        }

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor (latest invoice amount)."""
        if not self.coordinator.invoices:
            return None
        return self.coordinator.invoices[-1].amount_euro

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """Return device info."""
        return DeviceInfo(
            identifiers={{self._entry.entry_id}},
            name=self._attr_name,
            manufacturer="Espinay & Delfín",
        )

class EspinayDelfinConsumptionSensor(CoordinatorEntity, SensorEntity):
    """Represents the Espina & Delfín consumption data."""

    def __init__(
        self,
        hass: Any,
        entry: config_entries.ConfigEntry,
        coordinator: EspinayDelfinUpdateCoordinator,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._hass = hass
        self._entry = entry
        self._coordinator = coordinator
        
        self._name = "Consumption"
        self._unique_id = f"{entry.entry_id}_consumption"
        self._attr_name = "Espinay & Delfín Consumption"
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_native_unit_of_measurement = "m³"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.coordinator.last_update_success

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return entity specific state attributes."""
        if not self.coordinator.data:
            return {}

        invoices = self.coordinator.invoices
        consumption_history = [
            {"period": inv.period, "consumption": inv.consumption_m3}
            for inv in invoices
        ]

        return {
            "consumption_history": consumption_history,
        }

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor (latest invoice consumption)."""
        if not self.coordinator.invoices:
            return None
        return self.coordinator.invoices[-1].consumption_m3

    @property
    def device_info(self) -> Optional[DeviceInfo]:
        """Return device info."""
        return DeviceInfo(
            identifiers={{self._entry.entry_id}},
            name=self._attr_name,
            manufacturer="Espinay & Delfín",
        )
