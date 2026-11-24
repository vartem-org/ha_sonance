"""Sonance DSP amplifier integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .client import SonanceClient
from .const import CONF_MODEL, MODELS
from .coordinator import SonanceCoordinator

PLATFORMS = [
    Platform.MEDIA_PLAYER,
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
]

type SonanceConfigEntry = ConfigEntry[SonanceCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SonanceConfigEntry) -> bool:
    client = SonanceClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
    coordinator = SonanceCoordinator(hass, entry, client, MODELS[entry.data[CONF_MODEL]])
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SonanceConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.client.close()
    return unloaded
