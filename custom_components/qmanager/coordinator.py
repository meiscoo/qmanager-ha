"""DataUpdateCoordinator for QManager."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import QManagerApiClient, QManagerAuthError, QManagerConnectionError
from .const import CONF_SCAN_INTERVAL_SECONDS, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class QManagerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls a QManager instance's fetch_data.sh cache on an interval."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, config_entry: ConfigEntry, api: QManagerApiClient
    ) -> None:
        seconds = config_entry.options.get(CONF_SCAN_INTERVAL_SECONDS)
        update_interval = (
            timedelta(seconds=seconds) if seconds else DEFAULT_SCAN_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_status()
        except QManagerAuthError as err:
            raise UpdateFailed(f"Authentication with QManager failed: {err}") from err
        except QManagerConnectionError as err:
            raise UpdateFailed(f"Could not reach QManager: {err}") from err
