# FormalCC Hermes Plugin Implementation Design

> **Version**: 1.0
> **Date**: 2026-04-20
> **Status**: Ready for Implementation

## Executive Summary

This document defines the implementation design for `formalcc-hermes-plugin`, a Python package that integrates FormalCC's compiler-grade context and memory system with Hermes Agent. The plugin provides two Hermes provider plugins (`formalcc-memory` and `formalcc-engine`) that connect Hermes to the FormalCC Runtime API via the formsy-gateway.

### Key Design Principles

1. **Thin Plugin Layer**: Plugins are lightweight adapters that translate Hermes provider interfaces to FormalCC Runtime API calls
2. **Server-Side Intelligence**: Scene routing (coding/vision/general) happens in FormalCC Runtime, not in Hermes plugin topology
3. **Graceful Degradation**: Runtime unavailability degrades to simpler behavior rather than crashing Hermes
4. **Enterprise-Ready**: Supports both Git-based (PoC) and pip-based (enterprise) installation
5. **Profile Isolation**: All plugin state respects `HERMES_HOME` and profile boundaries

---

## 1. Architecture Overview

### 1.1 Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│                      Hermes Agent                           │
│  (agent loop, tools, terminal, patch, verification)         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Provider Interface
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              formalcc-hermes-plugin                         │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ formalcc-memory  │      │ formalcc-engine  │            │
│  │ (MemoryProvider) │      │ (ContextEngine)  │            │
│  └──────────────────┘      └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS + OAuth2/API Key
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   formsy-gateway                            │
│  (auth, rate limiting, circuit breaker, audit logging)      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Internal HTTP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FormalCC Runtime API Service                   │
│  (scene router, coding/vision/memory engines)               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Plugin Responsibilities

**formalcc-memory (MemoryProvider)**
- Implements Hermes `MemoryProvider` interface
- Calls `/v1/runtime/memory_prefetch` before model invocations
- Calls `/v1/runtime/memory_sync_turn` after each turn (non-blocking)
- Calls `/v1/runtime/session_end` on session cleanup
- Exposes memory tools: `cc_memory_search`, `cc_memory_profile`
- Injects memory blocks as hidden system messages (visible to model, not to transcript)

**formalcc-engine (ContextEngine)**
- Implements Hermes `ContextEngine` interface
- Replaces built-in Hermes context compressor
- Calls `/v1/runtime/compile` for context compilation
- Handles scene routing (coding/vision/general) via Runtime API
- Supports `focus_topic` hints for compression
- Converts `CompileBundle` to OpenAI-style messages
- Degrades gracefully on Runtime unavailability

---

## 2. Repository Structure

```
formalcc-hermes-plugin/
├── plugins/
│   ├── memory/
│   │   └── formalcc-memory/
│   │       ├── __init__.py           # Provider registration
│   │       ├── provider.py           # MemoryProvider implementation
│   │       ├── client.py             # Runtime API client
│   │       ├── config.py             # Configuration management
│   │       ├── cli.py                # Diagnostic commands
│   │       ├── plugin.yaml           # Provider metadata
│   │       └── README.md
│   └── context_engine/
│       └── formalcc-engine/
│           ├── __init__.py           # Engine registration
│           ├── engine.py             # ContextEngine implementation
│           ├── client.py             # Runtime API client (shared)
│           ├── config.py             # Configuration management (shared)
│           ├── message_converter.py  # CompileBundle → OpenAI messages
│           ├── plugin.yaml           # Engine metadata
│           └── README.md
├── shared/
│   ├── __init__.py
│   ├── runtime_client.py             # Shared HTTP client
│   ├── auth.py                       # API key / OAuth2 handling
│   ├── models.py                     # Pydantic models for API
│   ├── errors.py                     # Error handling
│   └── utils.py                      # Common utilities
├── tests/
│   ├── test_memory_provider.py
│   ├── test_context_engine.py
│   ├── test_runtime_client.py
│   └── conftest.py
├── pyproject.toml                    # Package metadata + entry points
├── README.md                         # Installation & usage guide
├── DESIGN.md                         # This document
├── CHANGELOG.md
└── LICENSE
```

---

## 3. Core Interfaces

### 3.1 Hermes MemoryProvider Interface

Based on the test suite, the MemoryProvider interface requires:

