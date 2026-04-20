"""CLI commands for formalcc-memory provider."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from .config import ConfigManager
from shared import RuntimeClient

logger = logging.getLogger("formalcc.memory.cli")


async def status_command(hermes_home: Path) -> None:
    """Show provider status."""
    config_manager = ConfigManager(hermes_home)
    config = config_manager.load_config()

    print("FormalCC Memory Provider Status")
    print("=" * 40)
    print(f"Provider: formalcc-memory")
    print(f"Base URL: {config.base_url}")
    print(f"Workspace: {config.workspace_id}")
    print(f"Tenant: {config.tenant_id or 'N/A'}")
    print(f"Timeout: {config.timeout_s}s")
    print(f"Memory Tools: {'✓ Enabled' if config.enable_memory_tools else '✗ Disabled'}")


async def test_command(hermes_home: Path) -> None:
    """Test connectivity to Runtime API."""
    config_manager = ConfigManager(hermes_home)
    config = config_manager.load_config()

    print("Testing FormalCC Runtime API connectivity...")
    print(f"Base URL: {config.base_url}")

    try:
        async with RuntimeClient(
            base_url=config.base_url,
            api_key_env=config.api_key_env,
            timeout_s=config.timeout_s,
        ) as client:
            # Test memory prefetch
            from shared.models import MemoryPrefetchRequest

            request = MemoryPrefetchRequest(
                workspace_id=config.workspace_id,
                session_id="test_session",
                turn_id="test_turn_001",
                query="test query",
            )

            response = await client.memory_prefetch(request)
            print(f"✓ Memory prefetch successful ({response.elapsed_ms}ms)")
            print(f"  Retrieved: {response.retrieved_count} items")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return

    print("\n✓ All tests passed")


def main():
    """CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: hermes formalcc-memory <command>")
        print("Commands: status, test, config")
        sys.exit(1)

    command = sys.argv[1]
    hermes_home = Path.home() / ".hermes"

    if command == "status":
        asyncio.run(status_command(hermes_home))
    elif command == "test":
        asyncio.run(test_command(hermes_home))
    elif command == "config":
        config_manager = ConfigManager(hermes_home)
        config = config_manager.load_config()
        print(config.to_dict())
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
