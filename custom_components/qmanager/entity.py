"""Shared base entity for QManager platforms."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import QManagerDataUpdateCoordinator


class QManagerEntity(CoordinatorEntity[QManagerDataUpdateCoordinator]):
    """Base entity tying every QManager entity to one modem device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: QManagerDataUpdateCoordinator) -> None:
        super().__init__(coordinator)
        device = (coordinator.data or {}).get("device", {})
        unique_id = coordinator.config_entry.unique_id or coordinator.config_entry.entry_id
        self._device_unique_id = unique_id

        self._attr_device_info = DeviceInfo(
            identifiers={("qmanager", unique_id)},
            name=coordinator.config_entry.title,
            manufacturer=device.get("manufacturer", "Quectel"),
            model=device.get("model"),
            sw_version=device.get("firmware"),
            serial_number=device.get("imei"),
            configuration_url=self._configuration_url(),
        )

    def _configuration_url(self) -> str | None:
        entry = self.coordinator.config_entry
        scheme = "https" if entry.data.get("ssl") else "http"
        return f"{scheme}://{entry.data['host']}:{entry.data['port']}"

    def _status(self) -> dict:
        return self.coordinator.data or {}


def get_path(data: dict, *keys: str):
    """Walk a nested dict, returning None if any key is missing."""
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
