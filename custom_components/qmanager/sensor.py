"""Sensor entities for QManager."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfInformation,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import QManagerConfigEntry
from .entity import QManagerEntity, get_path

SIGNAL_STRENGTH_DECIBELS = "dB"
SIGNAL_STRENGTH_DECIBELS_MILLIWATT = "dBm"


@dataclass(frozen=True, kw_only=True)
class QManagerSensorDescription(SensorEntityDescription):
    """Describes a QManager sensor and how to pull its value from status JSON."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSOR_DESCRIPTIONS: tuple[QManagerSensorDescription, ...] = (
    QManagerSensorDescription(
        key="network_type",
        translation_key="network_type",
        value_fn=lambda d: get_path(d, "network", "type"),
    ),
    QManagerSensorDescription(
        key="carrier",
        translation_key="carrier",
        value_fn=lambda d: get_path(d, "network", "carrier"),
    ),
    QManagerSensorDescription(
        key="service_status",
        translation_key="service_status",
        value_fn=lambda d: get_path(d, "network", "service_status"),
    ),
    QManagerSensorDescription(
        key="wan_ipv4",
        translation_key="wan_ipv4",
        entity_registry_enabled_default=False,
        value_fn=lambda d: get_path(d, "network", "wan_ipv4"),
    ),
    QManagerSensorDescription(
        key="lte_band",
        translation_key="lte_band",
        value_fn=lambda d: get_path(d, "lte", "band"),
    ),
    QManagerSensorDescription(
        key="lte_rsrp",
        translation_key="lte_rsrp",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "lte", "rsrp"),
    ),
    QManagerSensorDescription(
        key="lte_rsrq",
        translation_key="lte_rsrq",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "lte", "rsrq"),
    ),
    QManagerSensorDescription(
        key="lte_sinr",
        translation_key="lte_sinr",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "lte", "sinr"),
    ),
    QManagerSensorDescription(
        key="nr_band",
        translation_key="nr_band",
        value_fn=lambda d: get_path(d, "nr", "band"),
    ),
    QManagerSensorDescription(
        key="nr_rsrp",
        translation_key="nr_rsrp",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "nr", "rsrp"),
    ),
    QManagerSensorDescription(
        key="nr_rsrq",
        translation_key="nr_rsrq",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "nr", "rsrq"),
    ),
    QManagerSensorDescription(
        key="nr_sinr",
        translation_key="nr_sinr",
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "nr", "sinr"),
    ),
    QManagerSensorDescription(
        key="temperature",
        translation_key="temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "device", "temperature"),
    ),
    QManagerSensorDescription(
        key="cpu_usage",
        translation_key="cpu_usage",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: get_path(d, "device", "cpu_usage"),
    ),
    QManagerSensorDescription(
        key="memory_used",
        translation_key="memory_used",
        native_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: get_path(d, "device", "memory_used_mb"),
    ),
    QManagerSensorDescription(
        key="uptime",
        translation_key="uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: get_path(d, "device", "uptime_seconds"),
    ),
    QManagerSensorDescription(
        key="connection_uptime",
        translation_key="connection_uptime",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        value_fn=lambda d: get_path(d, "device", "conn_uptime_seconds"),
    ),
    QManagerSensorDescription(
        key="latency",
        translation_key="latency",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "connectivity", "latency_ms"),
    ),
    QManagerSensorDescription(
        key="packet_loss",
        translation_key="packet_loss",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: get_path(d, "connectivity", "packet_loss_pct"),
    ),
    QManagerSensorDescription(
        key="watchdog_state",
        translation_key="watchdog_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: get_path(d, "watchcat", "state"),
    ),
    QManagerSensorDescription(
        key="watchdog_recoveries",
        translation_key="watchdog_recoveries",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: get_path(d, "watchcat", "total_recoveries"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: QManagerConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up QManager sensors from a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        QManagerSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class QManagerSensor(QManagerEntity, SensorEntity):
    """A single value pulled from the QManager status poll."""

    entity_description: QManagerSensorDescription

    def __init__(
        self,
        coordinator,
        description: QManagerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{self._device_unique_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._status())
