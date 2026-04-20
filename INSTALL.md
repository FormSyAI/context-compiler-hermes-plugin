# Installation Guide

This guide covers different installation methods for the FormalCC Hermes Plugin.

## Prerequisites

- Python 3.10 or higher
- Hermes Agent installed
- FormalCC API key

## Installation Methods

### Method 1: Git Install (Recommended for Development)

Install directly from GitHub:

```bash
hermes plugins install your-org/formalcc-hermes-plugin
```

Or clone and install locally:

```bash
git clone https://github.com/your-org/formalcc-hermes-plugin.git
cd formalcc-hermes-plugin
pip install -e .
```

### Method 2: pip Install (Recommended for Production)

Install from PyPI:

```bash
pip install formalcc-hermes-plugin
```

## Configuration

### 1. Set API Key

Set your FormalCC API key as an environment variable:

```bash
export FORMALCC_API_KEY=fsy_live_your_key_here
```

For persistent configuration, add to your shell profile:

```bash
# ~/.bashrc or ~/.zshrc
export FORMALCC_API_KEY=fsy_live_your_key_here
```

### 2. Configure Hermes

Edit your Hermes configuration file (`~/.hermes/config.yaml`):

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
  max_retries: 3
  enable_memory_tools: true
  enable_diagnostics: true
```

### 3. Verify Installation

Check that the plugins are installed and configured correctly:

```bash
hermes formalcc-memory status
hermes formalcc-memory test
```

Expected output:
```
FormalCC Memory Provider Status
========================================
Provider: formalcc-memory
Base URL: https://api.formsy.ai
Workspace: ws_default
Tenant: your_tenant
Timeout: 30s
Memory Tools: ✓ Enabled
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FORMALCC_API_KEY` | API key for authentication | Required |
| `FORMALCC_BASE_URL` | Base URL for Runtime API | `https://api.formsy.ai` |
| `FORMALCC_WORKSPACE_ID` | Workspace identifier | `ws_default` |
| `FORMALCC_TENANT_ID` | Tenant identifier | None |
| `FORMALCC_TIMEOUT` | Request timeout in seconds | `30` |

### Hermes Config Options

In `config.yaml` under the `formalcc` section:

```yaml
formalcc:
  # API Configuration
  base_url: "https://api.formsy.ai"
  api_key_env: "FORMALCC_API_KEY"

  # Identity
  workspace_id: "ws_default"
  tenant_id: "your_tenant"

  # Performance
  timeout_s: 30
  max_retries: 3

  # Features
  enable_memory_tools: true
  enable_diagnostics: true

  # Context Engine
  default_scene: "auto"
```

## Enterprise Configuration

For enterprise deployments with custom gateway URLs:

```yaml
formalcc:
  base_url: "https://formalcc.company.internal"
  workspace_id: "ws_enterprise"
  tenant_id: "company"
  timeout_s: 60
  max_retries: 5
```

## Troubleshooting

### Plugin Not Found

If Hermes doesn't recognize the plugins:

1. Verify installation: `pip list | grep formalcc`
2. Check entry points: `python -c "import pkg_resources; print(list(pkg_resources.iter_entry_points('hermes.plugins.memory')))"`
3. Restart Hermes

### Authentication Errors

If you see authentication errors:

1. Verify API key is set: `echo $FORMALCC_API_KEY`
2. Check key format (should start with `fsy_live_` or `fsy_test_`)
3. Test connectivity: `hermes formalcc-memory test`

### Connection Errors

If you can't connect to the Runtime API:

1. Check base URL is correct
2. Verify network connectivity
3. Check firewall rules
4. Try with increased timeout: `FORMALCC_TIMEOUT=60`

## Uninstallation

To remove the plugin:

```bash
pip uninstall formalcc-hermes-plugin
```

Then remove the configuration from `~/.hermes/config.yaml`.

## Next Steps

- Read the [Usage Guide](docs/USAGE.md)
- Check the [API Documentation](docs/API.md)
- See [Examples](docs/EXAMPLES.md)