```python
class MemoryProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'formalcc-memory')"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available (no network calls)"""
        pass

    @abstractmethod
    async def initialize(self, config: dict, hermes_home: Path) -> None:
        """Initialize provider with config and home directory"""
        pass

    @abstractmethod
    async def prefetch(self, context: dict) -> Optional[str]:
        """Prefetch memory before model call. Returns memory block."""
        pass

    @abstractmethod
    async def sync_turn(self, turn_data: dict) -> None:
        """Sync turn data to memory (non-blocking)"""
        pass

    @abstractmethod
    async def session_end(self, session_data: dict) -> None:
        """Finalize session and flush memory"""
        pass

    @abstractmethod
    def get_tool_schemas(self) -> list[dict]:
        """Return tool schemas for memory tools"""
        pass

    @abstractmethod
    async def handle_tool_call(self, tool_name: str, arguments: dict) -> dict:
        """Handle memory tool invocations"""
        pass

    @abstractmethod
    def get_config_schema(self) -> dict:
        """Return JSON schema for provider config"""
        pass

    @abstractmethod
    async def save_config(self, config: dict) -> None:
        """Save provider configuration"""
        pass
```

### 3.2 Hermes ContextEngine Interface

```python
class ContextEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name (e.g., 'formalcc-engine')"""
        pass

    @abstractmethod
    async def update_from_response(self, response: dict, context: dict) -> None:
        """Update internal state from model response"""
        pass

    @abstractmethod
    def should_compress(self, messages: list[dict], token_count: int, threshold: int) -> bool:
        """Determine if compression should occur"""
        pass

    @abstractmethod
    async def compress(
        self,
        messages: list[dict],
        context: dict,
        focus_topic: Optional[str] = None
    ) -> list[dict]:
        """Compress/compile context and return OpenAI-style messages"""
        pass
```

---

## 4. Runtime API Contract Mapping

### 4.1 Endpoint Mapping

| Plugin Method | Gateway Endpoint | Purpose |
|--------------|------------------|---------|
| `prefetch()` | `POST /v1/runtime/memory_prefetch` | Get memory block before model call |
| `sync_turn()` | `POST /v1/runtime/memory_sync_turn` | Async turn ingestion (202 Accepted) |
| `session_end()` | `POST /v1/runtime/session_end` | Final memory flush |
| `handle_tool_call(cc_memory_search)` | `POST /v1/runtime/memory/search` | Tool-driven memory retrieval |
| `compress()` | `POST /v1/runtime/compile` | Context compilation |

### 4.2 Authentication

The plugin authenticates to formsy-gateway using Bearer API key:

```http
Authorization: Bearer fsy_live_abc123...
Content-Type: application/json
X-Request-ID: <uuid>
X-Session-ID: <hermes_session_id>
```

### 4.3 Key Request/Response Models

**Memory Prefetch Request:**
```json
{
  "workspace_id": "ws_abc123",
  "session_id": "sess_xyz789",
  "turn_id": "turn_001",
  "query": "Fix regex bug in validators.py",
  "limit": 10,
  "hints": {
    "scene": "coding",
    "repo_id": "org/repo"
  }
}
```

**Compile Request:**
```json
{
  "scene": "auto",
  "workspace_id": "ws_abc123",
  "session_id": "sess_xyz789",
  "turn_id": "turn_001",
  "identity": {
    "repo_id": "org/repo",
    "revision": "main"
  },
  "task": {
    "instruction": "Fix username validator",
    "task_type": "bugfix"
  },
  "hints": {
    "focus_topic": "validators.py regex",
    "bypass_router": false
  }
}
```

**Compile Response (CompileBundle):**
```json
{
  "scene": "coding",
  "compiled_messages": [
    {
      "role": "system",
      "content": "Focus on validators.py and regex line endings."
    }
  ],
  "evidence_units": [...],
  "supported_claims": [...],
  "advisory": {
    "recommended_action": "patch",
    "rationale_tail": "Prefer changing regex terminator only."
  },
  "metrics": {"elapsed_ms": 21}
}
```

---

## 5. Configuration Management

### 5.1 Configuration Sources

Configuration is loaded from multiple sources (in priority order):

1. **Environment variables** (highest priority)
2. **Hermes config.yaml** (`formalcc` section)
3. **Provider-local config** (`~/.hermes/profiles/<profile>/formalcc-config.json`)
4. **Defaults** (lowest priority)

### 5.2 Configuration Schema

```yaml
# In Hermes config.yaml
memory:
  provider: "formalcc-memory"

context:
  engine: "formalcc-engine"

formalcc:
  base_url: "https://api.formsy.ai"  # or enterprise gateway URL
  api_key_env: "FORMALCC_API_KEY"    # env var name for API key
  workspace_id: "ws_default"
  tenant_id: "acme"
  timeout_s: 30
  max_retries: 3
  enable_memory_tools: true
  enable_diagnostics: true
```

### 5.3 Environment Variables

```bash
# Required
FORMALCC_API_KEY=fsy_live_abc123...

# Optional
FORMALCC_BASE_URL=https://api.formsy.ai
FORMALCC_WORKSPACE_ID=ws_default
FORMALCC_TENANT_ID=acme
FORMALCC_TIMEOUT=30
```

---

## 6. Implementation Details

