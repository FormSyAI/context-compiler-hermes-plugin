# Troubleshooting FAQ

## Authentication Issues

### "Authentication failed" error
**Symptom:** `RuntimeAPIError: Authentication failed (401)`

**Causes & Fixes:**
1. API key not set
   ```bash
   echo $FORMALCC_API_KEY  # Should print your key
   export FORMALCC_API_KEY=fsy_live_your_key_here
   ```
2. Wrong environment variable name
   ```yaml
   # In config.yaml, check api_key_env matches your env var
   formalcc:
     api_key_env: "FORMALCC_API_KEY"
   ```
3. Key expired — generate a new one from the FormalCC dashboard

---

### "Access forbidden" error
**Symptom:** `RuntimeAPIError: Access forbidden (403)`

**Causes & Fixes:**
1. API key doesn't have access to the workspace
   ```bash
   # Verify workspace_id matches your key's permissions
   hermes formalcc-memory validate
   ```
2. Wrong tenant_id
   ```yaml
   formalcc:
     tenant_id: "your_correct_tenant"
   ```

---

## Connectivity Issues

### "Connection failed" error
**Symptom:** `ConnectionError: Connection refused`

**Causes & Fixes:**
1. Wrong base_url
   ```bash
   curl https://api.formsy.ai/health  # Should return 200
   ```
2. Firewall blocking outbound HTTPS
   - Allow outbound traffic on port 443
3. VPN required for enterprise deployments
   - Connect to VPN before using the plugin

---

### "Request timed out" error
**Symptom:** `TimeoutError: Request timed out after 30s`

**Causes & Fixes:**
1. Increase timeout
   ```bash
   export FORMALCC_TIMEOUT=60
   ```
2. Check network latency
   ```bash
   curl -w "%{time_total}" https://api.formsy.ai/health
   ```
3. Use a closer gateway URL if available

---

## Memory Issues

### Memory not being prefetched
**Symptom:** No memory context injected before model calls

**Diagnosis:**
```bash
hermes formalcc-memory doctor
```

**Causes & Fixes:**
1. Provider not initialized — check Hermes config
   ```yaml
   memory:
     provider: "formalcc-memory"
   ```
2. API errors — check logs for warnings
   ```bash
   FORMALCC_LOG_LEVEL=DEBUG hermes ...
   ```
3. Empty query — ensure user message is non-empty

---

### Memory sync not working
**Symptom:** Memory not accumulating across turns

**Causes & Fixes:**
1. sync_turn is fire-and-forget — check logs for errors
2. Session ID not consistent across turns
3. API rate limiting — check for 429 errors in logs

---

## Context Compression Issues

### Context not being compressed
**Symptom:** Token count exceeds threshold but compression not triggered

**Causes & Fixes:**
1. Engine not configured
   ```yaml
   context:
     engine: "formalcc-engine"
   ```
2. Token count below threshold — check Hermes token counting
3. Compile API errors — check logs

---

### Compressed context missing information
**Symptom:** Important context lost after compression

**Causes & Fixes:**
1. Use focus_topic to preserve relevant content
   ```python
   context["focus_topic"] = "validators.py email regex"
   ```
2. Check advisory messages for guidance
3. Reduce compression threshold to trigger less aggressively

---

## CLI Issues

### "command not found: hermes"
**Fix:** Ensure Hermes is installed and in PATH
```bash
pip install hermes-agent
which hermes
```

### "Unknown command: formalcc-memory"
**Fix:** Ensure plugin is installed
```bash
pip list | grep formalcc
pip install formalcc-hermes-plugin
```

---

## Performance Issues

### High latency on memory prefetch
**Target:** < 200ms p99

**Fixes:**
1. Use a geographically closer gateway
2. Reduce `limit` parameter (default: 10)
3. Enable connection pooling (coming in Phase 4)

### High latency on compile
**Target:** < 500ms p99

**Fixes:**
1. Increase timeout to avoid false timeouts
2. Check if scene detection is correct
3. Reduce context size before compiling

---

## Diagnostic Commands

```bash
# Quick status check
hermes formalcc-memory status

# Verbose status with live diagnostics
hermes formalcc-memory status -v

# Full health check
hermes formalcc-memory doctor

# Validate configuration
hermes formalcc-memory validate

# Test connectivity
hermes formalcc-memory test

# Show current config
hermes formalcc-memory config
```
