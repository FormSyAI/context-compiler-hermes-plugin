"""End-to-end tests simulating full Hermes agent scenarios."""

import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path

from plugins.memory.formalcc_memory.provider import FormalCCMemoryProvider
from plugins.context_engine.formalcc_engine.engine import FormalCCContextEngine
from shared.models import (
    MemoryPrefetchResponse,
    CompileBundle,
    CompiledMessage,
    Advisory,
)


@pytest.mark.asyncio
async def test_e2e_coding_task_with_memory(mock_hermes_home, mock_config):
    """End-to-end test: coding task with memory and context compression."""
    # Setup providers
    memory_provider = FormalCCMemoryProvider()
    context_engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await memory_provider.initialize(mock_config, mock_hermes_home)
        await context_engine.initialize(mock_config, mock_hermes_home)

        # Mock memory prefetch
        memory_provider._memory_client.prefetch = AsyncMock(
            return_value="Previous context: User prefers TDD approach"
        )

        # Mock compile
        bundle = CompileBundle(
            scene="coding",
            compiled_messages=[
                CompiledMessage(
                    role="system",
                    content="Focus on validators.py. Apply TDD approach."
                )
            ],
            advisory=Advisory(
                recommended_action="test_first",
                rationale_tail="Write tests before implementation"
            ),
        )
        context_engine._engine_client.compile = AsyncMock(return_value=bundle)

        # Simulate Hermes agent loop
        session_id = "e2e_session_001"

        # Step 1: Prefetch memory
        memory_context = {
            "session_id": session_id,
            "query": "Fix the email validator bug",
        }
        memory_block = await memory_provider.prefetch(memory_context)
        assert memory_block is not None
        assert "TDD" in memory_block

        # Step 2: Build messages with memory
        messages = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "system", "content": f"[MEMORY] {memory_block}"},
            {"role": "user", "content": "Fix the email validator bug in validators.py"},
        ]

        # Step 3: Compress context if needed
        compile_context = {
            "session_id": session_id,
            "repo_id": "org/myapp",
        }
        compressed = await context_engine.compress(
            messages, compile_context, focus_topic="validators.py email"
        )

        assert len(compressed) > 0
        assert any("validators.py" in msg.get("content", "") for msg in compressed)
        assert any("[ADVISORY]" in msg.get("content", "") for msg in compressed)

        # Step 4: Sync turn (non-blocking)
        memory_provider._memory_client.sync_turn = AsyncMock()
        turn_data = {
            "session_id": session_id,
            "turn_id": "turn_001",
            "user_message": "Fix the email validator bug",
            "assistant_message": "I'll fix the validator using TDD approach",
        }
        await memory_provider.sync_turn(turn_data)

        # Verify all components worked together
        memory_provider._memory_client.prefetch.assert_called_once()
        context_engine._engine_client.compile.assert_called_once()
        memory_provider._memory_client.sync_turn.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_vision_task(mock_hermes_home, mock_config):
    """End-to-end test: vision/document analysis task."""
    memory_provider = FormalCCMemoryProvider()
    context_engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await memory_provider.initialize(mock_config, mock_hermes_home)
        await context_engine.initialize(mock_config, mock_hermes_home)

        # Mock memory prefetch
        memory_provider._memory_client.prefetch = AsyncMock(
            return_value="Previous analysis: Focus on financial data"
        )

        # Mock compile for vision scene
        bundle = CompileBundle(
            scene="vision_doc",
            compiled_messages=[
                CompiledMessage(
                    role="system",
                    content="Analyze financial data in the document"
                )
            ],
        )
        context_engine._engine_client.compile = AsyncMock(return_value=bundle)

        session_id = "e2e_vision_001"

        # Prefetch memory
        memory_context = {
            "session_id": session_id,
            "query": "Analyze the quarterly report",
        }
        memory_block = await memory_provider.prefetch(memory_context)
        assert "financial" in memory_block.lower()

        # Compress with vision scene
        messages = [
            {"role": "user", "content": "Analyze this quarterly report"}
        ]
        compile_context = {
            "session_id": session_id,
            "document_id": "doc_q4_2025",
        }
        compressed = await context_engine.compress(messages, compile_context)

        assert len(compressed) > 0
        # Verify vision scene was used
        context_engine._engine_client.compile.assert_called_once()


