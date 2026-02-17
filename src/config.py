"""OrbitMind configuration."""

# Lightstreamer
LIGHTSTREAMER_SERVER = "https://push.lightstreamer.com"
LIGHTSTREAMER_ADAPTER = "ISSLIVE"

# Telemetry channels to collect (only actively streaming channels)
CHANNELS = [
    # CMG system (ML target: torque prediction)
    "USLAB000006",  # CMG torque roll (N-m)
    "USLAB000007",  # CMG torque pitch (N-m)
    "USLAB000008",  # CMG torque yaw (N-m)
    "USLAB000009",  # CMG angular momentum
    "USLAB000010",  # CMG momentum %
    # Attitude
    "USLAB000019", "USLAB000020", "USLAB000021",  # Attitude rates/quaternion
    "USLAB000022", "USLAB000023", "USLAB000024",
    "USLAB000025", "USLAB000026", "USLAB000027",
    # SARJ angles
    "S0000003", "S0000004", "S0000005",
    "S0000002",
    # BGA angles
    "S4000007", "S4000008", "S6000007", "S6000008",
    "P4000007", "P4000008", "P6000007", "P6000008",
    # Orbital
    "USLAB000032", "USLAB000033", "USLAB000034",  # Position
    "USLAB000035", "USLAB000036", "USLAB000037",  # Velocity
    "USLAB000038",  # Orbital altitude/range
    # Radiator / truss thermal
    "P1000002", "S1000002",  # Radiator data
    "P1000003", "S1000003",  # Radiator data
    "P1000004", "S1000004",  # Radiator temps
    "P1000005", "S1000005",  # Radiator temps
    "P1000001", "S1000001",  # Radiator data
    # Thermal
    "USLAB000056",  # Coolant water low temp %
    "USLAB000059",  # Cabin temperature
    "USLAB000060",  # Avionics cooling temp
    "NODE2000006",  # Node 2 air cooling temp
    "NODE3000012",  # Node 3 avionics cooling temp
    "NODE3000013",  # Node 3 air cooling temp
    # Z1 truss
    "Z1000014", "Z1000015",
    # Time
    "TIME_000001",  # GMT
]

# Collector settings
DB_BATCH_SIZE = 100
DB_FLUSH_INTERVAL = 5.0
STALE_CONNECTION_TIMEOUT = 60.0  # Reconnect if no data for this many seconds
