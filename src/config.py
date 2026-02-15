"""OrbitMind configuration."""

# Lightstreamer
LIGHTSTREAMER_SERVER = "https://push.lightstreamer.com"
LIGHTSTREAMER_ADAPTER = "ISSLIVE"

# Telemetry channels to collect
CHANNELS = [
    # Drive currents (targets)
    "S4000002", "S4000005", "S6000002", "S6000005",
    "P4000002", "P4000005", "P6000002", "P6000005",
    # SARJ angles
    "S0000003", "S0000004",
    # BGA angles
    "S4000007", "S4000008", "S6000007", "S6000008",
    "P4000007", "P4000008", "P6000007", "P6000008",
    # Orbital
    "USLAB000040",  # Solar beta angle
    "USLAB000032", "USLAB000033", "USLAB000034",  # Position
    "USLAB000035", "USLAB000036", "USLAB000037",  # Velocity
    "USLAB000010",  # CMG momentum
    "TIME_000001",  # GMT
]

# Collector settings
DB_BATCH_SIZE = 100
DB_FLUSH_INTERVAL = 5.0
