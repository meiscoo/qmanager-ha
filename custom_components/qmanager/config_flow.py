"""Config flow for QManager."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_SSL
from homeassistant.core import callback

from .api import QManagerApiClient, QManagerAuthError, QManagerConnectionError
from .const import (
    CONF_SCAN_INTERVAL_SECONDS,
    DEFAULT_PORT,
    DOMAIN,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SSL, default=False): bool,
    }
)


async def _validate_and_get_imei(hass, data: dict[str, Any]) -> str | None:
    """Try logging in and pulling status; return the modem IMEI if available."""
    # unsafe=True: QManager modems are typically reached by bare IP (LAN or
    # Tailscale), and aiohttp's default cookie jar silently drops Set-Cookie
    # for IP hosts otherwise, which breaks session auth after login.
    async with aiohttp.ClientSession(
        cookie_jar=aiohttp.CookieJar(unsafe=True)
    ) as session:
        api = QManagerApiClient(
            session,
            data[CONF_HOST],
            data[CONF_PORT],
            data[CONF_PASSWORD],
            use_ssl=data.get(CONF_SSL, False),
        )
        await api.async_login()
        status = await api.async_get_status()

    return status.get("device", {}).get("imei")


class QManagerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for QManager."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                imei = await _validate_and_get_imei(self.hass, user_input)
            except QManagerAuthError:
                errors["base"] = "invalid_auth"
            except QManagerConnectionError:
                errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating QManager connection")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    imei or f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"QManager ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return QManagerOptionsFlow()


class QManagerOptionsFlow(OptionsFlow):
    """Handle QManager options (poll interval)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(CONF_SCAN_INTERVAL_SECONDS, 30)
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL_SECONDS, default=current
                ): vol.All(int, vol.Range(min=MIN_SCAN_INTERVAL)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
