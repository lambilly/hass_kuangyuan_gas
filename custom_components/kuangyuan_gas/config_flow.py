"""Config flow for Kuangyuan Gas integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("uno", description="请输入燃气户号"): str,
        vol.Required("cookie", description="请输入Cookie"): str,
        vol.Required("phone", description="请输入手机号"): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    # 构建完整的Cookie
    phone = data["phone"]
    base_cookie = data["cookie"]
    
    # 构建完整Cookie：用户输入的Cookie + 固定部分 + 手机号部分
    data["full_cookie"] = f"{base_cookie}; pt%5FAppUid=no%5Flogin; safedog-flow-item=E40DAE29FEA3F7315737490DA56A1126; pt%5Fnickname={phone}; pt%5Fuser%5Fname={phone}"
    
    return {"title": "燃气费查询"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kuangyuan Gas."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input["uno"])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={
                "domain": DOMAIN,
            },
            errors=errors,
        )