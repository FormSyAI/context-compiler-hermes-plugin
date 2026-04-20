"""Integration tests for FormalCC Hermes Plugin.

These tests simulate real Hermes agent scenarios with the FormalCC plugins.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from plugins.memory.formalcc_memory.provider import FormalCCMemoryProvider
from plugins.context_engine.formalcc_engine.engine import FormalCCContextEngine
from shared.models import MemoryPrefetchResponse, CompileBundle, CompiledMessage


@pytest.mark.asyncio
async def test_memory_prefetch_injection(mock_hermes_home, mock_config):
    """Test memory prefetch is injected as hidden system message."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        # Mock memory prefetch response
        provider._memory_client.prefetch = AsyncMock(
            return_value="Relevant context: User prefers minimal changes"
        )

        context = {
            "session_id": "test_session",
            "query": "Fix the validator bug",
        }

        memory_block = await provider.prefetch(context)

        assert memory_block is not None
        assert "minimal changes" in memory_block
        provider._memory_client.prefetch.assert_called_once()


@pytest.mark.asyncio
async def test_scene_routing_coding(mock_hermes_home, mock_config, sample_compile_bundle):
    """Test scene routing detects coding scene."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        # Mock compile response
        bundle = CompileBundle(**sample_compile_bundle)
        engine._engine_client.compile = AsyncMock(return_value=bundle)

        messages = [
            {"role": "user", "content": "Fix bug in validators.py"}
        ]

        context = {
            "session_id": "test_session",
            "repo_id": "org/repo",  # Triggers coding scene
        }

        result = await engine.compress(messages, context)

        # Verify compile was called with coding scene
        call_args = engine._engine_client.compile.call_args
        assert call_args is not None
        # Scene should be detected as coding
        assert result is not None


@pytest.mark.asyncio
async def test_scene_routing_vision(mock_hermes_home, mock_config, sample_compile_bundle):
    """Test scene routing detects vision scene."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        bundle = CompileBundle(**sample_compile_bundle)
        engine._engine_client.compile = AsyncMock(return_value=bundle)

        messages = [
            {"role": "user", "content": "Analyze this document"}
        ]

        context = {
            "session_id": "test_session",
            "document_id": "doc_123",  # Triggers vision scene
        }

        result = await engine.compress(messages, context)

        assert result is not None
        engine._engine_client.compile.assert_called_once()


@pytest.mark.asyncio
async def test_tool_dispatch_sequential(mock_hermes_home, mock_config):
    """Test memory tools work in sequential dispatch."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        provider._runtime_client.memory_search = AsyncMock(
            return_value={"results": ["item1", "item2"]}
        )

        # First tool call
        result1 = await provider.handle_tool_call(
            "cc_memory_search",
            {"query": "authentication", "limit": 5}
        )

        # Second tool call
        result2 = await provider.handle_tool_call(
            "cc_memory_profile",
            {}
        )

        assert "result" in result1
        assert "workspace_id" in result2


@pytest.mark.asyncio
async def test_focus_topic_support(mock_hermes_home, mock_config, sample_compile_bundle):
    """Test focus topic is passed to compile."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        bundle = CompileBundle(**sample_compile_bundle)
        engine._engine_client.compile = AsyncMock(return_value=bundle)

        messages = [
            {"role": "user", "content": "Fix the regex in validators.py"}
        ]

        context = {"session_id": "test_session"}
        focus_topic = "validators.py regex"

        result = await engine.compress(messages, context, focus_topic=focus_topic)

        # Verify focus_topic was passed in hints
        call_args = engine._engine_client.compile.call_args
        assert call_args is not None
        kwargs = call_args.kwargs
        assert "hints" in kwargs
        assert kwargs["hints"]["focus_topic"] == focus_topic


