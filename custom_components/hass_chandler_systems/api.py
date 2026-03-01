"""API client for Chandler Systems Signature Bluetooth devices."""

# Based on documentation from
# https://github.com/ChandlerSystems/Signature-API-Guide/blob/main/readme.md

from __future__ import annotations

import asyncio
import binascii
from collections.abc import Callable
import json
import logging
import math
from typing import Any

from bleak import BleakError
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError

from .const import (
    HEADER_ACK,
    HEADER_FIRST_PACKET,
    HEADER_LAST_PACKET,
    HEADER_MARCO,
    HEADER_NAK,
    HEADER_NOP,
    HEADER_POLO,
    HEADER_SINGLE_PACKET,
    KEY_FIRMWARE_VERSION,
    MIN_DATA_PACKET_SIZE,
    PACKET_CRC_SIZE,
    PACKET_HEADER_SIZE,
    READ_CHARACTERISTIC_UUID,
    SIGNATURE_SERVICE_UUID,
    WRITE_CHARACTERISTIC_UUID,
)

_LOGGER = logging.getLogger(__name__)


class ChandlerSystemsAPIError(HomeAssistantError):
    """Exception raised for Chandler Systems API errors."""


class ChandlerSystemsConnectionError(ChandlerSystemsAPIError):
    """Exception raised for connection errors."""


class ChandlerSystemsAuthenticationError(ChandlerSystemsAPIError):
    """Exception raised for authentication errors."""


