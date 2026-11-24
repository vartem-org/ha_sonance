"""Media player per amplifier group."""
from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import protocol as p
from .coordinator import SonanceCoordinator
from .entity import SonanceEntity

FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback):
    coordinator = entry.runtime_data
    async_add_entities(SonanceGroupPlayer(coordinator, g) for g in coordinator.model.groups)


class SonanceGroupPlayer(SonanceEntity, MediaPlayerEntity):
    _attr_supported_features = FEATURES

    def __init__(self, coordinator: SonanceCoordinator, group: str) -> None:
        super().__init__(coordinator)
        self._group = group
        self._attr_unique_id = f"{self._entry_id}_group_{group}"
        self._attr_name = f"Group {group}"
        self._attr_source_list = [f"Source {n}" for n in range(1, coordinator.model.sources + 1)]

    @property
    def _state(self):
        return self.coordinator.data.groups[self._group]

    @property
    def state(self) -> MediaPlayerState:
        if not self.coordinator.data.power or not self._state.on:
            return MediaPlayerState.OFF
        return MediaPlayerState.ON

    @property
    def volume_level(self) -> float | None:
        v = self._state.volume_db
        return None if v is None else p.volume_to_ha(v)

    @property
    def is_volume_muted(self) -> bool | None:
        return self._state.muted

    @property
    def source(self) -> str | None:
        n = self._state.source
        return None if n is None else f"Source {n}"

    @property
    def extra_state_attributes(self) -> dict:
        return {"volume_db": self._state.volume_db, "input_name": self._state.source_name}

    async def async_turn_on(self) -> None:
        if not self.coordinator.data.power:
            await self.coordinator.async_set_power(True)
        await self.coordinator.async_group_command(self._group, p.CMD_GROUP_ON)

    async def async_turn_off(self) -> None:
        await self.coordinator.async_group_command(self._group, p.CMD_GROUP_OFF)

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.async_set_volume_db(self._group, p.volume_from_ha(volume))

    async def async_volume_up(self) -> None:
        await self.coordinator.async_group_command(self._group, p.CMD_VOL_UP)

    async def async_volume_down(self) -> None:
        await self.coordinator.async_group_command(self._group, p.CMD_VOL_DOWN)

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.async_group_command(
            self._group, p.CMD_MUTE_ON if mute else p.CMD_MUTE_OFF
        )

    async def async_select_source(self, source: str) -> None:
        await self.coordinator.async_select_source(self._group, int(source.split()[-1]))
