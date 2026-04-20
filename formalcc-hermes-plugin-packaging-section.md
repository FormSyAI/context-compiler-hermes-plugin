# FormalCC Hermes Plugin Packaging, Installation, and Activation

## Why this section exists

The prior architecture documents describe FormalCC as an external context runtime and memory system for Hermes Agent, but they do not fully explain how an enterprise user would actually install, activate, and operate FormalCC inside Hermes.

Hermes uses a plugin-based extension system. In the current Hermes design, external memory providers and context engines are both provider plugins, both are single-select, and both are managed through `hermes plugins` or config. Therefore, a production-ready FormalCC integration must include a **plugin packaging and distribution layer**, not only Runtime APIs.

This section defines how FormalCC should be packaged for Hermes, how users install it, how it is activated, and how it binds to the FormalCC Runtime API.

---

## Design goals

1. Make FormalCC installable through the standard Hermes plugin workflow.
2. Preserve the earlier architecture decision: Hermes remains the agent runtime, while FormalCC remains the external compiler-grade context and memory system.
3. Support both early PoC installation and enterprise-controlled versioned deployment.
4. Keep coding and vision scene routing inside FormalCC server-side control planes, not as separate Hermes plugins.
5. Provide enterprise-friendly diagnostics and setup workflows.

---

## Core packaging decision

FormalCC should be distributed to Hermes as **one plugin distribution with two provider plugins**:

- `formalcc-memory`
- `formalcc-engine`

Optional:
- one small helper plugin or provider CLI surface for diagnostics, setup checking, and runtime health commands.

### Why this is the right structure

- Hermes supports **one external memory provider at a time**.
- Hermes supports **one context engine at a time**.
- Coding and vision should not become separate Hermes context-engine plugins, because Hermes chooses a single active context engine; scene routing should happen inside FormalCC Runtime.
- This preserves the earlier architecture principle: **single Hermes engine plugin, multi-backend FormalCC control plane**.

---

## What each plugin does

### 1. `formalcc-memory`

This is the external Hermes memory provider.

Responsibilities:
- implement the Hermes `MemoryProvider` interface
- prefetch code-memory or long-term task memory before model calls
- sync turns back into FormalCC memory pipelines
- finalize / flush memory at session end
- optionally expose memory-related tools such as:
  - `cc_memory_search`
  - `cc_memory_profile`
  - `cc_memory_conclude`

Binding target:
- FormalCC Memory Runtime APIs
  - `/v1/runtime/memory_prefetch`
  - `/v1/runtime/memory_sync_turn`
  - `/v1/runtime/session_end`

### 2. `formalcc-engine`

This is the external Hermes context engine.

Responsibilities:
- implement the Hermes `ContextEngine` interface
- replace the built-in Hermes context compressor
- decide whether to compress / compile
- send compile requests to FormalCC Runtime
- receive a compiled context bundle and convert it to valid Hermes/OpenAI-style messages
- route requests internally to coding / vision / general compile paths through FormalCC Runtime

Binding target:
- FormalCC Runtime APIs
  - `/v1/runtime/compile`
  - `/v1/runtime/advisory`
  - optionally resource preparation endpoints

### Optional 3. Helper diagnostics surface

A small helper surface is recommended for enterprise usability.

Possible commands:
- `hermes formalcc-memory status`
- `hermes formalcc-memory config`
- `hermes formalcc-memory test`
- `hermes formalcc-engine doctor`

This can be implemented either:
- as provider CLI under `formalcc-memory/cli.py`, or
- as a small additional general plugin.

Recommended near-term choice:
- start with provider CLI for `formalcc-memory`
- add a tiny diagnostic plugin only if enterprise installation workflows require more structure

---

## Discovery and distribution modes

FormalCC should support **two installation modes**.

### Mode A — Git-based plugin installation

Best for:
- early joint testing with Hermes
- PoCs
- community or open-core distribution

Installation path:
```bash
hermes plugins install your-org/formalcc-hermes-plugin
# or
hermes plugins install https://github.com/your-org/formalcc-hermes-plugin.git
```

Advantages:
- simple
- aligned with Hermes native plugin install flow
- easy for pilots and developer users

Trade-offs:
- looser enterprise version governance
- less ideal for locked-down enterprise environments

### Mode B — pip package distribution

Best for:
- enterprise deployment
- controlled version pinning
- CI/CD rollout
- internal package mirrors

Installation path:
```bash
pip install formalcc-hermes-plugin
```

The package should register via Hermes plugin entry points so Hermes auto-discovers it on startup.

Advantages:
- version pinning
- enterprise-friendly release management
- cleaner compatibility control

Trade-offs:
- slightly more packaging work
- requires robust release discipline

### Recommended packaging strategy

- **PoC / community**: Git install supported
- **Enterprise / production**: pip package strongly supported
- both modes should remain available

---

## Recommended repository structure

```text
formalcc-hermes-plugin/
├── plugins/
│   ├── memory/
│   │   └── formalcc-memory/
│   │       ├── __init__.py
│   │       ├── plugin.yaml
│   │       ├── cli.py
│   │       └── README.md
│   └── context_engine/
│       └── formalcc-engine/
│           ├── __init__.py
│           ├── plugin.yaml
│           └── README.md
├── skills/
│   └── formalcc/
│       └── SKILL.md
├── pyproject.toml
└── README.md
```

### Notes

