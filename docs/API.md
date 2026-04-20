# API Reference

## Memory Provider (`formalcc-memory`)

### Class: `FormalCCMemoryProvider`

Implements the Hermes `MemoryProvider` interface.

#### Properties

**`name`** → `str`
Returns `"formalcc-memory"`.

**`is_available()`** → `bool`
Returns `True` if provider is initialized. No network calls.

#### Methods

**`initialize(config: dict, hermes_home: Path) → None`**
Initialize provider with Hermes config and home directory.

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `dict` | Hermes config dict (reads `formalcc` section) |
| `hermes_home` | `Path` | Hermes home directory for local state |

---

**`prefetch(context: dict) → Optional[str]`**
Prefetch memory before model call. Returns memory block string or `None`.

| Context Key | Type | Description |
|-------------|------|-------------|
| `session_id` | `str` | Current session ID |
| `query` | `str` | User query for memory retrieval |
| `hints` | `dict` | Optional hints (scene, repo_id) |

---

**`sync_turn(turn_data: dict) → None`**
Sync turn data to memory (non-blocking).

| Turn Data Key | Type | Description |
|---------------|------|-------------|
| `session_id` | `str` | Current session ID |
| `turn_id` | `str` | Turn identifier |
| `user_message` | `str` | User message content |
| `assistant_message` | `str` | Assistant response content |
| `metadata` | `dict` | Optional metadata |

---

**`session_end(session_data: dict) → None`**
Finalize session and flush memory.

| Session Data Key | Type | Description |
|------------------|------|-------------|
| `session_id` | `str` | Session to finalize |
| `metadata` | `dict` | Optional metadata |

---

**`get_tool_schemas() → list[dict]`**
Returns tool schemas for memory tools. Returns empty list if `enable_memory_tools` is `False`.

Tools returned:
- `cc_memory_search`
- `cc_memory_profile`

---

**`handle_tool_call(tool_name: str, arguments: dict) → dict`**
Handle memory tool invocations from the model.

| Tool | Arguments | Returns |
|------|-----------|---------|
| `cc_memory_search` | `query: str`, `limit: int` | `{"result": {...}}` |
| `cc_memory_profile` | _(none)_ | `{"workspace_id": ..., "session_id": ..., "turn_count": ...}` |

---

**`get_config_schema() → dict`**
Returns JSON schema for provider configuration.

---

**`save_config(config: dict) → None`**
Save provider configuration to local config file.

---

## Context Engine (`formalcc-engine`)

### Class: `FormalCCContextEngine`

Implements the Hermes `ContextEngine` interface.

#### Properties

**`name`** → `str`
Returns `"formalcc-engine"`.

#### Methods

**`initialize(config: dict, hermes_home: Path) → None`**
Initialize context engine.

---

**`update_from_response(response: dict, context: dict) → None`**
Update internal state from model response. Increments turn counter.

---

**`should_compress(messages: list[dict], token_count: int, threshold: int) → bool`**
Returns `True` when `token_count > threshold`.

---

**`compress(messages: list[dict], context: dict, focus_topic: Optional[str] = None) → list[dict]`**
Compile context via FormalCC Runtime. Returns OpenAI-style messages.

| Context Key | Type | Description |
|-------------|------|-------------|
| `session_id` | `str` | Current session ID |
| `repo_id` | `str` | Repository ID (triggers coding scene) |
| `document_id` | `str` | Document ID (triggers vision scene) |
| `revision` | `str` | Git revision (default: `"main"`) |

| Parameter | Type | Description |
|-----------|------|-------------|
| `focus_topic` | `str` | Optional topic to focus compression on |

On failure, returns original `messages` unchanged.

---

## Shared Components

### `RuntimeClient`

Async HTTP client for FormalCC Runtime API.

```python
async with RuntimeClient(
    base_url="https://api.formsy.ai",
    api_key_env="FORMALCC_API_KEY",
    timeout_s=30,
    max_retries=3,
) as client:
    response = await client.memory_prefetch(request)
```

#### Methods

| Method | Endpoint | Description |
|--------|----------|-------------|
| `memory_prefetch(request)` | `POST /v1/runtime/memory_prefetch` | Prefetch memory |
| `memory_sync_turn(request)` | `POST /v1/runtime/memory_sync_turn` | Sync turn |
| `session_end(request)` | `POST /v1/runtime/session_end` | End session |
| `compile(request)` | `POST /v1/runtime/compile` | Compile context |
| `memory_search(...)` | `POST /v1/runtime/memory/search` | Search memory |

---

### `ConfigValidator`

Validates FormalCC configuration.

```python
result = ConfigValidator.validate_config(config_dict)
# result.valid: bool
# result.errors: list[str]
# result.warnings: list[str]
```

---

### `CircuitBreaker`

Circuit breaker for API resilience.

```python
cb = CircuitBreaker(CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=2,
    timeout_seconds=60,
))
result = cb.call(my_function, *args)
```

States: `CLOSED` → `OPEN` → `HALF_OPEN` → `CLOSED`

---

### `ErrorHandler`

User-friendly error handling.

```python
message = ErrorHandler.get_user_friendly_message(error)
suggestions = ErrorHandler.get_recovery_suggestions(error)
```

---

### `ErrorRecovery`

Retry decision logic.

```python
if ErrorRecovery.should_retry(error, attempt=0, max_attempts=3):
    delay = ErrorRecovery.get_retry_delay(error, attempt=0)
    await asyncio.sleep(delay)
```

---

## Error Types

| Error | Description |
|-------|-------------|
| `FormalCCError` | Base exception |
| `AuthenticationError` | Invalid or missing API key |
| `ConfigurationError` | Invalid configuration |
| `RuntimeAPIError` | API returned an error (has `status_code`) |
| `TimeoutError` | Request timed out |

---

## Configuration Schema

```yaml
formalcc:
  base_url: string          # Default: "https://api.formsy.ai"
  api_key_env: string       # Default: "FORMALCC_API_KEY"
  workspace_id: string      # Default: "ws_default"
  tenant_id: string         # Optional
  timeout_s: integer        # Default: 30
  max_retries: integer      # Default: 3
  enable_memory_tools: bool # Default: true
  enable_diagnostics: bool  # Default: true
  default_scene: string     # Default: "auto"
```
