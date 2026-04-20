"""
FormalCC Hermes Plugin - Usage Examples

These examples demonstrate common usage patterns.
"""

# ============================================================
# Example 1: Basic Setup
# ============================================================

# Set environment variable
# export FORMALCC_API_KEY=fsy_live_your_key_here

# In Hermes config.yaml:
HERMES_CONFIG_EXAMPLE = """
memory:
  provider: "formalcc-memory"

context:
  engine: "formalcc-engine"

formalcc:
  base_url: "https://api.formsy.ai"
  workspace_id: "ws_default"
  timeout_s: 30
  enable_memory_tools: true
"""


# ============================================================
# Example 2: Coding Task with Memory
# ============================================================

async def example_coding_task():
    """Example: coding task with memory and context compression."""
    from pathlib import Path
    from plugins.memory.formalcc_memory.provider import FormalCCMemoryProvider
    from plugins.context_engine.formalcc_engine.engine import FormalCCContextEngine

    hermes_home = Path.home() / ".hermes"
    config = {
        "formalcc": {
            "base_url": "https://api.formsy.ai",
            "workspace_id": "ws_default",
        }
    }

    # Initialize providers
    memory = FormalCCMemoryProvider()
    engine = FormalCCContextEngine()

    await memory.initialize(config, hermes_home)
    await engine.initialize(config, hermes_home)

    session_id = "session_001"

    # Step 1: Prefetch memory before model call
    memory_block = await memory.prefetch({
        "session_id": session_id,
        "query": "Fix the email validator bug",
        "hints": {"scene": "coding", "repo_id": "org/myapp"},
    })

    # Step 2: Build messages (Hermes injects memory as hidden system message)
    messages = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Fix the email validator bug in validators.py"},
    ]

    if memory_block:
        messages.insert(1, {"role": "system", "content": f"[MEMORY] {memory_block}"})

    # Step 3: Compress context if needed
    if engine.should_compress(messages, token_count=8000, threshold=6000):
        messages = await engine.compress(
            messages,
            context={"session_id": session_id, "repo_id": "org/myapp"},
            focus_topic="validators.py email regex",
        )

    # Step 4: Call model (not shown - Hermes handles this)
    # response = await hermes.call_model(messages)

    # Step 5: Sync turn (non-blocking)
    await memory.sync_turn({
        "session_id": session_id,
        "turn_id": "turn_001",
        "user_message": "Fix the email validator bug",
        "assistant_message": "I'll fix the validator...",
    })

    # Step 6: End session
    await memory.session_end({"session_id": session_id})


# ============================================================
# Example 3: Memory Search Tool
# ============================================================

async def example_memory_search():
    """Example: using memory search tool."""
    from pathlib import Path
    from plugins.memory.formalcc_memory.provider import FormalCCMemoryProvider

    hermes_home = Path.home() / ".hermes"
    config = {"formalcc": {"workspace_id": "ws_default"}}

    memory = FormalCCMemoryProvider()
    await memory.initialize(config, hermes_home)

    # Get available tools
    tools = memory.get_tool_schemas()
    print(f"Available tools: {[t['name'] for t in tools]}")

    # Handle tool call from model
    result = await memory.handle_tool_call(
        "cc_memory_search",
        {"query": "authentication patterns", "limit": 5}
    )
    print(f"Search results: {result}")

    # Get memory profile
    profile = await memory.handle_tool_call("cc_memory_profile", {})
    print(f"Memory profile: {profile}")


# ============================================================
# Example 4: Enterprise Configuration
# ============================================================

ENTERPRISE_CONFIG = """
formalcc:
  base_url: "https://formalcc.company.internal"
  api_key_env: "FORMALCC_API_KEY"
  workspace_id: "ws_production"
  tenant_id: "acme"
  timeout_s: 60
  max_retries: 5
  enable_memory_tools: false
  enable_diagnostics: true
"""


# ============================================================
# Example 5: Configuration Validation
# ============================================================

def example_config_validation():
    """Example: validate configuration before use."""
    from shared.config_validator import ConfigValidator

    config = {
        "base_url": "https://api.formsy.ai",
        "workspace_id": "ws_default",
        "timeout_s": 30,
    }

    result = ConfigValidator.validate_config(config)

    if result.valid:
        print("✓ Configuration is valid")
    else:
        print("✗ Configuration errors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.warnings:
        print("⚠ Warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")


# ============================================================
# Example 6: Error Handling
# ============================================================

async def example_error_handling():
    """Example: handle errors gracefully."""
    from shared.error_handler import ErrorHandler, ErrorRecovery
    from shared.errors import RuntimeAPIError

    try:
        # Simulate API call
        raise RuntimeAPIError("Unauthorized", status_code=401)

    except RuntimeAPIError as e:
        # Get user-friendly message
        message = ErrorHandler.get_user_friendly_message(e)
        print(message)

        # Get recovery suggestions
        suggestions = ErrorHandler.get_recovery_suggestions(e)
        for suggestion in suggestions:
            print(f"  → {suggestion}")

        # Check if retryable
        if ErrorRecovery.should_retry(e, attempt=0, max_attempts=3):
            delay = ErrorRecovery.get_retry_delay(e, attempt=0)
            print(f"Retrying in {delay}s...")
