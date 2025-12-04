#!/usr/bin/env python
"""Demo showing MCP-like features: streaming, sessions, sampling, notifications."""

from toolable import Toolable, StreamEvent, SessionEvent, sample, notify, stream, session

app = Toolable(name="mcp-demo", help="Demo of MCP-like agent features")


# ============================================================================
# 1. NOTIFICATIONS - Working NOW (stderr output)
# ============================================================================

@app.command()
def process_with_notifications(items: int = 5):
    """Process items with progress notifications to stderr."""
    notify.log("Starting processing", level="info")

    for i in range(items):
        notify.progress(f"Processing item {i+1}/{items}", percent=int((i+1)/items * 100))
        # Simulate work
        import time
        time.sleep(0.1)

    notify.log("Processing complete", level="info")
    return {"processed": items, "status": "success"}


# ============================================================================
# 2. STREAMING - Needs Integration (Task 14)
# ============================================================================

@app.command()
def streaming_example(count: int = 3) -> stream:
    """Stream progress events as the task executes.

    NOTE: This will work once we integrate streaming detection in _agent_execute_json.
    Plan Task 14: Detect `-> stream` return type and route to run_streaming_tool()
    """
    # Emit progress events
    for i in range(count):
        yield StreamEvent.progress(f"Processing step {i+1}/{count}", percent=int((i+1)/count * 100))

    # Emit artifacts
    yield StreamEvent.artifact("result.json", "/tmp/result.json")

    # Emit final result
    yield StreamEvent.result({
        "status": "success",
        "result": {"steps": count, "completed": True}
    })


# ============================================================================
# 3. SESSION MODE - Needs Integration (Task 14)
# ============================================================================

@app.command()
def interactive_chat() -> session:
    """Bidirectional conversation with the agent.

    NOTE: This will work once we integrate session detection in _agent_execute_json.
    Plan Task 14: Detect `-> session` return type and route to run_session_tool()
    """
    # Start session
    yield SessionEvent.start("Chat session started. Ask me anything!")

    # Loop until user quits
    for _ in range(5):  # Max 5 exchanges for demo
        # Wait for input
        yield SessionEvent.awaiting("You: ")

        # Receive input via send()
        user_input = yield

        if user_input.get("action") == "quit":
            break

        message = user_input.get("message", "")
        # Echo back
        yield SessionEvent.awaiting(f"Bot: You said '{message}'\n")

    # End session
    yield SessionEvent.end("success")


# ============================================================================
# 4. SAMPLING - Working NOW (LLM callback)
# ============================================================================

@app.command()
def use_llm_sampling(prompt: str):
    """Call back to the LLM during execution.

    The agent framework provides LLM access via stdin or HTTP callback.
    """
    notify.log("Requesting LLM completion...", level="info")

    # Request completion from the calling agent
    response = sample(
        prompt=prompt,
        max_tokens=100,
        temperature=0.7
    )

    notify.log("LLM response received", level="info")

    return {
        "prompt": prompt,
        "response": response,
        "status": "success"
    }


if __name__ == "__main__":
    app()
