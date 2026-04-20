# Usage Guide

This guide explains how to use the FormalCC Hermes Plugin effectively.

## Overview

Once installed and configured, the FormalCC plugins work automatically within Hermes:

- **Memory Provider**: Prefetches relevant context before each model call
- **Context Engine**: Compresses context when token limits are approached

## Memory Provider Features

### Automatic Memory Prefetch

Before each model invocation, the memory provider automatically:

1. Extracts the user query
2. Calls the FormalCC Runtime API
3. Retrieves relevant memory context
4. Injects it as a hidden system message

This happens transparently - you don't need to do anything.

### Memory Tools

When `enable_memory_tools: true`, the model can use these tools:

#### cc_memory_search

Search memory for specific information:

```
User: Can you search memory for authentication patterns?
Assistant: [Uses cc_memory_search tool]
```

The tool accepts:
- `query`: Search query string
- `limit`: Maximum results (default: 10)

#### cc_memory_profile

Get memory statistics:

```
User: What's in my memory profile?
Assistant: [Uses cc_memory_profile tool]
```

Returns:
- Workspace ID
- Session ID
- Turn count

### Turn Synchronization

After each conversation turn, the provider automatically:

1. Captures user and assistant messages
2. Sends them to the Runtime API (async)
3. Updates the memory index

This is non-blocking and doesn't delay responses.

## Context Engine Features

### Automatic Context Compression

When your conversation exceeds the token threshold, the context engine:

1. Detects the scene (coding/vision/general)
2. Calls the FormalCC Runtime API
3. Receives a compiled context bundle
4. Replaces the full context with the compiled version

### Scene Detection

The engine automatically detects the scene based on context:

**Coding Scene**
- Triggered when `repo_id` is present
- Optimized for code-related tasks
- Includes file paths, function names, etc.

**Vision Scene**
- Triggered when `document_id` is present
- Optimized for document analysis
- Includes visual context

**General Scene**
- Default fallback
- General conversation optimization

### Focus Topic

You can provide a focus topic for targeted compression:

```python
# In Hermes context
context = {
    "focus_topic": "authentication flow"
}
```

The engine will prioritize content related to the focus topic.

### Advisory Messages

The Runtime API may return advisory messages:

```
[ADVISORY] Prefer minimal changes to the regex validator
```

These are injected as system messages to guide the model.

## CLI Commands

### Memory Provider Commands

**Check Status**
```bash
hermes formalcc-memory status
```

Shows:
- Provider availability
- Configuration
- Connectivity status
- Last operation timestamps

**Test Connectivity**
```bash
hermes formalcc-memory test
```

Validates:
- API key
- Network connectivity
- Runtime API availability
- Memory prefetch functionality

**Show Configuration**
```bash
hermes formalcc-memory config
```

Displays current configuration values.

## Configuration Examples

### Development Setup

```yaml
formalcc:
  base_url: "https://api.formsy.ai"
  workspace_id: "ws_dev"
  timeout_s: 30
  enable_memory_tools: true
  enable_diagnostics: true
```

### Production Setup

```yaml
formalcc:
  base_url: "https://formalcc.company.internal"
  workspace_id: "ws_prod"
  tenant_id: "company"
  timeout_s: 60
  max_retries: 5
  enable_memory_tools: false
  enable_diagnostics: false
```

### Testing Setup

```yaml
formalcc:
  base_url: "https://api.formsy.ai"
  workspace_id: "ws_test"
  timeout_s: 10
  max_retries: 1
```

## Best Practices

### Memory Management

1. **Use descriptive queries**: When using memory search, be specific
2. **Monitor memory profile**: Check memory stats periodically
3. **Clean up sessions**: Let sessions end properly for memory flush

### Context Compression

1. **Provide focus topics**: When working on specific features
2. **Trust the engine**: Let it decide when to compress
3. **Review advisories**: Pay attention to advisory messages

### Performance

1. **Set appropriate timeouts**: Balance speed vs reliability
2. **Use retries wisely**: Don't set too many retries
3. **Monitor diagnostics**: Check status regularly

## Troubleshooting

### Memory Not Working

If memory prefetch isn't working:

1. Check provider status: `hermes formalcc-memory status`
2. Test connectivity: `hermes formalcc-memory test`
3. Check logs for errors
4. Verify API key is valid

### Context Not Compressing

If context isn't being compressed:

1. Verify token count exceeds threshold
2. Check engine is active in config
3. Look for Runtime API errors in logs
4. Test with a longer conversation

### Slow Performance

If operations are slow:

1. Reduce timeout: `timeout_s: 15`
2. Decrease retries: `max_retries: 1`
3. Check network latency
4. Consider using a closer gateway

## Advanced Usage

### Custom Workspace

Use different workspaces for different projects:

```bash
export FORMALCC_WORKSPACE_ID=ws_project_alpha
```

### Multiple Tenants

Switch between tenants:

```bash
export FORMALCC_TENANT_ID=tenant_a
```

### Debugging

Enable verbose logging:

```python
import logging
logging.getLogger("formalcc").setLevel(logging.DEBUG)
```

## Examples

See the [examples directory](examples/) for:
- Basic usage examples
- Integration patterns
- Custom configurations
- Advanced scenarios
