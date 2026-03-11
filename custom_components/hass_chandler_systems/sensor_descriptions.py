"""Sensor entity descriptions for the Chandler Systems integration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfMass,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)

from .const import (
    KEY_AERATION_DAYS,
    KEY_AVG_WATER_USED,
    KEY_BATTERY_LEVEL,
    KEY_BRINE_TANK_FILL_HEIGHT,
    KEY_BRINE_TANK_REFILL_TIME,
    KEY_BRINE_TANK_REMAINING_SALT,
    KEY_BRINE_TANK_SALT_CAPACITY,
    KEY_BRINE_TANK_WIDTH,
    KEY_CHLORINE_PULSES,
    KEY_CURRENT_DAY_OVERRIDE,
    KEY_DAY_OVERRIDE,
    KEY_DAYS_IN_OPERATION,
    KEY_DAYS_SINCE_REGEN,
    KEY_DAYS_UNTIL_REGEN,
    KEY_FIRMWARE_VERSION,
    KEY_GALLONS_SINCE_REGEN,
    KEY_NUM_REGEN_POSITIONS,
    KEY_PEAK_FLOW_DAILY,
    KEY_PREFILL_DURATION,
    KEY_PRESENT_FLOW,
    KEY_REGEN_COUNTER,
    KEY_REGEN_COUNTER_RESETTABLE,
    KEY_REGEN_CURRENT_POSITION,
    KEY_REGEN_DAY_OVERRIDE,
    KEY_REGEN_SOAK_TIMER,
    KEY_REGEN_STATE,
    KEY_REGEN_TIME_HOURS,
    KEY_REGEN_TIME_REMAINING,
    KEY_REGEN_TIME_TYPE,
    KEY_RESERVE_CAPACITY,
    KEY_RESERVE_CAPACITY_GALLONS,
    KEY_SERIAL_A,
    KEY_SERIAL_B,
    KEY_TOTAL_GALLONS,
    KEY_TOTAL_GALLONS_REMAINING,
    KEY_TOTAL_GALLONS_RESETTABLE,
    KEY_TOTAL_GRAINS_CAPACITY,
    KEY_VALVE_ERROR,
    KEY_VALVE_SERIES,
    KEY_VALVE_STATUS,
    KEY_VALVE_TYPE,
    KEY_WATER_HARDNESS,
    KEY_WATER_USED_TODAY,
)


def divide_by_100(value: Any) -> Any:
    """Divide a raw value by 100 for display."""
    try:
        return round(float(value) / 100, 2)
    except (ValueError, TypeError):
        return value


def divide_by_10_int(value: Any) -> Any:
    """Divide a raw value by 10 for display."""
    try:
        return round(float(value) / 10)
    except (ValueError, TypeError):
        return value


_REGEN_STATE_STATES: dict[int, str] = {
    0: "idle",
    1: "moving_to_next_position",
    2: "moving_to_final_position",
    3: "twedo_waiting_for_motor",
    4: "waiting_for_twedo",
    5: "waiting_in_position",
    6: "moving_to_service",
    7: "moving_to_bypass",
    8: "in_bypass",
    9: "moving_to_brine_soak",
    10: "waiting_in_brine_soak",
    11: "moving_to_creep_position",
    12: "creeping_to_position",
}


def _map_regen_state(value: Any) -> str | None:
    """Map a raw regeneration state integer to its string state."""
    try:
        return _REGEN_STATE_STATES.get(int(value))
    except (ValueError, TypeError):
        return None


_REGEN_TIME_TYPES: dict[int, str] = {
    0: "seconds",
    1: "minutes",
    2: "salt_pounds",
}


def _map_regen_time_type(value: Any) -> str | None:
    """Map a raw regeneration time type integer to its string state."""
    try:
        return _REGEN_TIME_TYPES.get(int(value))
    except (ValueError, TypeError):
        return None


_VALVE_ERROR_STATES: dict[int, str] = {
    0: "no_error",
    2: "lost_home",
    3: "no_encoder_normal_current",
    4: "cannot_find_home",
    5: "no_encoder_high_current",
    6: "no_encoder_no_current",
    7: "twedo_motor_timeout",
    192: "regen_aborted_on_battery",
}


def _map_valve_error(value: Any) -> str | None:
    """Map a raw valve error integer to its string state."""
    try:
        return _VALVE_ERROR_STATES.get(int(value))
    except (ValueError, TypeError):
        return None


VALUE_TRANSFORMS: dict[str, Callable[[Any], Any]] = {
    KEY_PRESENT_FLOW: divide_by_100,
    KEY_PEAK_FLOW_DAILY: divide_by_100,
    KEY_GALLONS_SINCE_REGEN: divide_by_100,
    KEY_TOTAL_GALLONS: divide_by_100,
    KEY_AVG_WATER_USED: divide_by_100,
    KEY_WATER_USED_TODAY: divide_by_100,
    KEY_TOTAL_GALLONS_REMAINING: divide_by_100,
    KEY_TOTAL_GALLONS_RESETTABLE: divide_by_100,
    KEY_REGEN_STATE: _map_regen_state,
    KEY_REGEN_TIME_TYPE: _map_regen_time_type,
    KEY_VALVE_ERROR: _map_valve_error,
    KEY_BRINE_TANK_REMAINING_SALT: divide_by_10_int,
}

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # Dashboard sensors
    SensorEntityDescription(
        key=KEY_BATTERY_LEVEL,
        translation_key="battery_level",
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_TOTAL_GALLONS_REMAINING,
        translation_key="total_gallons_remaining",
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_PEAK_FLOW_DAILY,
        translation_key="peak_flow_daily",
        native_unit_of_measurement=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_WATER_HARDNESS,
        translation_key="water_hardness",
        native_unit_of_measurement="gpg",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_WATER_USED_TODAY,
        translation_key="water_used_today",
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key=KEY_AVG_WATER_USED,
        translation_key="avg_water_used",
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_TIME_HOURS,
        translation_key="regen_time_hours",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_SOAK_TIMER,
        translation_key="regen_soak_timer",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Brine tank sensors.
    SensorEntityDescription(
        key=KEY_BRINE_TANK_WIDTH,
        translation_key="brine_tank_width",
        native_unit_of_measurement=UnitOfLength.INCHES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_BRINE_TANK_FILL_HEIGHT,
        translation_key="brine_tank_fill_height",
        native_unit_of_measurement=UnitOfLength.INCHES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_BRINE_TANK_REFILL_TIME,
        translation_key="brine_tank_refill_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_BRINE_TANK_SALT_CAPACITY,
        translation_key="brine_tank_salt_capacity",
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_BRINE_TANK_REMAINING_SALT,
        translation_key="brine_tank_remaining_salt",
        native_unit_of_measurement=UnitOfMass.POUNDS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_DAY_OVERRIDE,
        translation_key="day_override",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_CURRENT_DAY_OVERRIDE,
        translation_key="current_day_override",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_TIME_TYPE,
        translation_key="regen_time_type",
        device_class=SensorDeviceClass.ENUM,
        options=list(_REGEN_TIME_TYPES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_TIME_REMAINING,
        translation_key="regen_time_remaining",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_CURRENT_POSITION,
        translation_key="regen_current_position",
    ),
    SensorEntityDescription(
        key=KEY_PREFILL_DURATION,
        translation_key="prefill_duration",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Global sensors
    SensorEntityDescription(
        key=KEY_VALVE_STATUS,
        translation_key="valve_status",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_PRESENT_FLOW,
        translation_key="present_flow",
        native_unit_of_measurement=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_STATE,
        translation_key="regen_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(_REGEN_STATE_STATES.values()),
    ),
    SensorEntityDescription(
        key=KEY_VALVE_ERROR,
        translation_key="valve_error",
        device_class=SensorDeviceClass.ENUM,
        options=list(_VALVE_ERROR_STATES.values()),
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Status/history sensors
    SensorEntityDescription(
        key=KEY_DAYS_IN_OPERATION,
        translation_key="days_in_operation",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_DAYS_SINCE_REGEN,
        translation_key="days_since_regen",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_GALLONS_SINCE_REGEN,
        translation_key="gallons_since_regen",
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_COUNTER,
        translation_key="regen_counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_COUNTER_RESETTABLE,
        translation_key="regen_counter_resettable",
        state_class=SensorStateClass.TOTAL,
    ),
    SensorEntityDescription(
        key=KEY_TOTAL_GALLONS,
        translation_key="total_gallons",
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_TOTAL_GALLONS_RESETTABLE,
        translation_key="total_gallons_resettable",
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.TOTAL,
    ),
    # Device list / diagnostic sensors
    SensorEntityDescription(
        key=KEY_SERIAL_A,
        translation_key="serial_a",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=KEY_SERIAL_B,
        translation_key="serial_b",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=KEY_FIRMWARE_VERSION,
        translation_key="firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=KEY_VALVE_TYPE,
        translation_key="valve_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=KEY_VALVE_SERIES,
        translation_key="valve_series",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    # Advanced settings sensors
    SensorEntityDescription(
        key=KEY_DAYS_UNTIL_REGEN,
        translation_key="days_until_regen",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_REGEN_DAY_OVERRIDE,
        translation_key="regen_day_override",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_RESERVE_CAPACITY,
        translation_key="reserve_capacity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_RESERVE_CAPACITY_GALLONS,
        translation_key="reserve_capacity_gallons",
        native_unit_of_measurement=UnitOfVolume.GALLONS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_TOTAL_GRAINS_CAPACITY,
        translation_key="total_grains_capacity",
        native_unit_of_measurement="gpg",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=KEY_AERATION_DAYS,
        translation_key="aeration_days",
        native_unit_of_measurement=UnitOfTime.DAYS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_CHLORINE_PULSES,
        translation_key="chlorine_pulses",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=KEY_NUM_REGEN_POSITIONS,
        translation_key="num_regen_positions",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)
