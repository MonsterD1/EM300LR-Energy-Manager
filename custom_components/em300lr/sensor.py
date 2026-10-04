"""Sensors for the EM300 LR.

Names are chosen so that entity_ids match the former template sensors
(sensor.bcontrolem300_<name>), keeping history and statistics.
Only grid import/export power and energy are enabled by default.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactiveEnergy,
    UnitOfReactivePower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN, MANUFACTURER, MODEL
from .coordinator import EM300ConfigEntry, EM300Coordinator

ENABLED_BY_DEFAULT = {
    "1-0:1.4.0*255",
    "1-0:1.8.0*255",
    "1-0:2.4.0*255",
    "1-0:2.8.0*255",
}

POWER = (SensorDeviceClass.POWER, UnitOfPower.WATT, SensorStateClass.MEASUREMENT)
ENERGY = (
    SensorDeviceClass.ENERGY,
    UnitOfEnergy.WATT_HOUR,
    SensorStateClass.TOTAL_INCREASING,
)
R_POWER = (
    SensorDeviceClass.REACTIVE_POWER,
    UnitOfReactivePower.VOLT_AMPERE_REACTIVE,
    SensorStateClass.MEASUREMENT,
)
R_ENERGY = (
    SensorDeviceClass.REACTIVE_ENERGY,
    UnitOfReactiveEnergy.VOLT_AMPERE_REACTIVE_HOUR,
    SensorStateClass.TOTAL_INCREASING,
)
A_POWER = (
    SensorDeviceClass.APPARENT_POWER,
    UnitOfApparentPower.VOLT_AMPERE,
    SensorStateClass.MEASUREMENT,
)
A_ENERGY = (None, "VAh", SensorStateClass.TOTAL_INCREASING)
PF = (SensorDeviceClass.POWER_FACTOR, None, SensorStateClass.MEASUREMENT)
FREQ = (
    SensorDeviceClass.FREQUENCY,
    UnitOfFrequency.HERTZ,
    SensorStateClass.MEASUREMENT,
)
CURRENT = (
    SensorDeviceClass.CURRENT,
    UnitOfElectricCurrent.AMPERE,
    SensorStateClass.MEASUREMENT,
)
VOLTAGE = (
    SensorDeviceClass.VOLTAGE,
    UnitOfElectricPotential.VOLT,
    SensorStateClass.MEASUREMENT,
)

# OBIS channel offset within a block -> (name, power kind, energy kind)
_FLOW_CHANNELS = {
    1: ("Active", POWER, ENERGY),
    3: ("Reactive", R_POWER, R_ENERGY),
    9: ("Apparent", A_POWER, A_ENERGY),
}


@dataclass(frozen=True, kw_only=True)
class EM300SensorDescription(SensorEntityDescription):
    """Description keyed by OBIS code."""


def _desc(obis: str, name: str, kind: tuple) -> EM300SensorDescription:
    device_class, unit, state_class = kind
    return EM300SensorDescription(
        key=obis,
        name=name,
        device_class=device_class,
        native_unit_of_measurement=unit,
        state_class=state_class,
        entity_registry_enabled_default=obis in ENABLED_BY_DEFAULT,
    )


def _build_descriptions() -> list[EM300SensorDescription]:
    descs: list[EM300SensorDescription] = []
    # block 0 = total, 20/40/60 = L1/L2/L3
    for base, prefix in ((0, ""), (20, "L1 "), (40, "L2 "), (60, "L3 ")):
        for offset, (label, p_kind, e_kind) in _FLOW_CHANNELS.items():
            for direction, step in (("Plus", 0), ("Minus", 1)):
                ch = base + offset + step
                descs.append(
                    _desc(
                        f"1-0:{ch}.4.0*255",
                        f"{prefix}{label} Power {direction}",
                        p_kind,
                    )
                )
                descs.append(
                    _desc(
                        f"1-0:{ch}.8.0*255",
                        f"{prefix}{label} Energy {direction}",
                        e_kind,
                    )
                )
        if base == 0:
            descs.append(_desc("1-0:13.4.0*255", "Power Factor", PF))
            descs.append(_desc("1-0:14.4.0*255", "Frequency", FREQ))
        else:
            descs.append(_desc(f"1-0:{base + 11}.4.0*255", f"{prefix}Current", CURRENT))
            descs.append(_desc(f"1-0:{base + 12}.4.0*255", f"{prefix}Voltage", VOLTAGE))
            descs.append(_desc(f"1-0:{base + 13}.4.0*255", f"{prefix}Power Factor", PF))
    return descs


SENSORS = _build_descriptions()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EM300ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create one entity per OBIS value the device reports."""
    coordinator = entry.runtime_data
    async_add_entities(
        EM300Sensor(coordinator, desc)
        for desc in SENSORS
        if desc.key in coordinator.data
    )


class EM300Sensor(CoordinatorEntity[EM300Coordinator], SensorEntity):
    """One OBIS value."""

    _attr_has_entity_name = True
    entity_description: EM300SensorDescription

    def __init__(
        self, coordinator: EM300Coordinator, description: EM300SensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        serial = coordinator.client.serial
        self._attr_unique_id = f"{serial}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=DEFAULT_NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=serial,
            sw_version=coordinator.client.app_version,
            configuration_url=f"http://{coordinator.config_entry.data['host']}",
        )

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.entity_description.key)
        return float(value) if isinstance(value, (int, float)) else None
