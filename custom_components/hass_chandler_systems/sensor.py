"""Sensor platform for the Chandler Systems integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .const import KEY_VALVE_TYPE
from .coordinator import ChandlerSystemsConfigEntry, ChandlerSystemsCoordinator
from .device_info import excluded_keys_for_valve_type
from .entity import ChandlerSystemsEntity
from .sensor_descriptions import SENSOR_DESCRIPTIONS, VALUE_TRANSFORMS

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChandlerSystemsConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Chandler Systems sensors from a config entry."""
    coordinator = entry.runtime_data
    excluded = excluded_keys_for_valve_type(coordinator.data.get(KEY_VALVE_TYPE))
    async_add_entities(
        ChandlerSystemsSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
        if description.key not in excluded
    )


class ChandlerSystemsSensor(ChandlerSystemsEntity, SensorEntity):
    """Sensor entity for a Chandler Systems device."""

    def __init__(
        self,
        coordinator: ChandlerSystemsCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}-{description.key}"
        self._previous_value: StateType = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.entity_description.state_class == SensorStateClass.TOTAL:
            current_value = self.native_value
            if current_value is not None:
                if current_value == 0 and self._previous_value != 0:
                    self._attr_last_reset = dt_util.utcnow()
                self._previous_value = current_value
        super()._handle_coordinator_update()

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device info for the sensor."""
        return self.coordinator.device_info

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        if not self.coordinator.data:
            return None
        raw = self.coordinator.data.get(self.entity_description.key)
        if raw is None:
            return None
        transform = VALUE_TRANSFORMS.get(self.entity_description.key)
        if transform:
            return transform(raw)
        return raw
