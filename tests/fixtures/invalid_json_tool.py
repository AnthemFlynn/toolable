#!/usr/bin/env python
"""Test tool that returns invalid JSON for registry tests."""

import json
import sys

if "--discover" in sys.argv:
    print(
        json.dumps(
            {
                "name": "invalid_json_tool",
                "version": "1.0.0",
                "tools": [
                    {
                        "name": "bad_json",
                        "summary": "Returns invalid JSON",
                        "streaming": False,
                        "session_mode": False,
                    }
                ],
                "resources": [],
                "prompts": [],
            }
        )
    )
    sys.exit(0)

# Return invalid JSON (not a dict)
print("This is not valid JSON {[]}}")
