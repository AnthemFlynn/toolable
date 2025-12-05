#!/usr/bin/env python
"""Demo tool showing Toolable features for both humans and AI agents."""

from toolable import Toolable

app = Toolable(name="demo-tool", help="Demo tool with human CLI and agent features")


@app.command()
def greet(name: str, enthusiastic: bool = False):
    """Greet someone by name.

    Args:
        name: The person's name
        enthusiastic: Add extra excitement
    """
    greeting = f"Hello, {name}!"
    if enthusiastic:
        greeting += " 🎉"

    print(greeting)
    # Return dict for agent mode
    return {"greeting": greeting, "name": name}


@app.command()
def calculate(operation: str, a: float, b: float):
    """Perform a mathematical operation.

    Args:
        operation: One of: add, subtract, multiply, divide
        a: First number
        b: Second number
    """
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else None,
    }

    result = operations.get(operation)
    if result is None:
        return {"error": f"Invalid operation: {operation}"}

    print(f"{a} {operation} {b} = {result}")
    return {"operation": operation, "a": a, "b": b, "result": result}


@app.resource(uri_pattern="/users/{user_id}", summary="Get user information")
def get_user(user_id: str):
    """Fetch user details by ID."""
    # Mock data
    users = {
        "1": {"id": "1", "name": "Alice", "role": "admin"},
        "2": {"id": "2", "name": "Bob", "role": "user"},
    }
    return users.get(user_id, {"error": "User not found"})


# Register the resource
app.register_resource(get_user)


if __name__ == "__main__":
    app()
