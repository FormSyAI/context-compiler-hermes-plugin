"""Tests for FormalCC Memory Provider."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from plugins.memory.formalcc_memory.provider import FormalCCMemoryProvider
from plugins.memory.formalcc_memory.config import MemoryConfig
from shared.models import MemoryPrefetchResponse


@pytest.mark.asyncio
async def test_provider_initialization(mock_hermes_home, mock_config):
    """Test provider initialization."""
    provider = FormalCCMemoryProvider()

    assert provider.name == "formalcc-memory"
    assert not provider.is_available()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

    assert provider.is_available()


@pytest.mark.asyncio
async def test_prefetch_success(mock_hermes_home, mock_config, sample_memory_prefetch_response):
    """Test successful memory prefetch."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        # Mock the runtime client
        mock_response = MemoryPrefetchResponse(**sample_memory_prefetch_response)
        provider._memory_client.prefetch = AsyncMock(return_value=mock_response.memory_block)

        context = {
            "session_id": "test_session",
            "query": "test query",
        }

        result = await provider.prefetch(context)

        assert result == "Test memory content"


@pytest.mark.asyncio
async def test_prefetch_failure_graceful(mock_hermes_home, mock_config):
    """Test graceful handling of prefetch failure."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        # Mock failure
        provider._memory_client.prefetch = AsyncMock(return_value="")

        context = {"session_id": "test_session", "query": "test"}
        result = await provider.prefetch(context)

        assert result is None


@pytest.mark.asyncio
async def test_sync_turn(mock_hermes_home, mock_config):
    """Test turn synchronization."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        provider._memory_client.sync_turn = AsyncMock()

        turn_data = {
            "session_id": "test_session",
            "turn_id": "turn_001",
            "user_message": "Hello",
            "assistant_message": "Hi there",
        }

        await provider.sync_turn(turn_data)

        provider._memory_client.sync_turn.assert_called_once()


def test_get_tool_schemas(mock_hermes_home, mock_config):
    """Test tool schema generation."""
    provider = FormalCCMemoryProvider()
    provider._config = MemoryConfig.from_dict(mock_config["formalcc"])

    schemas = provider.get_tool_schemas()

    assert len(schemas) == 2
    assert schemas[0]["name"] == "cc_memory_search"
    assert schemas[1]["name"] == "cc_memory_profile"


@pytest.mark.asyncio
async def test_handle_tool_call_search(mock_hermes_home, mock_config):
    """Test memory search tool call."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        provider._runtime_client.memory_search = AsyncMock(
            return_value={"results": ["item1", "item2"]}
        )

        result = await provider.handle_tool_call(
            "cc_memory_search",
            {"query": "test", "limit": 10}
        )

        assert "result" in result
        assert result["result"]["results"] == ["item1", "item2"]
