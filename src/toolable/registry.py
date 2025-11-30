import subprocess
import json
from pathlib import Path
from typing import Any


class ToolRegistry:
    """Registry for discovering and calling external toolable executables."""

    def __init__(self, tool_paths: list[Path | str]):
        self.tools: dict[str, dict] = {}
        self.resources: dict[str, dict] = {}
        self.prompts: dict[str, dict] = {}

        for path in tool_paths:
            self._load_tool(Path(path))

    def _load_tool(self, path: Path) -> None:
        """Load manifest from a toolable executable."""
        if not path.exists():
            return

        try:
            result = subprocess.run(
                [str(path), "--discover"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                manifest = json.loads(result.stdout)

                for tool in manifest.get("tools", []):
                    tool["_path"] = path
                    self.tools[tool["name"]] = tool

                for resource in manifest.get("resources", []):
                    resource["_path"] = path
                    self.resources[resource["uri_pattern"]] = resource

                for prompt in manifest.get("prompts", []):
                    prompt["_path"] = path
                    self.prompts[prompt["name"]] = prompt

        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
            # Log error but continue loading other tools
            import warnings
            warnings.warn(f"Failed to load tool from {path}: {e}")

    def discover(self) -> dict[str, str]:
        """Return tool summaries for LLM context injection."""
        return {name: info["summary"] for name, info in self.tools.items()}

    def schema(self, name: str) -> dict:
        """Get full schema for a tool."""
        tool = self.tools.get(name)
        if not tool:
            raise KeyError(f"Unknown tool: {name}")

        path = tool["_path"]
        result = subprocess.run(
            [str(path), name, "--manifest"],
            capture_output=True,
            text=True,
        )

        return json.loads(result.stdout)

    def call(self, name: str, params: dict) -> dict:
        """Execute a tool and return response."""
        tool = self.tools.get(name)
        if not tool:
            return {"status": "error", "error": {"code": "NOT_FOUND", "message": f"Unknown tool: {name}", "recoverable": True}}

        path = tool["_path"]
        result = subprocess.run(
            [str(path), name, json.dumps(params)],
            capture_output=True,
            text=True,
        )

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL",
                    "message": f"Invalid response: {result.stdout}",
                    "recoverable": False,
                }
            }

    def fetch_resource(self, uri: str) -> dict:
        """Fetch a resource by URI."""
        import re

        for pattern, info in self.resources.items():
            regex = re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", pattern)
            if re.match(regex, uri):
                path = info["_path"]
                result = subprocess.run(
                    [str(path), "--resource", uri],
                    capture_output=True,
                    text=True,
                )
                return json.loads(result.stdout)

        return {"status": "error", "error": {"code": "NOT_FOUND", "message": f"No resource matches: {uri}", "recoverable": True}}

    def render_prompt(self, name: str, args: dict) -> dict:
        """Render a prompt."""
        prompt = self.prompts.get(name)
        if not prompt:
            return {"status": "error", "error": {"code": "NOT_FOUND", "message": f"Unknown prompt: {name}", "recoverable": True}}

        path = prompt["_path"]
        result = subprocess.run(
            [str(path), "--prompt", name, json.dumps(args)],
            capture_output=True,
            text=True,
        )

        return json.loads(result.stdout)
