"""Base entity for the Chandler Systems integration."""

from __future__ import annotations

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.core import callback

from .coordinator import ChandlerSystemsCoordinator


class ChandlerSystemsEntity(
    PassiveBluetoothCoordinatorEntity[ChandlerSystemsCoordinator]
):
    """Base entity for Chandler Systems devices."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ChandlerSystemsCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

    @property
    def available(self) -> bool:
        """Return True if the entity is available."""
        return super().available and self.coordinator.last_connection_successful

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
