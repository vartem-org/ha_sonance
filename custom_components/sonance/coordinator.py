"""Data coordinator for Sonance DSP."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import protocol as p
from .client import SonanceClient, SonanceError
from .const import DOMAIN, ModelInfo

_LOGGER = logging.getLogger(__name__)


@dataclass
class GroupState:
    on: bool = True  # amp has no group power query; tracked optimistically
    volume_db: int | None = None
    source: int | None = None
    source_name: str | None = None
    muted: bool | None = None


@dataclass
class ChannelState:
    preset: str | None = None
    short: bool | None = None
    over_temp: bool | None = None
    stereo: bool | None = None


@dataclass
class SonanceData:
    power: bool | None = None
    groups: dict[str, GroupState] = field(default_factory=dict)
    channels: dict[str, ChannelState] = field(default_factory=dict)


class SonanceCoordinator(DataUpdateCoordinator[SonanceData]):
    """Polls the amplifier."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: SonanceClient, model: ModelInfo
    ) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=timedelta(seconds=30)
        )
        self.client = client
        self.model = model
        self._data = SonanceData(
            groups={g: GroupState() for g in model.groups},
            channels={c: ChannelState() for c in model.channels},
        )
        self._polls = 0

    async def _query(self, frame: bytes, expect: str) -> str:
        return await self.client.send(frame, re.compile(expect, re.I))

    async def _refresh_group(self, group: str) -> None:
        gi = p.group_index(group)
        st = self._data.groups[group]
        text = await self._query(p.target_frame(p.CMD_Q_VOLUME, gi), r"Vol\s*=\s*-?\d+")
        st.volume_db = p.parse_volume(text, group)
        text = await self._query(p.target_frame(p.CMD_Q_SOURCE, gi), r"Src\d*\s*=")
        if (src := p.parse_source(text, group)) is not None:
            st.source, st.source_name = src
        text = await self._query(p.target_frame(p.CMD_Q_MUTE, gi), r"Mute\s*=\s*(on|off)")
        st.muted = p.parse_mute(text, group)

    async def _refresh_channel(self, channel: str) -> None:
        ci = p.channel_index(channel)
        st = self._data.channels[channel]
        text = await self._query(p.target_frame(p.CMD_Q_PRESET, ci), r"DSP_Preset.*Channel")
        st.preset = p.parse_channel_value(p.RE_PRESET, text, channel)
        text = await self._query(p.target_frame(p.CMD_Q_SHORT, ci), r"AmpShortCir.*Channel")
        if (v := p.parse_channel_value(p.RE_SHORT, text, channel)) is not None:
            st.short = v.lower() != "no short"
        text = await self._query(p.target_frame(p.CMD_Q_TEMP, ci), r"AmpOverTemp.*Channel")
        if (v := p.parse_channel_value(p.RE_TEMP, text, channel)) is not None:
            st.over_temp = "over" in v.lower()

    async def _async_update_data(self) -> SonanceData:
        try:
            text = await self._query(p.global_frame(p.CMD_Q_POWER), r"Power status\s*:\s*(On|Off)")
            self._data.power = p.parse_power(text)
            for g in self.model.groups:
                await self._refresh_group(g)
            # channel diagnostics are slower-changing: every 4th poll (and the first)
            if self._polls % 4 == 0:
                for c in self.model.channels:
                    await self._refresh_channel(c)
            self._polls += 1
        except SonanceError as err:
            raise UpdateFailed(str(err)) from err
        return self._data

    # ---- commands ----
    async def _command(self, frame: bytes) -> None:
        try:
            await self.client.send(frame, required=False)
        except SonanceError as err:
            raise UpdateFailed(str(err)) from err

    async def async_set_power(self, on: bool) -> None:
        await self._command(p.global_frame(p.CMD_POWER_ON if on else p.CMD_POWER_OFF))
        self._data.power = on
        self.async_set_updated_data(self._data)

    async def async_group_command(self, group: str, cmd: int, refresh: bool = True) -> None:
        await self._command(p.target_frame(cmd, p.group_index(group)))
        if cmd == p.CMD_GROUP_ON:
            self._data.groups[group].on = True
        elif cmd == p.CMD_GROUP_OFF:
            self._data.groups[group].on = False
        if refresh:
            try:
                await self._refresh_group(group)
            except SonanceError as err:
                raise UpdateFailed(str(err)) from err
        self.async_set_updated_data(self._data)

    async def async_set_volume_db(self, group: str, db: int) -> None:
        await self.async_group_command(group, p.volume_code(db))

    async def async_select_source(self, group: str, source: int) -> None:
        await self.async_group_command(group, p.CMD_SOURCE_BASE + source - 1)

    async def async_channel_command(self, channel: str, cmd: int) -> None:
        await self._command(p.target_frame(cmd, p.channel_index(channel)))
        try:
            await self._refresh_channel(channel)
        except SonanceError as err:
            raise UpdateFailed(str(err)) from err
        self.async_set_updated_data(self._data)

    async def async_select_preset(self, channel: str, preset: int) -> None:
        await self.async_channel_command(channel, p.CMD_PRESET_BASE + preset)