@pytest.mark.asyncio
async def test_graceful_degradation_memory(mock_hermes_home, mock_config):
    """Test graceful degradation when memory prefetch fails."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        # Mock failure
        provider._memory_client.prefetch = AsyncMock(return_value="")

        context = {
            "session_id": "test_session",
            "query": "test query",
        }

        result = await provider.prefetch(context)

        # Should return None, not crash
        assert result is None


@pytest.mark.asyncio
async def test_graceful_degradation_compile(mock_hermes_home, mock_config, sample_messages):
    """Test graceful degradation when compile fails."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        # Mock failure
        engine._engine_client.compile = AsyncMock(return_value=None)

        context = {"session_id": "test_session"}

        result = await engine.compress(sample_messages, context)

        # Should return original messages, not crash
        assert result == sample_messages


@pytest.mark.asyncio
async def test_profile_isolation(tmp_path, mock_config):
    """Test that plugin state respects profile boundaries."""
    profile1 = tmp_path / "profile1"
    profile2 = tmp_path / "profile2"
    profile1.mkdir()
    profile2.mkdir()

    provider1 = FormalCCMemoryProvider()
    provider2 = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider1.initialize(mock_config, profile1)
        await provider2.initialize(mock_config, profile2)

        # Each provider should have its own state
        assert provider1._hermes_home != provider2._hermes_home
        assert provider1._hermes_home == profile1
        assert provider2._hermes_home == profile2


@pytest.mark.asyncio
async def test_non_blocking_sync(mock_hermes_home, mock_config):
    """Test that turn sync is non-blocking."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await provider.initialize(mock_config, mock_hermes_home)

        # Mock sync that would normally take time
        provider._memory_client.sync_turn = AsyncMock()

        turn_data = {
            "session_id": "test_session",
            "turn_id": "turn_001",
            "user_message": "Hello",
            "assistant_message": "Hi there",
        }

        # Should complete quickly without blocking
        await provider.sync_turn(turn_data)

        provider._memory_client.sync_turn.assert_called_once()


@pytest.mark.asyncio
async def test_advisory_injection(mock_hermes_home, mock_config):
    """Test that advisory messages are injected."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        # Create bundle with advisory
        from shared.models import Advisory
        bundle = CompileBundle(
            scene="coding",
            compiled_messages=[
                CompiledMessage(role="system", content="Focus on validators.py")
            ],
            advisory=Advisory(
                recommended_action="patch",
                rationale_tail="Prefer minimal changes to regex"
            )
        )

        engine._engine_client.compile = AsyncMock(return_value=bundle)

        messages = [{"role": "user", "content": "Fix bug"}]
        context = {"session_id": "test_session"}

        result = await engine.compress(messages, context)

        # Check that advisory was injected
        assert len(result) == 2
        assert any("[ADVISORY]" in msg.get("content", "") for msg in result)


@pytest.mark.asyncio
async def test_session_lifecycle(mock_hermes_home, mock_config):
    """Test complete session lifecycle: init -> prefetch -> sync -> end."""
    provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        # Initialize
        await provider.initialize(mock_config, mock_hermes_home)
        assert provider.is_available()

        # Mock client methods
        provider._memory_client.prefetch = AsyncMock(return_value="context")
        provider._memory_client.sync_turn = AsyncMock()
        provider._runtime_client.session_end = AsyncMock()

        # Prefetch
        context = {"session_id": "test_session", "query": "test"}
        memory = await provider.prefetch(context)
        assert memory == "context"

        # Sync turn
        turn_data = {
            "session_id": "test_session",
            "turn_id": "turn_001",
            "user_message": "Hello",
            "assistant_message": "Hi",
        }
        await provider.sync_turn(turn_data)

        # End session
        session_data = {"session_id": "test_session"}
        await provider.session_end(session_data)

        # Verify all methods were called
        provider._memory_client.prefetch.assert_called_once()
        provider._memory_client.sync_turn.assert_called_once()
        provider._runtime_client.session_end.assert_called_once()
