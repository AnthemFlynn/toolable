#!/usr/bin/env python
"""Test tool with prompt for registry tests."""
import sys
import json

if "--discover" in sys.argv:
    print(json.dumps({
        "name": "tool_with_prompt",
        "version": "1.0.0",
        "tools": [],
        "resources": [],
        "prompts": [{"name": "greet", "summary": "Greeting prompt", "arguments": {"name": "Name"}}]
    }))
    sys.exit(0)

if "--prompt" in sys.argv:
    prompt_name = sys.argv[sys.argv.index("--prompt") + 1]
    args_json = sys.argv[sys.argv.index("--prompt") + 2]
    args = json.loads(args_json)
    result = f"Hello {args.get('name', 'World')}!"
    print(json.dumps(result))
    sys.exit(0)

print(json.dumps({"status": "success", "result": {}}))