- `skills/` is optional but useful. It gives Hermes an installable knowledge surface describing when to use FormalCC and how coding / vision / memory routing works.
- `plugin.yaml` should carry provider metadata, version, and hook declarations.
- `pyproject.toml` should support entry-point based discovery for pip installations.

---

## Activation model inside Hermes

### Installation is not activation

This distinction must be explicit in product docs.

1. User installs the plugin distribution.
2. Hermes discovers the available provider plugins.
3. User selects the active provider plugins through:
   - `hermes plugins`, or
   - direct `config.yaml` editing.

### Expected active choices

- active memory provider = `formalcc-memory`
- active context engine = `formalcc-engine`

### Example config

```yaml
memory:
  provider: "formalcc-memory"

context:
  engine: "formalcc-engine"

formalcc:
  base_url: "https://compiler.company.internal"
  api_key_env: "FORMALCC_API_KEY"
  workspace: "default"
  tenant: "acme"
  timeout_s: 15
  mode: "enterprise"
```

The plugin implementation can either:
- read `formalcc.*` from config files, or
- keep the official provider-facing config minimal and store the rest in provider-local JSON under `HERMES_HOME`.

Recommended practice:
- keep setup prompts minimal
- move advanced options into provider-local config files

---

## Detailed provider behavior requirements

### `formalcc-memory` requirements

The provider must:
- implement `name`, `is_available()`, `initialize()`, `get_tool_schemas()`, `handle_tool_call()`, `get_config_schema()`, and `save_config()` as required by Hermes
- keep `is_available()` free of network calls
- make `sync_turn()` non-blocking
- use `hermes_home` / `get_hermes_home()` for all local state
- support profile isolation
- tolerate backend unavailability gracefully

### `formalcc-engine` requirements

The engine must:
- implement `update_from_response()`, `should_compress()`, and `compress()`
- emit valid OpenAI-style messages for Hermes consumption
- support `focus_topic` compatibility in compression calls
- preserve coding vs. vision routing inside FormalCC Runtime
- degrade gracefully to simpler packing if Runtime is unavailable

---

## Server-side routing principle

Hermes should not know whether a compile request is coding or vision in provider topology terms.

Instead:
- Hermes always talks to one active `formalcc-engine`
- `formalcc-engine` talks to one FormalCC Runtime surface
- FormalCC Runtime performs scene routing internally

This is important for three reasons:

1. Hermes only allows one active context engine.
2. Coding and vision compile contracts should remain evolvable without changing Hermes plugin topology.
3. Enterprise deployments should control routing policy server-side.

---

## CLI and operator ergonomics

Enterprise deployments will frequently fail at configuration and connectivity rather than at core algorithm quality. Therefore, diagnostics are not optional in practice.

### Recommended provider CLI

At minimum, provide:

```bash
hermes formalcc-memory status
hermes formalcc-memory config
hermes formalcc-memory test
```

If needed later, add:

```bash
hermes formalcc-engine doctor
```

### What these commands should validate

- base URL reachability
- API key validity
- workspace / tenant resolution
- current active provider selection
- Runtime version compatibility
- last successful memory sync timestamp
- scene routing smoke test

---

## Compatibility and lifecycle requirements

The plugin packaging section should explicitly inherit the earlier Hermes smoke-suite constraints.

### Required compatibility points

1. **Prefetch visibility contract**
   - prefetched memory should be visible to the model context but not pollute persisted transcript

2. **Sequential tool dispatch stability**
   - memory provider tools must work in both sequential and concurrent dispatch paths

3. **Compression compatibility**
   - context engine must safely handle `focus_topic`

4. **Non-blocking memory sync**
   - memory sync must not delay final assistant response

5. **Graceful fallback**
   - Runtime failures should degrade, not crash Hermes

6. **Profile isolation**
   - all provider-local files must remain scoped to the active `HERMES_HOME`

---

## How this section changes the earlier architecture

This plugin packaging layer clarifies that FormalCC integration is not complete with Runtime APIs alone.

The real deployment stack becomes:

1. **FormalCC Core Engines**
   - Code / Vision / Memory engines
2. **FormalCC Runtime API Plane**
   - compile, memory prefetch, sync, advisory, resource prep
3. **FormalCC Hermes Plugin Distribution**
   - `formalcc-memory`
   - `formalcc-engine`
4. **Hermes Runtime**
   - agent loop, tools, terminal, patch generation, verification

This improves the architecture in two ways:

- it makes installation and activation operationally concrete
- it preserves the original division of labor: Hermes is the agent runtime; FormalCC is the external compiler-grade intelligence plane

---

## Recommended next implementation steps

### Phase 1
- create the plugin distribution repository
- implement `formalcc-memory` minimal provider
- implement `formalcc-engine` minimal context engine
- support Git install workflow

### Phase 2
- add pip packaging with Hermes entry-point discovery
- add minimal provider CLI commands
- document enterprise `config.yaml` and env conventions

### Phase 3
- integrate the Hermes smoke suite with the real plugin package
- validate profile isolation, sync semantics, and fallback behavior
- publish version compatibility matrix for Hermes ↔ FormalCC Runtime

---

## Final recommendation

FormalCC should be presented to Hermes users not only as a runtime service, but as an **installable Hermes plugin distribution** with:

- one external memory provider
- one external context engine
- optional diagnostics surface
- dual packaging modes: Git and pip

This is the missing deployment layer that turns the earlier architecture from a conceptual integration into a real installable product.