### 6.1 Memory Provider Implementation

**Key Behaviors:**

1. **Prefetch (Hidden Injection)**
   - Called before each model invocation
   - Returns memory block as string
   - Hermes injects as hidden system message (visible to model, not transcript)
   - Non-blocking, timeout 5s

2. **Sync Turn (Non-blocking)**
   - Called after each assistant response
   - Sends turn data to Runtime API asynchronously
   - Does NOT block final response to user
   - Fire-and-forget with error logging

3. **Session End (Blocking)**
   - Called on session cleanup
   - Flushes final memory state
   - Blocks until complete or timeout (10s)

4. **Memory Tools**
   - `cc_memory_search`: Explicit memory search tool
   - `cc_memory_profile`: Get memory profile/stats

**Error Handling:**
- Prefetch failure → return empty string, log warning
- Sync failure → log error, continue
- Session end failure → log error, continue
- Tool call failure → return error message to model

### 6.2 Context Engine Implementation

**Key Behaviors:**

1. **Should Compress**
   - Always returns `True` when token count > threshold
   - Delegates compression decision to FormalCC Runtime

2. **Compress (Compile)**
   - Extracts context from Hermes messages
   - Builds RuntimeRequest with identity, task, hints
   - Calls `/v1/runtime/compile`
   - Converts CompileBundle to OpenAI messages
   - Returns compiled messages

3. **Scene Routing**
   - Detects repo_id → coding scene
   - Detects document_id → vision_doc scene
   - Otherwise → general scene
   - Runtime API performs final routing

4. **Focus Topic Support**
   - Passes `focus_topic` in `hints` field
   - Used for compression with specific focus

**Error Handling:**
- Compile failure → return minimal bundle (empty compiled_messages)
- Timeout → return original messages (no compression)
- 503 Service Unavailable → graceful degradation

### 6.3 Message Conversion

**CompileBundle → OpenAI Messages:**

```python
def convert_compile_bundle_to_messages(bundle: CompileBundle) -> list[dict]:
    """Convert CompileBundle to OpenAI-style messages."""
    messages = []
    
    # Add compiled messages directly
    for msg in bundle.compiled_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Optionally add advisory as system message
    if bundle.advisory and bundle.advisory.recommended_action:
        advisory_text = f"[ADVISORY] {bundle.advisory.rationale_tail}"
        messages.append({
            "role": "system",
            "content": advisory_text
        })
    
    return messages
```

---

## 7. Error Handling & Graceful Degradation

### 7.1 Error Categories

| Error Type | HTTP Status | Plugin Behavior |
|-----------|-------------|-----------------|
| Invalid Request | 400 | Log error, return empty result |
| Unauthorized | 401 | Log error, raise config error |
| Not Found | 404 | Log warning, return empty result |
| Timeout | 504 | Log warning, return fallback |
| Service Unavailable | 503 | Log warning, return fallback |
| Internal Error | 500 | Log error, return fallback |

### 7.2 Fallback Strategies

**Memory Prefetch Failure:**
- Return empty string
- Model proceeds without memory context
- Log warning for diagnostics

**Compile Failure:**
- Return original messages (no compression)
- Model proceeds with full context
- Log error for diagnostics

**Sync Turn Failure:**
- Log error
- Continue without blocking user
- Memory may be incomplete but session continues

### 7.3 Circuit Breaker

The formsy-gateway already implements circuit breaker. The plugin should:
- Respect 503 responses (circuit open)
- Implement client-side timeout (30s default)
- Use exponential backoff for retries (3 attempts max)

---

## 8. Diagnostic CLI

### 8.1 Commands

```bash
# Check provider status
hermes formalcc-memory status

# Show configuration
hermes formalcc-memory config

# Test connectivity
hermes formalcc-memory test

# Context engine diagnostics
hermes formalcc-engine doctor
```

### 8.2 Status Command Output

```
FormalCC Memory Provider Status
================================
Provider: formalcc-memory
Status: ✓ Available
Base URL: https://api.formsy.ai
Workspace: ws_abc123
Tenant: acme

Connectivity: ✓ OK (127ms)
Last Prefetch: 2026-04-20 10:15:32 (2 minutes ago)
Last Sync: 2026-04-20 10:17:45 (success)
Session: sess_xyz789

Memory Tools:
  ✓ cc_memory_search
  ✓ cc_memory_profile
```

### 8.3 Test Command

```bash
hermes formalcc-memory test
```

Validates:
- Base URL reachability
- API key validity
- Workspace/tenant resolution
- Memory prefetch smoke test
- Scene routing smoke test

---

## 9. Packaging & Distribution

### 9.1 pyproject.toml

