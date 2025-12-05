# Toolable Feature Showcase

Complete demonstration of all Toolable features: **Typer CLI + MCP-like agent capabilities**.

## 🎯 Quick Start

```bash
# Install
pip install -e .

# Try the demo
cd examples
python complete_demo.py --help
```

---

## 1️⃣ Human CLI Mode (Pure Typer)

### Standard Help

```bash
$ python complete_demo.py --help
```
```
Usage: complete_demo.py [OPTIONS] COMMAND [ARGS]...

  Complete demo of Toolable: Typer + MCP features

╭─ Commands ───────────────────────────────────────╮
│ hello          Say hello                         │
│ calculate      Perform calculation               │
│ process_batch  Process items with streaming      │
│ long_task      Run task with notifications       │
│ divide         Divide with error handling        │
╰──────────────────────────────────────────────────╯
```

### Execute Commands

```bash
$ python complete_demo.py hello "Alice" --excited
Hello, Alice! 🎉

$ python complete_demo.py calculate 10 5 --operation multiply
# Returns: {"operation": "multiply", "a": 10, "b": 5, "result": 50}
```

---

## 2️⃣ Agent Discovery

### Discover All Capabilities

```bash
$ python complete_demo.py --discover
```
```json
{
  "name": "complete-tool",
  "version": "0.2.0",
  "tools": [
    {
      "name": "hello",
      "summary": "Say hello (works for humans and agents).",
      "streaming": false,
      "session_mode": false
    },
    {
      "name": "process_batch",
      "summary": "Process items with real-time streaming progress.",
      "streaming": true,
      "session_mode": false
    }
  ],
  "resources": [
    {
      "uri_pattern": "/items/{item_id}",
      "summary": "Get item by ID",
      "mime_types": []
    }
  ],
  "prompts": []
}
```

**Notice:**
- ✅ `process_batch` correctly marked as `"streaming": true`
- ✅ Resources discovered automatically

---

## 3️⃣ Schema Generation

### Get Command Schema

```bash
$ python complete_demo.py calculate --manifest
```
```json
{
  "name": "calculate",
  "summary": "Perform calculation with type hints.",
  "description": "Perform calculation with type hints.",
  "schema": {
    "type": "object",
    "properties": {
      "a": {"type": "number"},
      "b": {"type": "number"},
      "operation": {"type": "string", "default": "add"}
    },
    "required": ["a", "b"]
  }
}
```

**Notice:**
- ✅ Types extracted from function signature
- ✅ Optional params show defaults
- ✅ Required params listed

---

## 4️⃣ JSON Execution

### Normal Commands

```bash
$ python complete_demo.py '{"command": "hello", "params": {"name": "Bob", "excited": true}}'
```
```
Hello, Bob! 🎉
```
```json
{"status": "success", "result": {"greeting": "Hello, Bob! 🎉", "name": "Bob"}}
```

### Math Operations

```bash
$ python complete_demo.py '{"command": "calculate", "params": {"a": 15, "b": 3, "operation": "divide"}}'
```
```json
{"status": "success", "result": {"operation": "divide", "a": 15, "b": 3, "result": 5.0}}
```

---

## 5️⃣ Streaming Mode

### Real-time Progress Events

```bash
$ python complete_demo.py '{"command": "process_batch", "params": {"items": 3, "delay": 0.1}}'
```

**Output (jsonlines):**
```json
{"type": "progress", "message": "Processing item 1/3", "percent": 33}
{"type": "progress", "message": "Processing item 2/3", "percent": 66}
{"type": "progress", "message": "Processing item 3/3", "percent": 100}
{"type": "artifact", "name": "batch_results.json", "uri": "/tmp/batch_results.json"}
{"type": "result", "status": "success", "result": {"processed": 3, "time_taken": 0.3}}
```

**Notice:**
- ✅ One event per line (jsonlines format)
- ✅ Progress updates in real-time
- ✅ Artifacts emitted
- ✅ Final result at the end

---

## 6️⃣ Notifications (Side-Channel)

### Progress to stderr, Result to stdout

```bash
$ python complete_demo.py long-task --steps 3 2>&1
```

