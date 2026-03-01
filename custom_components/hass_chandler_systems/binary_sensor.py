"""Binary sensor platform for the Chandler Systems integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    KEY_AUTO_RESERVE_MODE,
    KEY_DISPLAY_OFF,
    KEY_PREFILL_ENABLED,
    KEY_REGEN_ACTIVE,
    KEY_REGEN_IN_AERATION,
    KEY_REGEN_MOTOR_IN_PROGRESS,
    KEY_REGEN_SOAK_MODE,
    KEY_VALVE_TYPE,
)
from .coordinator import ChandlerSystemsConfigEntry, ChandlerSystemsCoordinator
from .device_info import excluded_keys_for_valve_type
from .entity import ChandlerSystemsEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True)
class ChandlerSystemsBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Chandler Systems binary sensor."""


BINARY_SENSOR_DESCRIPTIONS: tuple[ChandlerSystemsBinarySensorEntityDescription, ...] = (
    # Dashboard binary sensors
    ChandlerSystemsBinarySensorEntityDescription(
        key=KEY_REGEN_IN_AERATION,
        translation_key="regen_in_aeration",
    ),
    ChandlerSystemsBinarySensorEntityDescription(
        key=KEY_REGEN_SOAK_MODE,
        translation_key="regen_soak_mode",
    ),
    ChandlerSystemsBinarySensorEntityDescription(
        key=KEY_PREFILL_ENABLED,
        translation_key="prefill_enabled",
    ),
    # Global binary sensors
    ChandlerSystemsBinarySensorEntityDescription(
        key=KEY_REGEN_ACTIVE,
        translation_key="regen_active",
    ),
    # Device list binary sensors
    ChandlerSystemsBinarySensorEntityDescription(
        key=KEY_REGEN_MOTOR_IN_PROGRESS,
        translation_key="regen_motor_in_progress",
    ),
    # Advanced settings binary sensors
    ChandlerSystemsBinarySensorEntityDescription(
        key=KEY_AUTO_RESERVE_MODE,
        translation_key="auto_reserve_mode",
    ),
    ChandlerSystemsBinarySensorEntityDescription(
        key=KEY_DISPLAY_OFF,
        translation_key="display_off",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChandlerSystemsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Chandler Systems binary sensors from a config entry."""
    coordinator = entry.runtime_data
    excluded = excluded_keys_for_valve_type(coordinator.data.get(KEY_VALVE_TYPE))
    async_add_entities(
        ChandlerSystemsBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
        if description.key not in excluded
    )


class ChandlerSystemsBinarySensor(ChandlerSystemsEntity, BinarySensorEntity):
    """Binary sensor entity for a Chandler Systems device."""

    entity_description: ChandlerSystemsBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: ChandlerSystemsCoordinator,
        description: ChandlerSystemsBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}-{description.key}"

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device info for the sensor."""
        return self.coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        raw = self.coordinator.data.get(self.entity_description.key)
        if raw is None:
            return None
        return bool(raw)
