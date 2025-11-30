#!/usr/bin/env python
"""Broken test tool that returns invalid JSON."""

import sys

if "--discover" in sys.argv:
    print("not valid json {")
    sys.exit(0)

print("{}")
