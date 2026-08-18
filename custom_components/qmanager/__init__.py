"""The QManager integration."""
from __future__ import annotations

from dataclasses import dataclass

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_SSL, Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import QManagerApiClient, QManagerAuthError, QManagerConnectionError
from .const import (
    ATTR_COMMAND,
    DOMAIN,
    SERVICE_SEND_AT_COMMAND,
    SERVICE_START_CELL_SCAN,
)
from .coordinator import QManagerDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


@dataclass
class QManagerRuntimeData:
    """Data stored on the config entry at runtime."""

    api: QManagerApiClient
    coordinator: QManagerDataUpdateCoordinator


QManagerConfigEntry = ConfigEntry[QManagerRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: QManagerConfigEntry) -> bool:
    """Set up QManager from a config entry."""
    session = async_create_clientsession(hass, verify_ssl=False)
    api = QManagerApiClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_PASSWORD],
        use_ssl=entry.data.get(CONF_SSL, False),
    )

    try:
        await api.async_login()
    except QManagerAuthError as err:
        raise ConfigEntryNotReady(f"Invalid QManager password: {err}") from err
    except QManagerConnectionError as err:
        raise ConfigEntryNotReady(f"Could not reach QManager at {entry.data[CONF_HOST]}: {err}") from err

    coordinator = QManagerDataUpdateCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = QManagerRuntimeData(api=api, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _async_register_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: QManagerConfigEntry) -> None:
    """Reload the entry when its options (e.g. poll interval) change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: QManagerConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _entry_for_device(hass: HomeAssistant, device_id: str) -> QManagerConfigEntry:
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if device is None:
        raise ValueError(f"Unknown device_id {device_id}")
    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and entry.domain == DOMAIN:
            return entry
    raise ValueError(f"Device {device_id} is not a QManager device")


def _async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_SEND_AT_COMMAND):
        return

    async def async_send_at_command(call: ServiceCall) -> ServiceResponse:
        entry = _entry_for_device(hass, call.data["device_id"])
        response = await entry.runtime_data.api.async_send_at_command(
            call.data[ATTR_COMMAND]
        )
        return {"response": response}

    async def async_start_cell_scan(call: ServiceCall) -> None:
        entry = _entry_for_device(hass, call.data["device_id"])
        await entry.runtime_data.api.async_start_cell_scan()

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_AT_COMMAND,
        async_send_at_command,
        schema=vol.Schema(
            {
                vol.Required("device_id"): str,
                vol.Required(ATTR_COMMAND): str,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_START_CELL_SCAN,
        async_start_cell_scan,
        schema=vol.Schema({vol.Required("device_id"): str}),
    )
