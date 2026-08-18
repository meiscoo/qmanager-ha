"""Binary sensor entities for QManager."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import QManagerConfigEntry
from .entity import QManagerEntity, get_path


@dataclass(frozen=True, kw_only=True)
class QManagerBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a QManager binary sensor and how to pull its value."""

    value_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[QManagerBinarySensorDescription, ...] = (
    QManagerBinarySensorDescription(
        key="internet_available",
        translation_key="internet_available",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda d: get_path(d, "connectivity", "internet_available"),
    ),
    QManagerBinarySensorDescription(
        key="modem_reachable",
        translation_key="modem_reachable",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("modem_reachable"),
    ),
    QManagerBinarySensorDescription(
        key="carrier_aggregation",
        translation_key="carrier_aggregation",
        value_fn=lambda d: get_path(d, "network", "ca_active"),
    ),
    QManagerBinarySensorDescription(
        key="sim_failover_active",
        translation_key="sim_failover_active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: get_path(d, "sim_failover", "active"),
    ),
    QManagerBinarySensorDescription(
        key="watchdog_enabled",
        translation_key="watchdog_enabled",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: get_path(d, "watchcat", "enabled"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up QManager binary sensors from a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        QManagerBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class QManagerBinarySensor(QManagerEntity, BinarySensorEntity):
    """A boolean value pulled from the QManager status poll."""

    entity_description: QManagerBinarySensorDescription

    def __init__(self, coordinator, description: QManagerBinarySensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._device_unique_id}_{description.key}"

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self._status())
