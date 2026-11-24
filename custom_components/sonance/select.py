"""Per-channel EQ preset select."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import SonanceEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    c = entry.runtime_data
    async_add_entities(SonancePreset(c, ch) for ch in c.model.channels)


class SonancePreset(SonanceEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, channel: str) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{self._entry_id}_preset_{channel}"
        self._attr_name = f"Channel {channel} EQ preset"
        self._attr_options = list(coordinator.model.presets)

    @property
    def current_option(self) -> str | None:
        preset = self.coordinator.data.channels[self._channel].preset
        # amp reports the preset name; tolerate case/whitespace differences
        for opt in self._attr_options:
            if preset and opt.lower() == preset.strip().lower():
                return opt
        return None

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_select_preset(self._channel, self._attr_options.index(option))
