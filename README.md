# FormalCC Hermes Plugin

FormalCC integration for Hermes Agent, providing compiler-grade context compression and memory management.

## Overview

This plugin integrates FormalCC's context runtime and memory system with Hermes Agent through two provider plugins:

- **formalcc-memory**: Memory provider for prefetch, sync, and session management
- **formalcc-engine**: Context engine for compiler-grade context compression

## Features

- 🧠 **Memory Prefetch**: Retrieve relevant context before model invocations
- 🔄 **Turn Synchronization**: Async memory updates without blocking responses
- 🎯 **Scene Routing**: Server-side routing for coding/vision/general contexts
- 🛠️ **Memory Tools**: Expose memory search and profile tools to the model
- 📊 **Graceful Degradation**: Continue operation when Runtime API is unavailable
- 🔐 **Enterprise Ready**: OAuth2/API key auth, profile isolation, diagnostics

## Installation

### Mode A: Git Install (PoC)

```bash
hermes plugins install your-org/formalcc-hermes-plugin
```

### Mode B: pip Install (Enterprise)

```bash
pip install formalcc-hermes-plugin
```

## Configuration

### 1. Set API Key

```bash
export FORMALCC_API_KEY=fsy_live_your_key_here
```

### 2. Activate in Hermes Config

Edit your Hermes `config.yaml`:

```yaml
memory:
  provider: "formalcc-memory"

context:
  engine: "formalcc-engine"

formalcc:
  base_url: "https://api.formsy.ai"
  workspace_id: "ws_default"
  tenant_id: "your_tenant"
  timeout_s: 30
  enable_memory_tools: true
```

### 3. Verify Installation

```bash
hermes formalcc-memory status
hermes formalcc-memory test
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Hermes Agent                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              formalcc-hermes-plugin                         │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │ formalcc-memory  │      │ formalcc-engine  │            │
│  └──────────────────┘      └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              FormalCC Runtime API Service                   │
└─────────────────────────────────────────────────────────────┘
```

## Usage

Once configured, the plugins work automatically:

- **Memory prefetch** happens before each model call
- **Turn sync** happens after each assistant response
- **Context compression** triggers when token count exceeds threshold
- **Memory tools** are available to the model when enabled

### Memory Tools

When `enable_memory_tools: true`, the model can use:

```python
# Search memory
cc_memory_search(query="authentication flow", limit=10)

# Get memory profile
cc_memory_profile()
```

## Development

### Setup

```bash
git clone https://github.com/your-org/formalcc-hermes-plugin.git
cd formalcc-hermes-plugin
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/
pytest tests/ --cov=plugins --cov=shared
```

### Code Quality

```bash
black .
ruff check .
```

## CLI Commands

### Memory Provider

```bash
# Check status
hermes formalcc-memory status

# Test connectivity
hermes formalcc-memory test

# Show configuration
hermes formalcc-memory config
```

## Compatibility

| Hermes Version | Plugin Version | Runtime API Version | Status |
|---------------|----------------|---------------------|--------|
| 0.9.x | 0.1.0 | v0.3 | ✓ Supported |
| 1.0.x | 0.1.0 | v0.3 | ✓ Supported |

## Documentation

- [Design Document](DESIGN.md)
- [Packaging Guide](formalcc-hermes-plugin-packaging-section.md)
- [Memory Provider README](plugins/memory/formalcc_memory/README.md)
- [Context Engine README](plugins/context_engine/formalcc_engine/README.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-org/formalcc-hermes-plugin/issues
- Documentation: https://docs.formalai.com