**stderr (notifications):**
```json
{"type": "notification", "kind": "log", "level": "info", "message": "Starting long task..."}
{"type": "notification", "kind": "progress", "message": "Step 1/3", "percent": 33}
{"type": "notification", "kind": "progress", "message": "Step 2/3", "percent": 66}
{"type": "notification", "kind": "progress", "message": "Step 3/3", "percent": 100}
{"type": "notification", "kind": "log", "level": "info", "message": "Task completed successfully"}
```

**stdout (result):**
```json
{"status": "success", "steps_completed": 3}
```

**Notice:**
- ✅ Notifications go to **stderr** (monitoring)
- ✅ Result goes to **stdout** (structured data)
- ✅ Two separate channels

---

## 7️⃣ Error Handling

### Structured Error Responses

```bash
$ python complete_demo.py '{"command": "divide", "params": {"a": 10, "b": 0}}'
```
```json
{
  "status": "error",
  "error": {
    "code": "INVALID_INPUT",
    "message": "Cannot divide by zero",
    "suggestion": "Use a non-zero divisor",
    "recoverable": true
  }
}
```

**Notice:**
- ✅ Error codes for programmatic handling
- ✅ Human-readable messages
- ✅ Actionable suggestions
- ✅ Recoverable flag guides retry behavior

---

## 🎨 Feature Comparison

| Feature | Typer | Toolable |
|---------|-------|----------|
| **Type-hinted CLI** | ✅ | ✅ |
| **Rich output** | ✅ | ✅ |
| **Shell completion** | ✅ | ✅ |
| **Auto-generated help** | ✅ | ✅ |
| **Discovery (`--discover`)** | ❌ | ✅ |
| **Schema gen (`--manifest`)** | ❌ | ✅ |
| **JSON execution** | ❌ | ✅ |
| **Streaming events** | ❌ | ✅ |
| **Session mode** | ❌ | ✅ |
| **Resources** | ❌ | ✅ |
| **Prompts** | ❌ | ✅ |
| **Side-channel notifications** | ❌ | ✅ |
| **LLM sampling** | ❌ | ✅ |
| **Structured errors** | ❌ | ✅ |

---

## 📦 Architecture

```
Human CLI Mode:          Agent Mode:
   (Typer)               (MCP-like)

┌──────────┐            ┌──────────┐
│  --help  │            │--discover│
│ --flags  │            │--manifest│
│  ARGS    │            │   JSON   │
└────┬─────┘            └────┬─────┘
     │                       │
     ▼                       ▼
┌────────────────────────────────┐
│    Toolable (Typer fork)       │
│  - Command routing             │
│  - Type validation             │
│  - Agent flag detection        │
└────────────────────────────────┘
     │                       │
     ▼                       ▼
┌──────────┐            ┌──────────┐
│  stdout  │            │  stdout  │
│  (text)  │            │  (JSON)  │
└──────────┘            └──────────┘
                        ┌──────────┐
                        │  stderr  │
                        │(notifs.) │
                        └──────────┘
```

---

## 🚀 Use Cases

### 1. CLI Tools for Both Humans and AI
```python
# One tool, two interfaces:
# - Developers use: git-tool commit --message "fix"
# - AI agents use: '{"command": "commit", "params": {"message": "fix"}}'
```

### 2. Long-Running Tasks with Progress
```python
@app.command()
def backup(files: int) -> stream:
    for i in range(files):
        yield StreamEvent.progress(f"Backing up {i}/{files}")
    yield StreamEvent.result({"backed_up": files})
```

### 3. Interactive Workflows (Session Mode)
```python
@app.command()
def interview() -> session:
    yield SessionEvent.start("Interview started")
    for question in questions:
        yield SessionEvent.awaiting(question)
        answer = yield
        # Process answer...
    yield SessionEvent.end("success")
```

### 4. Data Access (Resources)
```python
@app.resource(uri_pattern="/logs/{date}", summary="Get logs")
def get_logs(date: str):
    return read_logs(date)
```

---

## 🎯 Summary

**Toolable = Typer + Agent Superpowers**

✅ **Backwards compatible** - Existing Typer code works unchanged
✅ **Zero server overhead** - Direct CLI execution
✅ **MCP-like features** - Discovery, schemas, resources, streaming
✅ **Dual mode** - One tool for humans and AI agents
✅ **Type safe** - Full Pydantic validation
✅ **Production ready** - All features tested and working

**Getting started:** Just replace `from typer import Typer` with `from toolable import Toolable`!