@pytest.mark.asyncio
async def test_e2e_memory_tool_usage(mock_hermes_home, mock_config):
    """End-to-end test: model uses memory search tool."""
    memory_provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await memory_provider.initialize(mock_config, mock_hermes_home)

        # Mock runtime client
        memory_provider._runtime_client.memory_search = AsyncMock(
            return_value={
                "results": [
                    {"content": "Authentication uses JWT tokens"},
                    {"content": "Token expiry is 24 hours"},
                ]
            }
        )

        # Get tool schemas
        tools = memory_provider.get_tool_schemas()
        assert len(tools) == 2
        assert tools[0]["name"] == "cc_memory_search"

        # Simulate model calling the tool
        result = await memory_provider.handle_tool_call(
            "cc_memory_search",
            {"query": "authentication flow", "limit": 10}
        )

        assert "result" in result
        assert "results" in result["result"]
        assert len(result["result"]["results"]) == 2


@pytest.mark.asyncio
async def test_e2e_error_recovery(mock_hermes_home, mock_config):
    """End-to-end test: graceful error recovery."""
    memory_provider = FormalCCMemoryProvider()
    context_engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await memory_provider.initialize(mock_config, mock_hermes_home)
        await context_engine.initialize(mock_config, mock_hermes_home)

        # Simulate memory prefetch failure
        memory_provider._memory_client.prefetch = AsyncMock(return_value="")

        memory_context = {"session_id": "test", "query": "test"}
        memory_block = await memory_provider.prefetch(memory_context)

        # Should gracefully return None
        assert memory_block is None

        # Simulate compile failure
        context_engine._engine_client.compile = AsyncMock(return_value=None)

        messages = [{"role": "user", "content": "test"}]
        compile_context = {"session_id": "test"}
        compressed = await context_engine.compress(messages, compile_context)

        # Should return original messages
        assert compressed == messages


@pytest.mark.asyncio
async def test_e2e_multi_turn_conversation(mock_hermes_home, mock_config):
    """End-to-end test: multi-turn conversation with memory accumulation."""
    memory_provider = FormalCCMemoryProvider()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await memory_provider.initialize(mock_config, mock_hermes_home)

        memory_provider._memory_client.prefetch = AsyncMock(return_value="context")
        memory_provider._memory_client.sync_turn = AsyncMock()

        session_id = "multi_turn_session"

        # Turn 1
        await memory_provider.prefetch({
            "session_id": session_id,
            "query": "What is authentication?"
        })
        await memory_provider.sync_turn({
            "session_id": session_id,
            "turn_id": "turn_001",
            "user_message": "What is authentication?",
            "assistant_message": "Authentication verifies user identity",
        })

        # Turn 2
        await memory_provider.prefetch({
            "session_id": session_id,
            "query": "How does JWT work?"
        })
        await memory_provider.sync_turn({
            "session_id": session_id,
            "turn_id": "turn_002",
            "user_message": "How does JWT work?",
            "assistant_message": "JWT is a token-based auth mechanism",
        })

        # Turn 3
        await memory_provider.prefetch({
            "session_id": session_id,
            "query": "Show me an example"
        })

        # Verify turn counter incremented
        assert memory_provider._turn_counter == 3


@pytest.mark.asyncio
async def test_e2e_concurrent_operations(mock_hermes_home, mock_config):
    """End-to-end test: concurrent memory and compile operations."""
    import asyncio

    memory_provider = FormalCCMemoryProvider()
    context_engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await memory_provider.initialize(mock_config, mock_hermes_home)
        await context_engine.initialize(mock_config, mock_hermes_home)

        memory_provider._memory_client.prefetch = AsyncMock(return_value="memory")
        context_engine._engine_client.compile = AsyncMock(
            return_value=CompileBundle(
                scene="coding",
                compiled_messages=[
                    CompiledMessage(role="system", content="compiled")
                ]
            )
        )

        # Run operations concurrently
        memory_task = memory_provider.prefetch({
            "session_id": "concurrent",
            "query": "test"
        })
        compile_task = context_engine.compress(
            [{"role": "user", "content": "test"}],
            {"session_id": "concurrent"}
        )

        memory_result, compile_result = await asyncio.gather(
            memory_task, compile_task
        )

        assert memory_result == "memory"
        assert len(compile_result) > 0
