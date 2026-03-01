# Chandler Systems for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A [Home Assistant](https://www.home-assistant.io/) custom component for monitoring and controlling [Chandler Systems](https://www.chandlersystems.com/) Signature-series water treatment devices over Bluetooth Low Energy (BLE).

## Features

- **Fully local** — no cloud dependency; communicates directly with your device over BLE
- **Auto-discovery** — devices are automatically detected via BLE advertisements
- **Active polling** — establishes an active Bluetooth connection on a polling interval to send and receive data from the device
- **40+ sensors** — battery level, flow rates, water usage, regeneration status, salt levels, diagnostics, and more
- **7 binary sensors** — regeneration state, motor status, aeration mode, and others
- **Device-type aware** — entities are dynamically filtered based on your device type (softener, aeration filter, etc.)

## Supported Devices

Chandler Systems Signature-series water treatment devices, including:

- Metered and timeclock softeners
- Backwashing filters
- Aeration filters
- HydroxR, ReactR, and Ultra filters

Across valve series 2–6 (D12, D15, CS125, CS150, CS121).

## Requirements

- Home Assistant 2024.12 or newer
- A Bluetooth adapter accessible to Home Assistant (built-in, USB dongle, or ESPHome Bluetooth proxy)
- Your device's API key (UUID format, provided by Chandler Systems)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three-dot menu in the top right and select **Custom repositories**
3. Add this repository URL and select **Integration** as the category
4. Search for **Chandler Systems** and install it
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/hass_chandler_systems` directory into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Ensure Bluetooth is available in Home Assistant
2. Your device should be auto-discovered — look for a notification in **Settings > Devices & Services**
3. If not auto-discovered, click **Add Integration**, search for **Chandler Systems**, and enter your device's Bluetooth address manually
4. Enter your API key when prompted
5. The integration will connect, authenticate, and begin receiving data

## Sensors

### Dashboard

| Sensor | Unit | Description |
|--------|------|-------------|
| Battery Level | mV | Device battery voltage |
| Total Gallons Remaining | gal | Estimated gallons until regeneration |
| Peak Flow Daily | GPM | Highest flow rate recorded today |
| Water Hardness | gpg | Configured water hardness |
| Water Used Today | gal | Total water consumed today |
| Average Water Used | gal | Daily average water usage |
| Salt Tank Capacity | lbs | Total salt tank capacity |
| Salt Tank Remaining | lbs | Estimated salt remaining |

### Flow & Valve

| Sensor | Unit | Description |
|--------|------|-------------|
| Present Flow | GPM | Current water flow rate |
| Valve Status | — | Current valve position |
| Regeneration State | — | Current regeneration phase (idle, backwash, brine draw, etc.) |
| Valve Error | — | Error state if any (lost home, encoder error, motor timeout, etc.) |

### History & Diagnostics

| Sensor | Unit | Description |
|--------|------|-------------|
| Days in Operation | days | Total days the device has been running |
| Days Since Regeneration | days | Days since last regeneration cycle |
| Gallons Since Regeneration | gal | Water used since last regeneration |
| Regeneration Counter | — | Total regeneration cycles |
| Total Gallons | gal | Lifetime water usage |
| Serial Number | — | Device serial number |
| Firmware Version | — | Current firmware version |

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| Regeneration Active | Whether a regeneration cycle is in progress |
| Regeneration Motor in Progress | Whether the valve motor is currently running |
| Regeneration in Aeration | Whether the device is in aeration mode |
| Regeneration Soak Mode | Whether the device is in soak mode |
| Prefill Enabled | Whether prefill is enabled |
| Auto Reserve Mode | Whether auto reserve capacity is enabled |
| Display Off | Whether the device display is turned off |

## Troubleshooting

- **Device not discovered**: Ensure your Bluetooth adapter is working and the device is powered on and within range. ESPHome Bluetooth proxies can extend range.
- **Authentication failed**: Verify your API key is correct. It should be a UUID (32 hex characters, with or without dashes).
- **Frequent disconnections**: The integration connects on a polling interval, exchanges data, then disconnects. This is normal behavior — it will reconnect automatically on the next poll cycle.
- **Missing sensors**: Some sensors only appear for specific device types. Softener-specific sensors (salt, hardness, brine) won't appear for filter-only devices.

## Contributing

Contributions are welcome! Please open an issue or pull request on [GitHub](https://github.com/toekneestuck/hass_chandler_systems).

## License

See [LICENSE](LICENSE) for details.
