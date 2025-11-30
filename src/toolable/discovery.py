import inspect
from typing import Any, Callable, get_type_hints
from pydantic import Field
from pydantic.fields import FieldInfo


def extract_schema_from_function(fn: Callable, input_model=None) -> dict:
    """Extract JSON schema from function signature or input model."""
    if input_model:
        return input_model.model_json_schema()

    hints = get_type_hints(fn)
    sig = inspect.signature(fn)

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls", "input"):
            continue

        prop = {"type": _python_type_to_json(hints.get(name, str))}

        # Extract Field metadata if present
        if isinstance(param.default, FieldInfo):
            field: FieldInfo = param.default
            if field.description:
                prop["description"] = field.description
            if field.default is not None:
                prop["default"] = field.default
        elif param.default is not inspect.Parameter.empty:
            prop["default"] = param.default
        else:
            required.append(name)

        properties[name] = prop

    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required

    return schema


def _python_type_to_json(py_type) -> str:
    """Map Python types to JSON schema types."""
    origin = getattr(py_type, "__origin__", None)

    if origin is list:
        return "array"
    if origin is dict:
        return "object"

    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    return mapping.get(py_type, "string")


def generate_tool_manifest(fn: Callable, meta: dict) -> dict:
    """Generate full manifest for a tool."""
    schema = extract_schema_from_function(fn, meta.get("input_model"))

    manifest = {
        "name": fn.__name__,
        "summary": meta["summary"],
        "description": inspect.getdoc(fn) or "",
        "streaming": meta.get("streaming", False),
        "session_mode": meta.get("session_mode", False),
        "schema": schema,
    }

    if meta.get("examples"):
        manifest["examples"] = meta["examples"]
    if meta.get("tags"):
        manifest["tags"] = meta["tags"]

    return manifest


def generate_resource_manifest(fn: Callable, meta: dict) -> dict:
    """Generate manifest for a resource."""
    return {
        "uri_pattern": meta["uri_pattern"],
        "summary": meta["summary"],
        "mime_types": meta.get("mime_types", []),
        "tags": meta.get("tags", []),
    }


def generate_prompt_manifest(fn: Callable, meta: dict) -> dict:
    """Generate manifest for a prompt."""
    return {
        "name": fn.__name__,
        "summary": meta["summary"],
        "arguments": meta["arguments"],
        "tags": meta.get("tags", []),
    }
