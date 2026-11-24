"""Base entity."""
from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN
from .coordinator import SonanceCoordinator


class SonanceEntity(CoordinatorEntity[SonanceCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SonanceCoordinator) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._entry_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Sonance",
            model=entry.data[CONF_MODEL],
            name=f"Sonance {entry.data[CONF_MODEL]}",
            configuration_url=None,
            serial_number=None,
        )
        self._host = entry.data[CONF_HOST]
