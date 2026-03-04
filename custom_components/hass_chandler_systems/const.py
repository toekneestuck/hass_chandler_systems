"""Constants for the Chandler Systems integration."""

DOMAIN = "chandler_systems"

# Bluetooth constants
MANUFACTURER_ID = 1850
SIGNATURE_SERVICE_UUID = "a725458c-bee1-4d2e-9555-edf5a8082303"
READ_CHARACTERISTIC_UUID = "a725458c-bee2-4d2e-9555-edf5a8082303"
WRITE_CHARACTERISTIC_UUID = "a725458c-bee3-4d2e-9555-edf5a8082303"

# Packet headers
HEADER_FIRST_PACKET = 0x80
HEADER_LAST_PACKET = 0x40
HEADER_KEEP_ALIVE = 0x20
HEADER_KEEP_ALIVE_TYPE = 0x10
HEADER_ACK_NAK = 0x08
HEADER_ACK_NAK_TYPE = 0x04
HEADER_TIMEOUT = 0x02
HEADER_TIMEOUT_TYPE = 0x01
HEADER_NOP = 0x00

# Derived headers
HEADER_SINGLE_PACKET = HEADER_FIRST_PACKET | HEADER_LAST_PACKET  # 0xC0
HEADER_ACK = HEADER_SINGLE_PACKET | HEADER_ACK_NAK | HEADER_ACK_NAK_TYPE  # 0xCC
HEADER_NAK = HEADER_SINGLE_PACKET | HEADER_ACK_NAK  # 0xC8
HEADER_MARCO = HEADER_SINGLE_PACKET | HEADER_KEEP_ALIVE  # 0xE0
HEADER_POLO = HEADER_SINGLE_PACKET | HEADER_KEEP_ALIVE | HEADER_KEEP_ALIVE_TYPE  # 0xF0

PACKET_HEADER_SIZE = 1
PACKET_CRC_SIZE = 2
MIN_DATA_PACKET_SIZE = PACKET_HEADER_SIZE + PACKET_CRC_SIZE + 2  # +2 for empty JSON {}

# Configuration constants
CONF_AUTH_KEY = "auth_key"

# Startup timeout — seconds to wait for initial data after BLE connection
DEVICE_STARTUP_TIMEOUT = 30

# Minimum amount of seconds to wait before attempting to connect to the device again
MIN_POLL_DURATION = 60

# Idle disconnect timeout — seconds with no push data before disconnecting
IDLE_DISCONNECT_TIMEOUT = 10

# Maximum connection duration — absolute cap on how long a poll connection stays open
MAX_CONNECTION_TIMEOUT = 3600

# API access key:
#   W = Write-Only (device pushes to app, read-only from HA's perspective)
#   R = Read-Only (app sends to device, command from HA's perspective)
#   RW = Read/Write (bidirectional)

# Dashboard data keys (prefix: d)
KEY_TIME_HOURS = "dh"  # Hours (military time) — RW
KEY_TIME_MINUTES = "dm"  # Minutes — RW
KEY_TIME_SECONDS = "ds"  # Seconds — RW
KEY_BATTERY_LEVEL = "dbl"  # mV — W
KEY_TOTAL_GALLONS_REMAINING = "dtgr"  # Gallons — W
KEY_PEAK_FLOW_DAILY = "dpfd"  # GPM — W
KEY_WATER_HARDNESS = "dwh"  # GPG (0-99) — RW
KEY_DAY_OVERRIDE = "ddo"  # Days (0-29) — RW
KEY_CURRENT_DAY_OVERRIDE = "dcdo"  # Days (0-29) — RW
KEY_WATER_USED_TODAY = "dwu"  # Gallons — W
KEY_AVG_WATER_USED = "dwau"  # Gallons — W
KEY_REGEN_TIME_HOURS = "drth"  # Hours (military time, 0-23) — RW
KEY_REGEN_TIME_TYPE = "drtt"  # 0-2 — W
KEY_REGEN_TIME_REMAINING = "drtr"  # Remaining regen step time — W
KEY_REGEN_CURRENT_POSITION = "drcp"  # Current regen position — W
KEY_REGEN_IN_AERATION = "dria"  # Boolean (0-1) — W
KEY_REGEN_SOAK_MODE = "dps"  # Boolean (0-1), in brine soak — W
KEY_REGEN_SOAK_TIMER = "drst"  # Minutes remaining in brine soak — W
KEY_PREFILL_ENABLED = "dpe"  # Boolean (0-1) — RW
KEY_PREFILL_DURATION = "dpd"  # Hours (1-4) — RW

# Brine tank data keys.
KEY_BRINE_TANK_WIDTH = "dbtw"  # Inches, brine tank width (diameter) - RW
KEY_BRINE_TANK_FILL_HEIGHT = "dbth"  # Inches, brine tank fill height - RW
KEY_BRINE_TANK_REFILL_TIME = "dbrt"  # Minutes, brine tank refill time - R
KEY_BRINE_TANK_SALT_CAPACITY = "dbts"  # Pounds, brine tank capacity - R
KEY_BRINE_TANK_REMAINING_SALT = "dbtr"  # Pounds, brine left in tank - RW

# Global data keys (prefix: g)
KEY_VALVE_STATUS = "gvs"  # Bit flags — W
KEY_VALVE_ERROR = "gve"  # Error code: 0-7, 192 — W
KEY_PRESENT_FLOW = "gpf"  # Hundredths of GPM (divide by 100) — W
KEY_REGEN_ACTIVE = "gra"  # Boolean — W
KEY_REGEN_STATE = "grs"  # Regeneration phase: 0-12 — W
KEY_REGEN_NOW = "grn"  # Boolean, trigger immediate regen — R
KEY_REGEN_LATER = "grl"  # Boolean, trigger regen at next scheduled time — R
KEY_FIND_HOME = "gfh"  # Boolean, tell valve to find home position — R

