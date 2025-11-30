import json
import os
import platform
import signal
import sys
import threading
from collections.abc import Callable
from typing import Any

from pydantic import ValidationError

from toolable.decorators import get_prompt_meta, get_resource_meta, get_tool_meta
from toolable.discovery import (
    extract_schema_from_function,
    generate_prompt_manifest,
    generate_resource_manifest,
    generate_tool_manifest,
)
from toolable.errors import ErrorCode, ToolError
from toolable.input import ToolInput
from toolable.response import Response
from toolable.sampling import configure_sampling
from toolable.session import run_session_tool
from toolable.streaming import run_streaming_tool


def _setup_timeout(timeout_seconds: int):
    """Setup timeout handling (cross-platform)."""
    if platform.system() == 'Windows':
        # On Windows, use threading.Timer
        def timeout_handler():
            print(json.dumps(Response.error("TIMEOUT", "Operation timed out", recoverable=False)), file=sys.stderr)
            os._exit(1)

        timer = threading.Timer(timeout_seconds, timeout_handler)
        timer.daemon = True
        timer.start()
        return timer
    else:
        # On Unix, use signal.alarm
        def timeout_handler(signum, frame):
            raise ToolError(ErrorCode.TIMEOUT, "Operation timed out")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        return None


class AgentCLI:
    def __init__(
        self,
        name: str | Callable,
        tools: list[Callable] | None = None,
        version: str = "0.1.0",
    ):
        # Support single-tool shorthand: AgentCLI(my_func).run()
        if callable(name):
            fn = name
            self.name = fn.__name__
            self._tools = {fn.__name__: fn}
        else:
            self.name = name
            self._tools = {}

        self._resources = {}
        self._prompts = {}
        self.version = version

        # Register initial tools
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, fn: Callable, name: str | None = None) -> None:
        """Register a tool."""
        tool_name = name or fn.__name__
        self._tools[tool_name] = fn

    def register_resource(self, fn: Callable) -> None:
        """Register a resource."""
        meta = get_resource_meta(fn)
        if not meta:
            raise ValueError(f"{fn.__name__} is not decorated with @resource")
        self._resources[meta["uri_pattern"]] = fn

    def register_prompt(self, fn: Callable) -> None:
        """Register a prompt."""
        self._prompts[fn.__name__] = fn

    def run(self) -> None:
        """Execute CLI based on arguments."""
        args = sys.argv[1:]

        if not args or "--help" in args and len(args) == 1:
            self._print_help()
            return

        # Global flags
        if "--discover" in args:
            self._print_discover()
            return
        if "--tools" in args:
            self._print_tools()
            return
        if "--resources" in args:
            self._print_resources()
            return
        if "--prompts" in args:
            self._print_prompts()
            return

        # Resource fetch
        if "--resource" in args:
            idx = args.index("--resource")
            if idx + 1 < len(args):
                self._fetch_resource(args[idx + 1])
            return

        # Prompt render
        if "--prompt" in args:
            idx = args.index("--prompt")
            if idx + 2 < len(args):
                self._render_prompt(args[idx + 1], args[idx + 2])
            return

        # Tool execution
        cmd = args[0]
        if cmd not in self._tools:
            # Single tool mode
            if len(self._tools) == 1:
                cmd = list(self._tools.keys())[0]
                tool_args = args
            else:
                print(json.dumps(Response.error("NOT_FOUND", f"Unknown command: {cmd}", recoverable=True)))
                return
        else:
            tool_args = args[1:]

        self._run_tool(cmd, tool_args)

    def _run_tool(self, name: str, args: list[str]) -> None:
        """Execute a tool."""
        fn = self._tools[name]
        meta = get_tool_meta(fn) or {}

        # Handle tool-specific flags
        if "--manifest" in args:
            manifest = generate_tool_manifest(fn, meta)
            print(json.dumps(manifest, indent=2))
            return

        if "--help" in args:
            self._print_tool_help(fn, meta)
            return

        # Parse input
        streaming = "--stream" in args
        session_mode = "--session" in args

        # Configure sampling if specified
        if "--sample-via" in args:
            idx = args.index("--sample-via")
            if idx + 1 < len(args):
                configure_sampling(args[idx + 1])

        # Extract JSON input or parse flags
        json_input = None
        for arg in args:
            if arg.startswith("{"):
                json_input = arg
                break

        if "--validate" in args:
            idx = args.index("--validate")
            if idx + 1 < len(args):
                json_input = args[idx + 1]
            result = self._validate_input(fn, meta, json_input or "{}")
            print(json.dumps(result))
            return

        # Build params
        try:
            params = self._parse_input(fn, meta, args, json_input)
        except ValidationError as e:
            print(json.dumps(Response.error(
                "INVALID_INPUT",
                str(e),
                recoverable=True
            )))
            return
        except json.JSONDecodeError as e:
            print(json.dumps(Response.error(
                "INVALID_INPUT",
                f"Invalid JSON: {e}",
                recoverable=True
            )))
            return

        # Handle reserved fields
        input_obj = params if isinstance(params, ToolInput) else None
        timeout_timer = None

        if input_obj:
            # Run pre_validate hook
            try:
                input_obj.pre_validate()
            except ToolError as e:
                print(json.dumps(e.to_response()))
                return

            # Handle working_dir
            try:
                if hasattr(input_obj, "working_dir") and input_obj.working_dir:
                    if not os.path.isdir(input_obj.working_dir):
                        raise ToolError(
                            ErrorCode.INVALID_PATH,
                            f"Directory not found: {input_obj.working_dir}",
                            recoverable=True
                        )
                    os.chdir(input_obj.working_dir)
            except ToolError as e:
                print(json.dumps(e.to_response()))
                return

            # Handle timeout
            try:
                if hasattr(input_obj, "timeout") and input_obj.timeout:
                    if input_obj.timeout <= 0:
                        raise ToolError(
                            ErrorCode.INVALID_INPUT,
                            "timeout must be positive",
                            recoverable=True
                        )
                    if input_obj.timeout > 600:  # 10 minutes max
                        raise ToolError(
                            ErrorCode.INVALID_INPUT,
                            "timeout exceeds maximum (600 seconds)",
                            recoverable=True
                        )
                    timeout_timer = _setup_timeout(input_obj.timeout)
            except ToolError as e:
                print(json.dumps(e.to_response()))
                return

            # Handle dry_run
            if hasattr(input_obj, "dry_run") and input_obj.dry_run:
                print(json.dumps(Response.success({
                    "dry_run": True,
                    "would_execute": input_obj.to_log_safe()
                })))
                return

        # Execute tool
        try:
            if meta.get("input_model"):
                result = fn(params)
            elif isinstance(params, dict):
                result = fn(**params)
            else:
                result = fn(params)

            # Handle different return types
            # Auto-detect streaming/session mode based on tool metadata
            if meta.get("streaming"):
                if not streaming:
                    raise ToolError(
                        ErrorCode.INVALID_INPUT,
                        "This tool requires --stream flag",
                        suggestion="Add --stream to the command",
                        recoverable=True
                    )
                run_streaming_tool(result)
            elif meta.get("session_mode"):
                if not session_mode:
                    raise ToolError(
                        ErrorCode.INVALID_INPUT,
                        "This tool requires --session flag",
                        suggestion="Add --session to the command",
                        recoverable=True
                    )
                final = run_session_tool(result)
                print(json.dumps(final))
            elif isinstance(result, dict):
                # Check if already a response envelope
                if "status" in result:
                    print(json.dumps(result))
                else:
                    print(json.dumps(Response.success(result)))
            else:
                print(json.dumps(Response.success({"result": result})))

        except ToolError as e:
            print(json.dumps(e.to_response()))
        except Exception as e:
            print(json.dumps(Response.error(
                "INTERNAL",
                str(e),
                recoverable=False
            )))
        finally:
            # Cleanup timeout timer on Windows
            if timeout_timer and platform.system() == 'Windows':
                timeout_timer.cancel()
            # Cancel alarm on Unix
            elif platform.system() != 'Windows':
                signal.alarm(0)

    def _parse_input(self, fn: Callable, meta: dict, args: list[str], json_input: str | None) -> Any:
        """Parse input from JSON or CLI flags."""
        input_model = meta.get("input_model")

        if json_input:
            data = json.loads(json_input)
            if input_model:
                return input_model(**data)
            return data

        # Parse CLI flags into dict
        data = {}
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--") and arg not in ("--stream", "--session", "--sample-via", "--manifest", "--help", "--validate"):
                key = arg[2:].replace("-", "_")
                if i + 1 < len(args) and not args[i + 1].startswith("--"):
                    value = args[i + 1]
                    # Try to parse as JSON for complex types
                    try:
                        data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        data[key] = value
                    i += 2
                else:
                    data[key] = True
                    i += 1
            else:
                i += 1

        if input_model:
            return input_model(**data)
        return data

    def _validate_input(self, fn: Callable, meta: dict, json_input: str) -> dict:
        """Validate input without executing."""
        try:
            data = json.loads(json_input)
            input_model = meta.get("input_model")

            if input_model:
                obj = input_model(**data)
                obj.pre_validate()

            return {"valid": True}
        except ValidationError as e:
            return {"valid": False, "errors": e.errors()}
        except ToolError as e:
            return {"valid": False, "errors": [{"code": e.code.value, "message": e.message}]}
        except Exception as e:
            return {"valid": False, "errors": [{"message": str(e)}]}

    def _print_discover(self) -> None:
        """Print full discovery output."""
        output = {
            "name": self.name,
            "version": self.version,
            "tools": [],
            "resources": [],
            "prompts": [],
        }

        for name, fn in self._tools.items():
            meta = get_tool_meta(fn) or {"summary": ""}
            output["tools"].append({
                "name": name,
                "summary": meta.get("summary", ""),
                "streaming": meta.get("streaming", False),
                "session_mode": meta.get("session_mode", False),
            })

        for pattern, fn in self._resources.items():
            meta = get_resource_meta(fn) or {}
            output["resources"].append(generate_resource_manifest(fn, meta))

        for name, fn in self._prompts.items():
            meta = get_prompt_meta(fn) or {}
            output["prompts"].append(generate_prompt_manifest(fn, meta))

        print(json.dumps(output, indent=2))

    def _print_tools(self) -> None:
        """Print tools only."""
        tools = []
        for name, fn in self._tools.items():
            meta = get_tool_meta(fn) or {}
            tools.append({"name": name, "summary": meta.get("summary", "")})
        print(json.dumps({"tools": tools}, indent=2))

    def _print_resources(self) -> None:
        """Print resources only."""
        resources = []
        for fn in self._resources.values():
            meta = get_resource_meta(fn) or {}
            resources.append(generate_resource_manifest(fn, meta))
        print(json.dumps({"resources": resources}, indent=2))

    def _print_prompts(self) -> None:
        """Print prompts only."""
        prompts = []
        for fn in self._prompts.values():
            meta = get_prompt_meta(fn) or {}
            prompts.append(generate_prompt_manifest(fn, meta))
        print(json.dumps({"prompts": prompts}, indent=2))

    def _fetch_resource(self, uri: str) -> None:
        """Fetch a resource by URI."""
        import re

        for pattern, fn in self._resources.items():
            # Convert pattern to regex with proper escaping
            # First, find all {placeholder} patterns
            placeholders = re.findall(r"\{(\w+)\}", pattern)
            # Replace placeholders with temporary markers
            temp_pattern = re.sub(r"\{(\w+)\}", "\x00\\1\x00", pattern)
            # Escape all literal regex characters
            escaped = re.escape(temp_pattern)
            # Replace markers with named groups
            regex_pattern = re.sub(r"\x00(\w+)\x00", r"(?P<\1>[^/]+)", escaped)
            # Use fullmatch to require exact match (no extra trailing content)
            match = re.fullmatch(regex_pattern, uri)

            if match:
                params = match.groupdict()
                try:
                    result = fn(**params)
                    print(json.dumps(result))
                except Exception as e:
                    print(json.dumps(Response.error("INTERNAL", str(e))))
                return

        print(json.dumps(Response.error("NOT_FOUND", f"No resource matches URI: {uri}", recoverable=True)))

    def _render_prompt(self, name: str, json_args: str) -> None:
        """Render a prompt."""
        if name not in self._prompts:
            print(json.dumps(Response.error("NOT_FOUND", f"Unknown prompt: {name}", recoverable=True)))
            return

        try:
            args = json.loads(json_args)
            fn = self._prompts[name]
            result = fn(**args)
            print(json.dumps(result))
        except Exception as e:
            print(json.dumps(Response.error("INTERNAL", str(e))))

    def _print_help(self) -> None:
        """Print human-readable help."""
        print(f"{self.name} v{self.version}")
        print()
        print("Usage:")
        print(f"  {self.name} --discover              Show all tools, resources, prompts")
        print(f"  {self.name} <command> --manifest    Show command schema")
        print(f"  {self.name} <command> '{{}}'          Execute with JSON input")
        print(f"  {self.name} <command> --flag value  Execute with CLI flags")
        print()
        print("Commands:")
        for name, fn in self._tools.items():
            meta = get_tool_meta(fn) or {}
            print(f"  {name:20} {meta.get('summary', '')}")

    def _print_tool_help(self, fn: Callable, meta: dict) -> None:
        """Print help for a specific tool."""
        print(f"{fn.__name__} - {meta.get('summary', '')}")
        print()
        if fn.__doc__:
            print(fn.__doc__)
            print()

        schema = extract_schema_from_function(fn, meta.get("input_model"))
        props = schema.get("properties", {})
        required = schema.get("required", [])

        if props:
            print("Parameters:")
            for name, prop in props.items():
                req = "*" if name in required else " "
                default = f" (default: {prop['default']})" if "default" in prop else ""
                desc = prop.get("description", "")
                print(f"  {req} --{name:15} {prop.get('type', 'string'):10} {desc}{default}")
