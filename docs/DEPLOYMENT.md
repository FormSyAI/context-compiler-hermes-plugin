# Deployment Guide

## Prerequisites

- Python 3.10+
- Hermes Agent installed
- FormalCC API key (`fsy_live_*`)
- Network access to `https://api.formsy.ai`

---

## Local Development

```bash
git clone https://github.com/FormSyAI/context-compiler-hermes-plugin.git
cd context-compiler-hermes-plugin
pip install -e ".[dev]"
export FORMALCC_API_KEY=fsy_test_your_key
hermes formalcc-memory doctor
```

---

## Production Deployment

### 1. Install

```bash
pip install formalcc-hermes-plugin
```

### 2. Configure

```bash
# Set API key (use secrets manager in production)
export FORMALCC_API_KEY=fsy_live_your_key_here

# Or use a .env file
cat > ~/.hermes/.env << EOF
FORMALCC_API_KEY=fsy_live_your_key_here
EOF
```

### 3. Hermes Config

```yaml
# ~/.hermes/config.yaml
memory:
  provider: "formalcc-memory"

context:
  engine: "formalcc-engine"

formalcc:
  base_url: "https://api.formsy.ai"
  workspace_id: "ws_production"
  tenant_id: "your_tenant"
  timeout_s: 60
  max_retries: 5
  enable_memory_tools: false
  enable_diagnostics: true
```

### 4. Verify

```bash
hermes formalcc-memory doctor
```

---

## Enterprise / On-Premise

For deployments with a private FormalCC gateway:

```yaml
formalcc:
  base_url: "https://formalcc.company.internal"
  workspace_id: "ws_enterprise"
  tenant_id: "company"
  timeout_s: 60
```

Ensure the gateway URL is reachable:
```bash
curl https://formalcc.company.internal/health
```

---

## Docker

```dockerfile
FROM python:3.13-slim

RUN pip install formalcc-hermes-plugin hermes-agent

ENV FORMALCC_API_KEY=""
ENV FORMALCC_BASE_URL="https://api.formsy.ai"
ENV FORMALCC_WORKSPACE_ID="ws_default"

COPY config.yaml /root/.hermes/config.yaml

CMD ["hermes", "start"]
```

```bash
docker build -t my-hermes-agent .
docker run -e FORMALCC_API_KEY=fsy_live_xxx my-hermes-agent
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FORMALCC_API_KEY` | Yes | — | API key |
| `FORMALCC_BASE_URL` | No | `https://api.formsy.ai` | Gateway URL |
| `FORMALCC_WORKSPACE_ID` | No | `ws_default` | Workspace ID |
| `FORMALCC_TENANT_ID` | No | — | Tenant ID |
| `FORMALCC_TIMEOUT` | No | `30` | Timeout in seconds |

---

## Health Checks

```bash
# Check plugin status
hermes formalcc-memory status

# Run full diagnostics
hermes formalcc-memory doctor

# Validate config
hermes formalcc-memory validate
```

Expected healthy output:
```
✓ Configuration is valid
✓ Connectivity: OK (127ms)
✓ Memory Prefetch: OK (5 items, 150ms)
✓ All diagnostics passed
```