# Graph data keys (prefix: g)
# Values are in hundredths — divide by 100
KEY_GRAPH_PEAK_FLOW = "grp"  # GPM per day — W
KEY_GRAPH_GALLONS_DAILY = "ggd"  # Gallons per day — W
KEY_GRAPH_GALLONS_BETWEEN_REGENS = "ggr"  # Gallons between regens — W

# Status/history keys (prefix: sh)
KEY_DAYS_IN_OPERATION = "shdo"  # Days — W
KEY_DAYS_SINCE_REGEN = "shdr"  # Days — W
KEY_GALLONS_SINCE_REGEN = "shgs"  # Hundredths of gallons (divide by 100) — W
KEY_REGEN_COUNTER = "shrc"  # Count (total) — W
KEY_REGEN_COUNTER_RESETTABLE = "shrr"  # Count (resettable) — RW
KEY_TOTAL_GALLONS = "shgt"  # Hundredths of gallons (divide by 100) — W
KEY_TOTAL_GALLONS_RESETTABLE = "shgr"  # Hundredths of gallons (divide by 100) — RW
KEY_ERROR_LOG = "shel"  # Last 20 errors (JSON array) — W

# Device list keys (prefix: dl)
KEY_SERIAL_A = "dlsa"  # First half of serial number — W
KEY_SERIAL_B = "dlsb"  # Second half of serial number — W
KEY_FIRMWARE_VERSION = "dlf"  # Firmware version — W
KEY_VALVE_TYPE = "dlvt"  # Valve type: 1-27 — W
KEY_VALVE_SERIES = "dlvs"  # Valve series: 2-6 — W
KEY_REGEN_MOTOR_IN_PROGRESS = "dlr"  # Boolean (0-1), motor moving to regen position — W

# Advanced settings keys (prefix: as)
KEY_DAYS_UNTIL_REGEN = "asd"  # Days until next regen — W
KEY_REGEN_DAY_OVERRIDE = "asr"  # Max days between regens — RW
KEY_AUTO_RESERVE_MODE = "asar"  # Boolean, auto reserve mode — RW
KEY_RESERVE_CAPACITY = "asrc"  # Gallons, current reserve capacity — RW
KEY_RESERVE_CAPACITY_GALLONS = "asrg"  # Gallons, total reserve capacity — W
KEY_TOTAL_GRAINS_CAPACITY = "astg"  # GPG, total grains capacity — RW
KEY_AERATION_DAYS = "asad"  # Days — RW
KEY_CHLORINE_PULSES = "ascp"  # Number of chlorine pulses — RW
KEY_DISPLAY_OFF = "asdo"  # Boolean, display off — RW
KEY_NUM_REGEN_POSITIONS = "asnp"  # Total regen positions — W
KEY_CYCLE_POSITION_TIMES = "aspt"  # Cycle position times — RW

# Valve type lookup — maps dlvt integer to a product category string
VALVE_TYPE_NAMES: dict[int, str] = {
    1: "Metered Softener",
    2: "Timeclock Softener",
    3: "Metered Softener",
    4: "Backwashing Filter",
    5: "Backwashing Filter",
    6: "HydroxR Filter",
    7: "ReactR Filter",
    8: "Ultra Filter",
    9: "Aeration Filter",
    10: "Aeration Filter",
    11: "Aeration Filter",
    12: "Aeration Filter",
    13: "Aeration Filter",
    14: "Aeration Filter",
    15: "Aeration Filter",
    16: "Aeration Filter",
    17: "Metered Softener",
    18: "Backwashing Filter",
    19: "Metered Softener",
    20: "Backwashing Filter",
    21: "Metered Softener",
    22: "Backwashing Filter",
    23: "Aeration Filter",
    24: "Aeration Filter",
    25: "Aeration Filter",
    26: "Backwashing Filter",
    27: "Backwashing Filter",
}

# Valve series lookup — maps dlvs integer to the valve body model name
VALVE_SERIES_NAMES: dict[int, str] = {
    2: "Series 2, D12 Body",
    3: "Series 3, D15 Body",
    4: "Series 4, CS125 Body",
    5: "Series 5, CS150 Body",
    6: "Series 6, CS121 Body",
}

# Keys exclusive to softener valve types (brine, salt, soak, hardness, reserve)
SOFTENER_ONLY_KEYS: frozenset[str] = frozenset(
    {
        KEY_TOTAL_GALLONS_REMAINING,
        KEY_WATER_HARDNESS,
        KEY_REGEN_SOAK_TIMER,
        KEY_BRINE_TANK_WIDTH,
        KEY_BRINE_TANK_FILL_HEIGHT,
        KEY_BRINE_TANK_REFILL_TIME,
        KEY_BRINE_TANK_SALT_CAPACITY,
        KEY_BRINE_TANK_REMAINING_SALT,
        KEY_PREFILL_DURATION,
        KEY_RESERVE_CAPACITY,
        KEY_RESERVE_CAPACITY_GALLONS,
        KEY_TOTAL_GRAINS_CAPACITY,
        KEY_REGEN_SOAK_MODE,
        KEY_PREFILL_ENABLED,
        KEY_AUTO_RESERVE_MODE,
    }
)

# Keys exclusive to aeration valve types
AERATION_ONLY_KEYS: frozenset[str] = frozenset(
    {
        KEY_AERATION_DAYS,
        KEY_CHLORINE_PULSES,
        KEY_REGEN_IN_AERATION,
    }
)
