#!/usr/bin/env python
"""Test tool with resource for registry tests."""

import json
import sys

if "--discover" in sys.argv:
    print(
        json.dumps(
            {
                "name": "tool_with_resource",
                "version": "1.0.0",
                "tools": [],
                "resources": [{"uri_pattern": "/files/{id}", "summary": "Get file"}],
                "prompts": [],
            }
        )
    )
    sys.exit(0)

if "--resource" in sys.argv:
    uri = sys.argv[sys.argv.index("--resource") + 1]
    # Extract ID from URI
    file_id = uri.split("/")[-1]
    print(json.dumps({"id": file_id, "content": f"Content of {file_id}"}))
    sys.exit(0)

print(json.dumps({"status": "success", "result": {}}))
