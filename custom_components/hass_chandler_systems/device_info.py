"""Device list helpers for the Chandler Systems integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    AERATION_ONLY_KEYS,
    DOMAIN,
    KEY_FIRMWARE_VERSION,
    KEY_SERIAL_A,
    KEY_SERIAL_B,
    KEY_VALVE_SERIES,
    KEY_VALVE_TYPE,
    SOFTENER_ONLY_KEYS,
    VALVE_SERIES_NAMES,
    VALVE_TYPE_NAMES,
)


def format_firmware_version(dlf: int) -> str:
    """Format a raw firmware integer as a version string (e.g. 613 → 'C6.13')."""
    return f"C{dlf // 100}.{dlf % 100:02d}"


def format_device_info(device_data: dict[str, Any]) -> DeviceInfo | None:
    """Return basic device info.

    This is used to populate the config flow's device info and the coordinator's data.
    """
    raw_type = device_data.get(KEY_VALVE_TYPE)
    raw_series = device_data.get(KEY_VALVE_SERIES)
    raw_serial_a = device_data.get(KEY_SERIAL_A) or 0
    raw_serial_b = device_data.get(KEY_SERIAL_B) or 0
    raw_firmware = device_data.get(KEY_FIRMWARE_VERSION)

    if raw_type is None:
        return None

    try:
        valve_type = VALVE_TYPE_NAMES.get(
            int(raw_type if raw_type is not None else -1), "Chandler Systems"
        )
        series = VALVE_SERIES_NAMES.get(
            int(raw_series if raw_series is not None else -1), "Unknown series"
        )
        firmware = (
            format_firmware_version(int(raw_firmware))
            if raw_firmware is not None
            else "Unknown firmware"
        )
        serial = f"{int(raw_serial_a):X}{int(raw_serial_b):X}"

        return DeviceInfo(
            {
                "identifiers": {(DOMAIN, serial)},
                "serial_number": serial,
                "manufacturer": "Chandler Systems",
                "model": valve_type,
                "name": valve_type,
                "sw_version": firmware,
                "hw_version": series,
            }
        )
    except (ValueError, TypeError):
        return None


def excluded_keys_for_valve_type(valve_type: int | None) -> frozenset[str]:
    """Return sensor/binary sensor keys to exclude for the given valve type.

    Returns an empty frozenset if the valve type is unknown (no filtering).
    """
    if valve_type is None:
        return frozenset()

    valve_name = VALVE_TYPE_NAMES.get(valve_type, "")
    excluded: set[str] = set()

    if not valve_name.endswith("Softener"):
        excluded |= SOFTENER_ONLY_KEYS

    if "Aeration" not in valve_name:
        excluded |= AERATION_ONLY_KEYS

    return frozenset(excluded)
