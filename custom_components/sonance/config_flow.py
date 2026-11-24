"""Config flow for Sonance DSP."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from . import protocol as p
from .client import SonanceClient, SonanceError
from .const import CONF_MODEL, DEFAULT_PORT, DOMAIN, MODELS


class SonanceConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            client = SonanceClient(user_input[CONF_HOST], user_input[CONF_PORT])
            try:
                text = await client.send(
                    p.global_frame(p.CMD_Q_POWER), re.compile(r"Power status", re.I)
                )
                if p.parse_power(text) is None:
                    errors["base"] = "invalid_response"
            except SonanceError:
                errors["base"] = "cannot_connect"
            finally:
                await client.close()
            if not errors:
                return self.async_create_entry(
                    title=f"Sonance {user_input[CONF_MODEL]} ({user_input[CONF_HOST]})",
                    data=user_input,
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Required(CONF_MODEL): vol.In(list(MODELS)),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
