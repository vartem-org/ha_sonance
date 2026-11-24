"""Per-channel fault sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import SonanceEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    c = entry.runtime_data
    async_add_entities(
        SonanceFault(c, ch, kind) for ch in c.model.channels for kind in ("short", "over_temp")
    )


class SonanceFault(SonanceEntity, BinarySensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, channel: str, kind: str) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._kind = kind
        self._attr_unique_id = f"{self._entry_id}_{kind}_{channel}"
        if kind == "short":
            self._attr_name = f"Channel {channel} short circuit"
            self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        else:
            self._attr_name = f"Channel {channel} over temperature"
            self._attr_device_class = BinarySensorDeviceClass.HEAT

    @property
    def is_on(self) -> bool | None:
        return getattr(self.coordinator.data.channels[self._channel], self._kind)
