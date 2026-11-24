"""Unit power and per-channel stereo/mono switches."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import protocol as p
from .entity import SonanceEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    c = entry.runtime_data
    entities = [SonancePowerSwitch(c)]
    entities += [SonanceStereoSwitch(c, ch) for ch in c.model.channels]
    async_add_entities(entities)


class SonancePowerSwitch(SonanceEntity, SwitchEntity):
    _attr_name = "Power"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._entry_id}_power"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.power

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_power(False)


class SonanceStereoSwitch(SonanceEntity, SwitchEntity):
    """On = stereo, off = mono."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, channel: str) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{self._entry_id}_stereo_{channel}"
        self._attr_name = f"Channel {channel} stereo"

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.channels[self._channel].stereo

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_channel_command(self._channel, p.CMD_STEREO_ON)
        self.coordinator.data.channels[self._channel].stereo = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_channel_command(self._channel, p.CMD_MONO_ON)
        self.coordinator.data.channels[self._channel].stereo = False
        self.async_write_ha_state()
