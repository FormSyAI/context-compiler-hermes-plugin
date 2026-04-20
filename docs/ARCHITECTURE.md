# Architecture

## Overview

The FormalCC Hermes Plugin integrates with the Hermes Agent framework to provide memory and context management capabilities via the FormalCC Runtime API.

```
┌─────────────────────────────────────────────────────────────┐
│                        Hermes Agent                         │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    Memory    │    │   Context    │    │    Model     │  │
│  │   Provider   │    │   Engine     │    │   (LLM)      │  │
│  │  (formalcc)  │    │  (formalcc)  │    │              │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘  │
│         │                  │                               │
└─────────┼──────────────────┼───────────────────────────────┘
          │                  │
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  FormalCC Runtime API                       │
│                                                             │
│  /v1/runtime/memory_prefetch    /v1/runtime/compile         │
│  /v1/runtime/memory_sync_turn   /v1/runtime/memory/search   │
│  /v1/runtime/session_end                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Memory Prefetch Flow

```
User sends message
       │
       ▼
┌─────────────────┐
│ MemoryProvider  │
│  .prefetch()    │
└────────┬────────┘
         │  POST /v1/runtime/memory_prefetch
         │  { workspace_id, session_id, turn_id, query }
         ▼
┌─────────────────┐
│  FormalCC API   │
│  returns        │
│  memory_block   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Hermes injects memory as hidden        │
│  system message:                        │
│  [MEMORY] <memory_block>                │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Model receives │
│  enriched       │
│  context        │
└─────────────────┘
```

---

## Context Compression Flow

```
Token count > threshold?
         │
        YES
         │
         ▼
┌─────────────────┐
│ ContextEngine   │
│  .compress()    │
└────────┬────────┘
         │  Detect scene
         │  (coding / vision / general)
         │
         ▼
┌─────────────────┐
│  POST           │
│  /v1/runtime/   │
│  compile        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Returns CompileBundle:                 │
│  - compiled_messages (condensed)        │
│  - advisory (recommended action)        │
│  - evidence_units (supporting context)  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  MessageConverter builds final          │
│  OpenAI-style messages:                 │
│  1. compiled_messages                   │
│  2. [ADVISORY] <rationale>              │
└─────────────────────────────────────────┘
```

---

## Turn Sync Flow

```
Model responds
       │
       ▼
┌─────────────────┐
│ MemoryProvider  │
│  .sync_turn()   │  ← non-blocking (fire-and-forget)
└────────┬────────┘
         │  POST /v1/runtime/memory_sync_turn
         │  { user_message, assistant_message, turn_id }
         ▼
┌─────────────────┐
│  FormalCC API   │
│  indexes turn   │
│  into memory    │
└─────────────────┘
```

---

## Circuit Breaker States

```
         ┌─────────────────────────────────┐
         │                                 │
    failures >= threshold            success >= threshold
         │                                 │
         ▼                                 │
  ┌─────────────┐   timeout elapsed   ┌────┴────────┐
  │    OPEN     │ ──────────────────► │  HALF_OPEN  │
  │  (reject)   │                     │  (testing)  │
  └─────────────┘                     └─────────────┘
                                            │
                                       failure
                                            │
                                            ▼
  ┌─────────────┐                     ┌─────────────┐
  │   CLOSED    │ ◄────────────────── │    OPEN     │
  │  (normal)   │   success >= 2      │  (reject)   │
  └─────────────┘                     └─────────────┘
```

---

## Plugin Architecture

```
formalcc-hermes-plugin/
│
├── shared/                     # Shared across both plugins
│   ├── runtime_client.py       # Async HTTP client
│   ├── auth.py                 # API key management
│   ├── models.py               # Pydantic request/response models
│   ├── errors.py               # Exception hierarchy
│   ├── resilience.py           # Circuit breaker + retry
│   ├── config_validator.py     # Config validation + generation
│   ├── error_handler.py        # User-friendly error messages
│   └── utils.py                # Utilities
│
├── plugins/
│   ├── memory/formalcc_memory/
│   │   ├── provider.py         # Hermes MemoryProvider interface
│   │   ├── client.py           # Memory API wrapper
│   │   ├── config.py           # Config management
│   │   ├── diagnostics.py      # Diagnostic runner
│   │   ├── cli.py              # CLI commands
│   │   └── plugin.yaml         # Plugin metadata
│   │
│   └── context_engine/formalcc_engine/
│       ├── engine.py           # Hermes ContextEngine interface
│       ├── client.py           # Compile API wrapper
│       ├── config.py           # Config management
│       ├── message_converter.py # Bundle → OpenAI messages
│       └── plugin.yaml         # Plugin metadata
│
└── tests/
    ├── conftest.py
    ├── test_memory_provider.py
    ├── test_context_engine.py
    ├── test_runtime_client.py
    ├── test_phase2_enhancements.py
    ├── test_integration.py
    ├── test_e2e.py
    └── test_coverage_improvements.py
```

---

## Error Hierarchy

```
FormalCCError (base)
├── AuthenticationError     # 401 - invalid/missing API key
├── ConfigurationError      # bad config values
├── RuntimeAPIError         # API returned error (has status_code)
└── TimeoutError            # request timed out
```

---

## Scene Detection Logic

```
compile_context has repo_id?
    YES → scene = "coding"
    NO  → compile_context has document_id?
              YES → scene = "vision_doc"
              NO  → scene = "general"
```
