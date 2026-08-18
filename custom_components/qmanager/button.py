"""Button entities for QManager."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import QManagerConfigEntry
from .entity import QManagerEntity

_LOGGER = logging.getLogger(__name__)

CELL_SCAN_DESCRIPTION = ButtonEntityDescription(
    key="start_cell_scan",
    translation_key="start_cell_scan",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up QManager buttons from a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities([QManagerCellScanButton(coordinator)])


class QManagerCellScanButton(QManagerEntity, ButtonEntity):
    """Triggers the QManager cell scanner daemon."""

    entity_description = CELL_SCAN_DESCRIPTION

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._device_unique_id}_start_cell_scan"

    async def async_press(self) -> None:
        await self.coordinator.api.async_start_cell_scan()
