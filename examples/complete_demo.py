#!/usr/bin/env python
"""Complete demo showing ALL Toolable features working together."""

from toolable import (
    StreamEvent,
    Toolable,
    notify,
    stream,
)

app = Toolable(
    name="complete-tool", help="Complete demo of Toolable: Typer + MCP features"
)


# ============================================================================
# 1. NORMAL COMMANDS - Just like Typer
# ============================================================================


@app.command()
def hello(name: str, excited: bool = False):
    """Say hello (works for humans and agents)."""
    greeting = f"Hello, {name}!"
    if excited:
        greeting += " 🎉"

    print(greeting)  # Human sees this
    return {"greeting": greeting, "name": name}  # Agent gets this


@app.command()
def calculate(a: float, b: float, operation: str = "add"):
    """Perform calculation with type hints."""
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else None,
    }

    result = operations.get(operation)
    if result is None:
        return {"error": "Invalid operation or division by zero"}

    return {"operation": operation, "a": a, "b": b, "result": result}


# ============================================================================
# 2. STREAMING - One-way event emission
# ============================================================================


@app.command()
def process_batch(items: int = 5, delay: float = 0.1) -> stream:
    """Process items with real-time streaming progress.

    Shows progress events as work happens.
    """
    import time

    # Emit progress as we work
    for i in range(items):
        yield StreamEvent.progress(
            f"Processing item {i+1}/{items}", percent=int((i + 1) / items * 100)
        )
        time.sleep(delay)

    # Emit artifacts
    yield StreamEvent.artifact("batch_results.json", "/tmp/batch_results.json")

    # Emit final result
    yield StreamEvent.result(
        {
            "status": "success",
            "result": {"processed": items, "time_taken": items * delay},
        }
    )


# ============================================================================
# 3. NOTIFICATIONS - Side-channel progress to stderr
# ============================================================================


@app.command()
def long_task(steps: int = 3):
    """Run task with notifications (separate from result)."""
    notify.log("Starting long task...", level="info")

    for i in range(steps):
        notify.progress(f"Step {i+1}/{steps}", percent=int((i + 1) / steps * 100))
        import time

        time.sleep(0.2)

    notify.log("Task completed successfully", level="info")

    return {"status": "success", "steps_completed": steps}


# ============================================================================
# 4. RESOURCES - Expose data endpoints
# ============================================================================


@app.resource(uri_pattern="/items/{item_id}", summary="Get item by ID")
def get_item(item_id: str):
    """Fetch item details."""
    # Mock database
    items = {
        "1": {"id": "1", "name": "Widget", "price": 9.99},
        "2": {"id": "2", "name": "Gadget", "price": 19.99},
    }
    return items.get(item_id, {"error": "Item not found"})


app.register_resource(get_item)


# ============================================================================
# 5. ERROR HANDLING - Structured errors
# ============================================================================


@app.command()
def divide(a: float, b: float):
    """Divide with proper error handling."""
    from toolable import ErrorCode, ToolError

    if b == 0:
        raise ToolError(
            ErrorCode.INVALID_INPUT,
            "Cannot divide by zero",
            suggestion="Use a non-zero divisor",
        )

    return {"result": a / b}


if __name__ == "__main__":
    app()