class ChandlerSystemsAPI:
    """API client for Chandler Systems Signature devices."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.address = address
        self.client: BleakClientWithServiceCache | None = None
        self._connected = False
        self._callbacks: list[Callable[[dict[str, Any]], None]] = []

        self._read_char: BleakGATTCharacteristic | None = None
        self._write_char: BleakGATTCharacteristic | None = None
        self._auth_key: str | None = None

        self._receive_buffer = bytearray()
        self._response_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        self._ack_event = asyncio.Event()
        self._nack_event = asyncio.Event()
        self._write_lock = asyncio.Lock()
        self.disconnect_event: asyncio.Event = asyncio.Event()

    async def connect(self, ble_device: BLEDevice) -> bool:
        """Connect to the Chandler Systems device."""
        try:
            self.client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                ble_device.name or ble_device.address,
                disconnected_callback=self._on_ble_disconnect,
            )
            self._connected = True

            # Find signature service and characteristics
            service = self.client.services.get_service(SIGNATURE_SERVICE_UUID)
            if not service:
                raise ChandlerSystemsConnectionError("Signature service not found")

            for char in service.characteristics:
                if char.uuid == READ_CHARACTERISTIC_UUID:
                    self._read_char = char
                elif char.uuid == WRITE_CHARACTERISTIC_UUID:
                    self._write_char = char

            if not self._read_char or not self._write_char:
                raise ChandlerSystemsConnectionError(
                    "Required characteristics not found"
                )

            _LOGGER.debug(
                "Found signature service with read char %s and write char %s",
                self._read_char.uuid,
                self._write_char.uuid,
            )
            # Subscribe to data sent by the device
            await self.client.start_notify(self._read_char, self._receive_handler)

            _LOGGER.info("Connected to Chandler Systems device %s", self.address)
        except BleakError as err:
            raise ChandlerSystemsConnectionError(f"Failed to connect: {err}") from err
        else:
            return True

    async def disconnect(self) -> None:
        """Disconnect from the device."""
        if self.client and self._connected:
            if self._write_lock.locked():
                _LOGGER.debug(
                    "Write lock is locked during disconnect, waiting for in-flight write to complete"
                )
            # Acquire the write lock to ensure any in-flight write completes
            # before tearing down the connection.
            async with self._write_lock:
                _LOGGER.debug("Sending graceful disconnect command to device")
                # Send reset command to prompt device to disconnect
                try:
                    await self._write_gatt(b"R", lock=False)
                except ChandlerSystemsConnectionError:
                    # Connection already dropped; skip the reset and proceed to cleanup.
                    _LOGGER.debug("Device already disconnected, skipping reset command")
                self._connected = False
                # Short delay to allow it to process the disconnect
                await asyncio.sleep(0.1)
                # disconnect the client
                await self.client.disconnect()
                _LOGGER.info(
                    "Disconnected from Chandler Systems device %s", self.address
                )

    async def identify(self, lock: bool = True) -> dict[str, Any]:
        """Send the ID packet and return the device's initial data response.

        Performs only the first half of the auth handshake — sends the ID status
        packet (0xEA), waits for the ACK, then waits for the initial data packet
        that contains device metadata (valve type, series, firmware version, serial
        numbers). The auth token is NOT sent, so no credentials are required.
        """
        try:
            self._clear_ack_nack()
            self._drain_response_queue()
            # Step 1: Send ID Status Packet (0xEA)
            _LOGGER.debug("Sending ID Status Packet (0xEA) for device identification")
            await self._write_gatt(b"\xea", lock=lock)
            # Step 2: Wait for ACK
            got_ack = await self._wait_for_ack(timeout=5)
            if not got_ack:
                raise ChandlerSystemsConnectionError(
                    "Device NAK'd the ID packet"
                    if got_ack is False
                    else "Timeout waiting for ACK after ID packet"
                )
            # Step 3: Wait for initial data response containing device metadata
            return await self._wait_for_response(timeout=5)
        except (BleakError, TimeoutError) as err:
            raise ChandlerSystemsConnectionError(
                f"Failed to identify device (device not responding?): {err}"
            ) from err

    async def authenticate(self, auth_key: str) -> bool:
        """Authenticate with the device."""
        self._auth_key = auth_key

        async with self._write_lock:
            try:
                # Steps 1-3: send ID packet and receive initial device data
                initial_data = await self.identify(lock=False)
                _LOGGER.debug("Received initial device data")

                # Step 4: validate and send auth token
                try:
                    # Convert UUID to bytes (remove dashes, decode hex)
                    token_bytes = bytes.fromhex(auth_key.replace("-", "").lower())
                except ValueError as err:
                    raise ChandlerSystemsAuthenticationError(
                        translation_key="invalid_key_format"
                    ) from err

                if (
                    "2D" in auth_key
                    and initial_data.get(KEY_FIRMWARE_VERSION, 0) <= 618
                ):
                    raise ChandlerSystemsAuthenticationError(
                        translation_key="bad_auth_key"
                    )

                if len(token_bytes) != 16:
                    raise ChandlerSystemsAuthenticationError(
                        f"Invalid auth key length, expected 16, got {len(token_bytes)} bytes"
                    )

                _LOGGER.debug("Sending Auth Token: %s", token_bytes.hex())
                self._drain_response_queue()
                await self._write_gatt(token_bytes, lock=False)

                # Step 5: wait for auth response (skip any non-auth data
                # the device may send before the auth status)
                _LOGGER.debug("Waiting for Auth Response")
                try:
                    auth_response = await self._wait_for_response(
                        predicate=lambda r: "as" in r,
                        timeout=10.0,
                    )
                    _LOGGER.debug("Received Auth Response: %s", auth_response)

                    # Check for failure: {"as": 2} means authorized
                    if auth_response.get("as") != 2:
                        _LOGGER.error(
                            "Authentication failed: Device reported unauthorized"
                        )
                        raise ConfigEntryAuthFailed("API key was rejected by device")

                    _LOGGER.info(
                        "Authentication successful for device %s", self.address
                    )
                except TimeoutError:
                    _LOGGER.warning("Timeout waiting for Auth Response")
                    return False
                else:
                    return True
            except BleakError as err:
                _LOGGER.error("Bluetooth error during authentication: %s", err)
                raise

    async def send_command(self, json_data: dict[str, Any]) -> dict[str, Any] | None:
        """Send a JSON command and wait for a JSON response."""
        if not self.client or not self._connected:
            raise ChandlerSystemsConnectionError(
                "Cannot send command to device, not connected"
            )

        self._drain_response_queue()
        # Send command (each chunk write is serialized by the write lock,
        # so this will wait for any in-flight ACK/NAK/POLO to finish first)
        await self._send_json(json_data)

        # Wait for response
        try:
            return await self._wait_for_response(timeout=10.0)
        except TimeoutError:
            _LOGGER.warning("Timeout waiting for response to command %s", json_data)
            return None

    def register_callback(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """Register a callback for notifications."""
        self._callbacks.append(fn)

    def unregister_callback(self, fn: Callable[[dict[str, Any]], None]) -> None:
        """Unregister a previously registered callback."""
        self._callbacks.remove(fn)

    def _drain_response_queue(self) -> None:
        """Discard any stale responses sitting in the queue."""
        while not self._response_queue.empty():
            self._response_queue.get_nowait()

    async def _wait_for_response(
        self,
        predicate: Callable[[dict[str, Any]], bool] | None = None,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        """Wait for a response from the queue, optionally matching a predicate.

        If predicate is None, returns the first response.
        If predicate is provided, skips non-matching responses until a match
        is found or timeout expires.
        """
        deadline = self.hass.loop.time() + timeout
        while True:
            remaining = deadline - self.hass.loop.time()
            if remaining <= 0:
                raise TimeoutError
            response = await asyncio.wait_for(
                self._response_queue.get(), timeout=remaining
            )
            if predicate is None or predicate(response):
                return response
            _LOGGER.debug(
                "Response did not match predicate, waiting for next: %s",
                response,
            )

    async def _send_json(self, json_data: dict[str, Any]) -> None:
        """Send JSON data to the device, handling chunking."""
        data_str = json.dumps(json_data, separators=(",", ":"))
        packet_bytes = data_str.encode("utf-8")
        packet_length = len(packet_bytes)

        # Calculate chunking
        # MTU should be retrieved from client, defaulting to 23 if not available
        mtu = self.client.mtu_size if self.client else 23
        # Max data per packet = MTU - Header(1) - CRC(2)
        max_payload_size = mtu - PACKET_HEADER_SIZE - PACKET_CRC_SIZE

        total_packets = math.ceil(packet_length / max_payload_size)

        _LOGGER.debug("Sending data across %d packets: %s", total_packets, json_data)

        for i in range(total_packets):
            start = i * max_payload_size
            end = min(start + max_payload_size, packet_length)
            chunk = packet_bytes[start:end]

            # Determine header
            if total_packets == 1:
                header = HEADER_SINGLE_PACKET
            elif i == 0:
                header = HEADER_FIRST_PACKET
            elif i == total_packets - 1:
                header = HEADER_LAST_PACKET
            else:
                header = HEADER_NOP

            await self._send_packet_chunk(header, chunk)

    async def _send_packet_chunk(self, header: int, data: bytes) -> None:
        """Send a single packet chunk and wait for ACK."""
        # Build packet: Header + Data + CRC
        packet = bytearray()
        packet.append(header)
        packet.extend(data)

        # Calculate CRC
        crc = self._calculate_crc16(packet)
        packet.extend(crc.to_bytes(2, "big"))

        # Send (serialized by write lock inside _write_gatt)
        _LOGGER.debug(
            "Sending chunk: Header=0x%02X, Len=%d, pkt=%s, raw=%s",
            header,
            len(data),
            packet.hex(),
            packet,
        )
        self._clear_ack_nack()
        await self._write_gatt(bytes(packet))

        # Wait for ACK or NAK
        got_ack = await self._wait_for_ack(timeout=10)
        if got_ack is None:
            _LOGGER.warning("Timeout waiting for ACK for chunk, header 0x%02X", header)
        elif not got_ack:
            _LOGGER.warning("Received NAK for chunk, header 0x%02X", header)

    def _receive_handler(
        self, _characteristic: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        """Handle incoming notifications by scheduling async processing."""
        self.hass.async_create_background_task(
            self._async_handle_notification(data),
            f"chandler_systems_notify_{self.address}",
        )

    async def _async_handle_notification(self, data: bytearray) -> None:
        """Process an incoming BLE notification."""
        try:
            await self._handle_packet(data)
        except BleakError as err:
            _LOGGER.error("Error handling packet: %s", err)

    async def _handle_packet(self, data: bytearray) -> None:
        """Handle a received packet.

        This is async so that protocol responses (ACK/NAK/POLO) are
        awaited inline under the write lock, guaranteeing they are sent
        before any command that a callback might trigger.
        """
        if not data:
            return

        header = data[0]

        # Handle Status Packets (1 byte)
        if len(data) == 1:
            if header == HEADER_ACK:
                self._ack_event.set()
                _LOGGER.debug("[receive_handler] Received ACK from device")
                return
            if header == HEADER_NAK:
                self._nack_event.set()
                _LOGGER.warning("[receive_handler] Received NAK from device")
                return
            if header == HEADER_MARCO:
                _LOGGER.debug("[receive_handler] got MARCO, sending POLO")
                await self._send_status_packet(HEADER_POLO)
                return
            if header == HEADER_POLO:
                return

            _LOGGER.debug(
                "[receive_handler] Received unknown status packet: 0x%02X", header
            )
            return

        # Handle Data Packets
        if len(data) < MIN_DATA_PACKET_SIZE:
            _LOGGER.warning(
                "[receive_handler] Received packet too small: %d bytes", len(data)
            )
            return

        # Verify CRC
        payload_with_header = data[:-PACKET_CRC_SIZE]
        received_crc = int.from_bytes(data[-PACKET_CRC_SIZE:], "little")

        if not self._verify_crc(received_crc, payload_with_header):
            _LOGGER.warning("[receive_handler] CRC mismatch on received packet")
            await self._send_status_packet(HEADER_NAK)
            return

        # Process Payload
        payload = data[PACKET_HEADER_SIZE:-PACKET_CRC_SIZE]

        # Check chunking bits
        is_first = (header & HEADER_FIRST_PACKET) != 0
        is_last = (header & HEADER_LAST_PACKET) != 0

        if is_first:
            self._receive_buffer.clear()

        self._receive_buffer.extend(payload)

        json_data = None
        if is_last:
            try:
                json_str = self._receive_buffer.decode("utf-8")
                _LOGGER.debug("[receive_handler] decoded JSON: %s", json_str)
                json_data = json.loads(json_str)

                self._response_queue.put_nowait(json_data)
            except json.JSONDecodeError:
                _LOGGER.error("[receive_handler] Failed to decode JSON response")
            finally:
                self._receive_buffer.clear()

        # Send ACK before notifying callbacks so the device gets a timely
        # acknowledgement and any commands triggered by callbacks are
        # serialized after the ACK via the write lock.
        _LOGGER.debug(
            "[receive_handler] sending ACK for %s packet of payload",
            "single" if is_first and is_last else "last" if is_last else "intermediate",
        )
        await self._send_status_packet(HEADER_ACK)

        # Notify callbacks only after ACK has been sent
        if json_data is not None:
            for fn in self._callbacks:
                fn(json_data)

    async def _wait_for_ack(self, timeout: float) -> bool | None:
        """Wait for ACK or NAK from the device.

        Returns True if ACK received, False if NAK received, None on timeout.
        """
        ack_task = self.hass.async_create_task(self._ack_event.wait())
        nack_task = self.hass.async_create_task(self._nack_event.wait())

        done, pending = await asyncio.wait(
            {ack_task, nack_task},
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        if not done:
            return None
        return ack_task in done

    async def _write_gatt(self, data: bytes, lock: bool = True) -> None:
        """Write data to the device, serialized by the write lock."""
        if not self.client or not self._write_char or not self._connected:
            raise ChandlerSystemsConnectionError("Not connected to device")

        try:
            if lock:
                async with self._write_lock:
                    await self.client.write_gatt_char(
                        self._write_char, data, response=False
                    )
            else:
                await self.client.write_gatt_char(
                    self._write_char, data, response=False
                )
        except BleakError as err:
            raise ChandlerSystemsConnectionError(
                f"Write failed, device may have disconnected: {err}"
            ) from err

    async def _send_status_packet(self, status: int) -> None:
        """Send a single-byte status packet, suppressing errors."""
        if not self.client or not self._connected:
            _LOGGER.debug("Disconnected, skipping send of status packet 0x%02X", status)
            return

        try:
            await self._write_gatt(bytes([status]))
        except (ChandlerSystemsConnectionError, BleakError) as err:
            _LOGGER.error("Failed to send status packet 0x%02X: %s", status, err)
            raise

    @callback
    def _on_ble_disconnect(self, _client: BleakClientWithServiceCache) -> None:
        """Handle a BLE disconnection (expected or unexpected).

        Called by Bleak on the event loop when the connection drops from
        either side. Sets disconnect_event to unblock the coordinator's wait
        loop immediately rather than waiting for the idle timeout.
        """
        if not self._connected:
            # Already marked disconnected (e.g. our own disconnect() ran first).
            return
        _LOGGER.info("BLE connection to %s dropped", self.address)
        self._connected = False
        self.disconnect_event.set()

    def _clear_ack_nack(self) -> None:
        """Clear ACK and NAK events."""
        self._ack_event.clear()
        self._nack_event.clear()

    def _calculate_crc16(self, data: bytes | bytearray, seed: int = 0xFFFF) -> int:
        """Calculate CRC-16 checksum using CRC-16-CCITT algorithm."""
        return binascii.crc_hqx(data, seed)

    def _verify_crc(
        self, received_crc: int, data: bytes | bytearray, seed: int = 0xFFFF
    ) -> bool:
        """Verify a received CRC-16 against computed value and check residue."""
        computed_crc = self._calculate_crc16(data, seed)

        if received_crc != computed_crc:
            _LOGGER.debug(
                "Invalid CRC [Expected: 0x%04X (%d)] [Actual: 0x%04X (%d)]",
                received_crc,
                received_crc,
                computed_crc,
                computed_crc,
            )
            return False

        buffer_with_crc = data + bytes([received_crc >> 8 & 0xFF, received_crc & 0xFF])
        return self._calculate_crc16(buffer_with_crc, seed) == 0x0000

    @property
    def connected(self) -> bool:
        """Return connection status."""
        return self._connected
