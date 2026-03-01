"""The Chandler Systems integration."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_AUTH_KEY
from .coordinator import ChandlerSystemsConfigEntry, ChandlerSystemsCoordinator

_LOGGER = logging.getLogger(__name__)

_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, entry: ChandlerSystemsConfigEntry
) -> bool:
    """Set up Chandler Systems from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    auth_key: str = entry.data[CONF_AUTH_KEY]

    coordinator = ChandlerSystemsCoordinator(
        hass=hass,
        logger=_LOGGER,
        address=address,
        auth_key=auth_key,
        config_entry=entry,
    )
    entry.runtime_data = coordinator

    # Start listening for BLE advertisements; unsubscribes on entry unload
    entry.async_on_unload(coordinator.async_start())

    if not await coordinator.async_wait_ready():
        raise ConfigEntryNotReady(
            f"Timed out waiting for Chandler Systems device {address} to become ready"
        )

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ChandlerSystemsConfigEntry
) -> bool:
    """Unload a config entry."""
    coordinator: ChandlerSystemsCoordinator = entry.runtime_data
    await coordinator.async_disconnect()
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