```toml
[project]
name = "formalcc-hermes-plugin"
version = "0.1.0"
description = "FormalCC integration for Hermes Agent"
requires-python = ">=3.10"
dependencies = [
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
]

[project.entry-points."hermes.plugins.memory"]
formalcc-memory = "plugins.memory.formalcc_memory:FormalCCMemoryProvider"

[project.entry-points."hermes.plugins.context_engine"]
formalcc-engine = "plugins.context_engine.formalcc_engine:FormalCCContextEngine"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### 9.2 Installation Modes

**Mode A: Git Install (PoC)**
```bash
hermes plugins install your-org/formalcc-hermes-plugin
```

**Mode B: pip Install (Enterprise)**
```bash
pip install formalcc-hermes-plugin
```

### 9.3 Activation

After installation, activate in Hermes config:

```yaml
memory:
  provider: "formalcc-memory"

context:
  engine: "formalcc-engine"
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

- `test_memory_provider.py`: Test MemoryProvider interface implementation
- `test_context_engine.py`: Test ContextEngine interface implementation
- `test_runtime_client.py`: Test HTTP client with mocked responses
- `test_message_converter.py`: Test CompileBundle → OpenAI conversion

### 10.2 Integration Tests

Reuse existing test suite in `symbolic-reasoning-agent/tests/hermes_integration/`:
- Memory prefetch injection
- Scene routing (coding/vision/general)
- Tool dispatch
- Focus topic support
- Graceful degradation

### 10.3 Smoke Tests

Minimal validation:
1. Provider loads successfully
2. Config is read correctly
3. API connectivity works
4. Memory prefetch returns data
5. Compile returns bundle

---

## 11. Implementation Phases

### Phase 1: Core Plugin Implementation (Week 1)
- [ ] Create repository structure
- [ ] Implement shared runtime client
- [ ] Implement formalcc-memory provider
- [ ] Implement formalcc-engine context engine
- [ ] Add basic error handling

### Phase 2: Configuration & CLI (Week 2)
- [ ] Configuration management (env vars, config files)
- [ ] Diagnostic CLI commands
- [ ] Error handling and graceful degradation
- [ ] Unit tests

### Phase 3: Integration & Testing (Week 3)
- [ ] Integration with existing Hermes test suite
- [ ] End-to-end testing
- [ ] Documentation (README, usage guide)
- [ ] Packaging (pyproject.toml, entry points)

### Phase 4: Enterprise Features (Week 4)
- [ ] pip packaging
- [ ] Version compatibility matrix
- [ ] Advanced diagnostics
- [ ] Production deployment guide

---

## 12. Security Considerations

### 12.1 API Key Management

- API keys stored in environment variables (never in code)
- Support for key rotation
- Validate key format (`fsy_live_*` or `fsy_test_*`)

### 12.2 Request Security

- All requests over HTTPS
- Request ID for tracing
- Timeout enforcement (30s default)
- No sensitive data in logs

### 12.3 Profile Isolation

- All plugin state scoped to `HERMES_HOME`
- No cross-profile data leakage
- Respect Hermes profile boundaries

---

## 13. Monitoring & Observability

### 13.1 Logging

```python
import logging

logger = logging.getLogger("formalcc.memory")

# Log levels
logger.debug("Prefetch request: %s", request_id)
logger.info("Memory prefetch completed: %dms", elapsed_ms)
logger.warning("Prefetch timeout, using fallback")
logger.error("Sync turn failed: %s", error)
```

### 13.2 Metrics

Track in provider state:
- Last prefetch timestamp
- Last sync timestamp
- Success/failure counts
- Average latency
- Circuit breaker state

### 13.3 Diagnostics

Expose via CLI:
- Provider status
- Connectivity health
- Recent operation history
- Error logs

---

## 14. Compatibility Matrix

| Hermes Version | Plugin Version | Runtime API Version | Status |
|---------------|----------------|---------------------|--------|
| 0.9.x | 0.1.0 | v0.3 | ✓ Supported |
| 1.0.x | 0.1.0 | v0.3 | ✓ Supported |

---

## 15. References

- [FormalCC Runtime API Spec v0.3](../symbolic-reasoning-agent/design/formalcc-runtime-api-spec-v0.3-refined.md)
- [FormalCC Context Runtime Architecture](../symbolic-reasoning-agent/design/formalcc-context-runtime-architecture.md)
- [Hermes Integration Smoke Suite](../symbolic-reasoning-agent/design/formalcc-hermes-smoke-suite-implementation-draft.md)
- [Formsy Gateway Runtime API Integration](../formsy-gateway/apps/api-service/RUNTIME_API_INTEGRATION.md)
- [Plugin Packaging Section](./formalcc-hermes-plugin-packaging-section.md)

---

## 16. Next Steps

1. Review and approve this design document
2. Create repository structure
3. Begin Phase 1 implementation
4. Set up CI/CD pipeline
5. Write integration tests

