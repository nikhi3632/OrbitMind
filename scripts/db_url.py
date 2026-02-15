#!/usr/bin/env python3
"""Print database URL (for use with psql)."""

import os

from dotenv import load_dotenv

load_dotenv()

print(os.getenv("TIMESCALE_SERVICE_URL"))
