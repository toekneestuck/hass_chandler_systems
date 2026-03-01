"""Config flow for the Chandler Systems integration."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowError
from homeassistant.helpers.device_registry import DeviceInfo

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

from .api import (
    ChandlerSystemsAPI,
    ChandlerSystemsAuthenticationError,
    ChandlerSystemsConnectionError,
)
from .const import CONF_AUTH_KEY, DOMAIN, MANUFACTURER_ID, SIGNATURE_SERVICE_UUID
from .device_info import format_device_info

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ADDRESS): str,
        vol.Required(CONF_AUTH_KEY): str,
    }
)


class ChandlerSystemsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Chandler Systems."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._device_info: DeviceInfo | None = None
        self._user_input: dict[str, Any] | None = None
        self._identify_task: asyncio.Task[None] | None = None
        super().__init__()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug("Bluetooth discovery: %s", discovery_info)

        # Check if this is a Chandler Systems device
        if (
            discovery_info.manufacturer_data.get(MANUFACTURER_ID) is not None
            or SIGNATURE_SERVICE_UUID in discovery_info.service_uuids
        ):
            await self.async_set_unique_id(discovery_info.address)
            self._abort_if_unique_id_configured()

            self._discovery_info = discovery_info
            self.context["title_placeholders"] = {
                "name": discovery_info.name or discovery_info.address,
                "address": discovery_info.address,
            }

            return await self.async_step_identify_device()

        return self.async_abort(reason="not_supported")

    async def async_step_identify_device(
        self, _user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Identify the device by connecting over BLE."""
        if not self._identify_task:
            self._identify_task = self.hass.async_create_task(
                self._async_identify_device()
            )

        if not self._identify_task.done():
            return self.async_show_progress(
                step_id="identify_device",
                progress_action="identify_device",
                progress_task=self._identify_task,
            )

        try:
            await self._identify_task
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Identify device task failed", exc_info=True)
        finally:
            self._identify_task = None

        next_step_id = "bluetooth_confirm" if self._discovery_info else "create_entry"
        return self.async_show_progress_done(next_step_id=next_step_id)

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        assert self._discovery_info is not None

        if self._device_info is not None:
            name = self._device_info.get("name") or self._discovery_info.name
            model = self._device_info.get("model") or self._discovery_info.name
        else:
            name = self._discovery_info.name or self._discovery_info.address
            model = self._discovery_info.name or self._discovery_info.address

        # First time showing the form
        if user_input is None:
            return self.async_show_form(
                step_id="bluetooth_confirm",
                data_schema=self.add_suggested_values_to_schema(
                    STEP_USER_DATA_SCHEMA,
                    {CONF_ADDRESS: self._discovery_info.address},
                ),
                description_placeholders={
                    "name": name,
                    "model": model,
                },
            )

        # Processing user input
        data = {**user_input, CONF_ADDRESS: self._discovery_info.address}
        errors: dict[str, str] = {}

        try:
            info = await self.validate_input(data)
        except ChandlerSystemsAuthenticationError as err:
            errors["base"] = err.translation_key or "invalid_auth"
        except FlowError as err:
            errors["base"] = err.translation_key or "connection_failed"

        if errors:
            return self.async_show_form(
                step_id="bluetooth_confirm",
                errors=errors,
                data_schema=self.add_suggested_values_to_schema(
                    STEP_USER_DATA_SCHEMA,
                    data,
                ),
                description_placeholders={
                    "name": name,
                    "model": model,
                },
            )

        # Everything is good, creating the entry
        title = (
            self._device_info.get("name") or info["title"]
            if self._device_info
            else info["title"]
        )
        return self.async_create_entry(title=title, data=data)

    async def validate_input(self, data: dict[str, Any]) -> dict[str, str]:
        """Validate the user input.

        Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
        The actual BLE connection is managed by the coordinator after setup; this step
        just ensures the address and auth key are present.
        """
        address: str = data[CONF_ADDRESS]
        if not data.get(CONF_AUTH_KEY) or data[CONF_AUTH_KEY] == "":
            raise FlowError(translation_key="invalid_key_format")

        ble_device: BLEDevice | None = None

        if self._discovery_info:
            address = self._discovery_info.address
            ble_device = self._discovery_info.device
        else:
            ble_device = async_ble_device_from_address(self.hass, address)

        if ble_device is None:
            raise FlowError("No BLE device found for the provided address")

        try:
            api = ChandlerSystemsAPI(self.hass, address)
            if await api.connect(ble_device):
                await api.authenticate(data[CONF_AUTH_KEY])
        except ChandlerSystemsConnectionError as err:
            raise FlowError(f"Connection to device failed: {err}") from err
        finally:
            await api.disconnect()

        return {"title": f"Chandler Systems ({address})"}

    async def async_step_create_entry(
        self, _user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create config entry after user flow identification."""
        assert self._user_input is not None

        address = self._user_input[CONF_ADDRESS]
        title = (
            self._device_info.get("name") or f"Chandler Systems ({address})"
            if self._device_info
            else f"Chandler Systems ({address})"
        )
        return self.async_create_entry(title=title, data=self._user_input)

    async def _async_identify_device(self) -> None:
        """Connect via BLE and retrieve device metadata.

        Stores the result in self._device_info. If the connection fails
        or the device is not reachable, self._device_info remains None
        and the next step will use fallback information.
        """
        ble_device: BLEDevice | None = None

        if self._discovery_info:
            address = self._discovery_info.address
            ble_device = self._discovery_info.device
        elif self._user_input:
            address = self._user_input[CONF_ADDRESS]
            ble_device = async_ble_device_from_address(self.hass, address)
        else:
            return

        if ble_device is None:
            _LOGGER.debug(
                "No BLE device found for %s, skipping identification", address
            )
            return

        try:
            api = ChandlerSystemsAPI(self.hass, address)
            await api.connect(ble_device)
            try:
                initial_data = await api.identify()
                self._device_info = format_device_info(initial_data)
            finally:
                await api.disconnect()
        except ChandlerSystemsConnectionError as err:
            _LOGGER.warning(
                "Could not connect for identification: %s",
                err,
            )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self.validate_input(user_input)
            except ChandlerSystemsAuthenticationError as err:
                errors["base"] = err.translation_key or "invalid_auth"
            except Exception as err:  # noqa: BLE001
                _LOGGER.error("Unexpected exception: %s", err)
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_ADDRESS])
                self._abort_if_unique_id_configured()

                self._user_input = user_input
                return await self.async_step_identify_device()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
