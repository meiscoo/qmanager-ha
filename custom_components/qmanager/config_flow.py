"""Config flow for QManager."""
from __future__ import annotations

import logging
from collections.abc import Mapping
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


STEP_REAUTH_DATA_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): str})


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

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start re-authentication when the stored password stops working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the new QManager password and validate it."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            data = {**entry.data, CONF_PASSWORD: user_input[CONF_PASSWORD]}
            try:
                imei = await _validate_and_get_imei(self.hass, data)
            except QManagerAuthError:
                errors["base"] = "invalid_auth"
            except (QManagerConnectionError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during QManager reauth")
                errors["base"] = "unknown"
            else:
                # Guard against the host now answering as a different modem.
                if imei and entry.unique_id and imei != entry.unique_id:
                    return self.async_abort(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_REAUTH_DATA_SCHEMA,
            description_placeholders={"host": entry.data[CONF_HOST]},
            errors=errors,
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
