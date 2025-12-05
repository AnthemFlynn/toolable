# agent Features Status

## ✅ Fully Working (No Integration Needed)

### 1. **Notifications** (`notify`)
**Status:** ✅ Working
**Location:** `src/toolable/notifications.py`

Emits progress/logs/artifacts to **stderr** (separate from stdout JSON responses).

```python
from toolable import notify

notify.progress("Processing...", percent=50)
notify.log("Important message", level="info")
notify.artifact("output.json", "/path/to/file")
```

**Output (stderr):**
```json
{"type": "notification", "kind": "progress", "message": "Processing...", "percent": 50}
{"type": "notification", "kind": "log", "level": "info", "message": "Important message"}
{"type": "notification", "kind": "artifact", "name": "output.json", "uri": "/path/to/file"}
```

---

## 🔄 Needs Integration (Task 14)

### 2. **Streaming** (`stream`, `StreamEvent`)
**Status:** 🔄 Code exists, needs agent execution integration
**Location:** `src/toolable/streaming.py`
**Blocker:** `_agent_execute_json()` doesn't detect `-> stream` return type

**What it does:** One-way event emission (progress → logs → artifacts → final result)

```python
from toolable import stream, StreamEvent

@app.command()
def process() -> stream:
    """Streaming tool."""
    yield StreamEvent.progress("Step 1/3", percent=33)
    yield StreamEvent.progress("Step 2/3", percent=66)
    yield StreamEvent.artifact("result.json", "/tmp/result.json")
    yield StreamEvent.result({"status": "success", "result": {"done": True}})
```

**Expected output (jsonlines):**
```json
{"type": "progress", "message": "Step 1/3", "percent": 33}
{"type": "progress", "message": "Step 2/3", "percent": 66}
{"type": "artifact", "name": "result.json", "uri": "/tmp/result.json"}
{"type": "result", "status": "success", "result": {"done": true}}
```

**Integration needed:**
- Detect `-> stream` in `_agent_execute_json()`
- Call `run_streaming_tool(result)` instead of wrapping in Response
- Update discovery to detect streaming commands

---

### 3. **Session Mode** (`session`, `SessionEvent`)
**Status:** 🔄 Code exists, needs agent execution integration
**Location:** `src/toolable/session.py`
**Blocker:** `_agent_execute_json()` doesn't detect `-> session` return type

**What it does:** Bidirectional communication (tool ↔ agent via stdin/stdout)

```python
from toolable import session, SessionEvent

@app.command()
def interactive_chat() -> session:
    """Chat with the tool."""
    yield SessionEvent.start("Chat started!")

    while True:
        yield SessionEvent.awaiting("You: ")
        user_input = yield  # Receives: {"message": "hello"}

        if user_input.get("action") == "quit":
            break

        yield SessionEvent.awaiting(f"Bot: {user_input['message']}\n")

    yield SessionEvent.end("success")
```

**Protocol:**
```
Tool → {"type": "session_start", "message": "Chat started!", "prompt": "> "}
Tool → {"type": "awaiting_input", "prompt": "You: "}
Agent → {"message": "hello"}
Tool → {"type": "awaiting_input", "prompt": "Bot: hello\n"}
Tool → {"type": "session_end", "status": "success"}
```

**Integration needed:**
- Detect `-> session` in `_agent_execute_json()`
- Call `run_session_tool(result)` instead of wrapping in Response
- Update discovery to detect session commands

---

### 4. **LLM Sampling** (`sample`)
**Status:** ✅ Code ready, works if agent framework supports it
**Location:** `src/toolable/sampling.py`
**Note:** Requires agent framework to implement callback protocol

**What it does:** Tool requests LLM completion from the calling agent

```python
from toolable import sample

@app.command()
def ask_llm(prompt: str):
    """Use LLM during execution."""
    response = sample(
        prompt=prompt,
        max_tokens=100,
        temperature=0.7
    )
    return {"response": response}
```

**Protocol (stdin mode):**
```
Tool → {"type": "sample_request", "id": "abc123", "prompt": "...", "max_tokens": 100}
Agent → {"type": "sample_response", "id": "abc123", "content": "LLM response here"}
```

**Protocol (HTTP mode):**
```python
configure_sampling("http://localhost:8000/sample")
# Tool POSTs to URL, expects {"content": "response"}
```

**Integration status:** ✅ Works if agent supports the protocol

---

## Integration Roadmap (Task 14 from Plan)

### Step 1: Update `_agent_execute_json()` to detect streaming/session

```python
def _agent_execute_json(self, json_input: str) -> None:
    # ... existing code ...

    # Execute command
    result = command_info.callback(**params)

    # NEW: Detect streaming/session from return type
    type_hints = get_type_hints(command_info.callback)
    return_type = type_hints.get("return", None)

    if return_type == stream or hasattr(result, '__next__'):
        from toolable.streaming import run_streaming_tool
        run_streaming_tool(result)
        return

    if return_type == session:
        from toolable.session import run_session_tool
        run_session_tool(result)
        return

    # Normal result
    print(json.dumps(Response.success(result)))
```

### Step 2: Update discovery to detect modes

```python
def _agent_discover(self) -> None:
    for command_info in self.registered_commands:
        type_hints = get_type_hints(command_info.callback)
        return_type = type_hints.get("return", None)

        tools.append({
            "name": command_info.name,
            "summary": summary,
            "streaming": return_type == stream,      # NEW
            "session_mode": return_type == session,   # NEW
        })
```

---

## Summary Table

| Feature | Code Status | Exported | Agent Integration | Plan Task |
|---------|-------------|----------|-------------------|-----------|
| **Notifications** | ✅ Complete | ✅ Yes | ✅ Working | N/A |
| **Streaming** | ✅ Complete | ✅ Yes | 🔄 Needs work | Task 14 |
| **Session** | ✅ Complete | ✅ Yes | 🔄 Needs work | Task 14 |
| **Sampling** | ✅ Complete | ✅ Yes | ⚠️ Agent-dependent | N/A |
| **Resources** | ✅ Complete | ✅ Yes | ✅ Working | Task 8 |
| **Prompts** | ✅ Complete | ✅ Yes | ✅ Working | Task 8 |

**Legend:**
- ✅ Complete/Working
- 🔄 Needs integration
- ⚠️ Depends on external agent framework
