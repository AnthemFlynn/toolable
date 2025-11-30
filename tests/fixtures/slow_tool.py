#!/usr/bin/env python
"""Slow tool that times out during discovery."""
import time
import sys

if "--discover" in sys.argv:
    time.sleep(10)  # Longer than 5 second timeout
    print("{}")
    sys.exit(0)

print("{}")
