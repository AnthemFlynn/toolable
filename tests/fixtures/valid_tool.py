#!/usr/bin/env python
"""Valid test tool for registry tests."""
import json
import sys

if "--discover" in sys.argv:
    print(json.dumps({
        "name": "valid_tool",
        "version": "1.0.0",
        "tools": [{"name": "example", "summary": "Example tool", "streaming": False, "session_mode": False}],
        "resources": [],
        "prompts": []
    }))
    sys.exit(0)

print(json.dumps({"status": "success", "result": {"message": "ok"}}))
