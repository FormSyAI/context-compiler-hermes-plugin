"""Tests for FormalCC Context Engine."""

import pytest
from unittest.mock import AsyncMock, patch

from plugins.context_engine.formalcc_engine.engine import FormalCCContextEngine
from shared.models import CompileBundle, CompiledMessage, Advisory


@pytest.mark.asyncio
async def test_engine_initialization(mock_hermes_home, mock_config):
    """Test engine initialization."""
    engine = FormalCCContextEngine()

    assert engine.name == "formalcc-engine"

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

    assert engine._config is not None


def test_should_compress():
    """Test compression decision logic."""
    engine = FormalCCContextEngine()

    # Should compress when over threshold
    assert engine.should_compress([], token_count=1000, threshold=500)

    # Should not compress when under threshold
    assert not engine.should_compress([], token_count=300, threshold=500)


@pytest.mark.asyncio
async def test_compress_success(mock_hermes_home, mock_config, sample_messages, sample_compile_bundle):
    """Test successful context compression."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        # Mock the compile response
        bundle = CompileBundle(**sample_compile_bundle)
        engine._engine_client.compile = AsyncMock(return_value=bundle)

        context = {
            "session_id": "test_session",
            "repo_id": "org/repo",
        }

        result = await engine.compress(sample_messages, context)

        assert len(result) > 0
        assert result[0]["role"] == "system"


@pytest.mark.asyncio
async def test_compress_failure_graceful(mock_hermes_home, mock_config, sample_messages):
    """Test graceful handling of compression failure."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        # Mock failure
        engine._engine_client.compile = AsyncMock(return_value=None)

        context = {"session_id": "test_session"}
        result = await engine.compress(sample_messages, context)

        # Should return original messages on failure
        assert result == sample_messages


@pytest.mark.asyncio
async def test_compress_with_focus_topic(mock_hermes_home, mock_config, sample_messages, sample_compile_bundle):
    """Test compression with focus topic."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        bundle = CompileBundle(**sample_compile_bundle)
        engine._engine_client.compile = AsyncMock(return_value=bundle)

        context = {"session_id": "test_session"}
        result = await engine.compress(
            sample_messages,
            context,
            focus_topic="validators.py regex"
        )

        assert len(result) > 0
        engine._engine_client.compile.assert_called_once()


@pytest.mark.asyncio
async def test_update_from_response(mock_hermes_home, mock_config):
    """Test state update from response."""
    engine = FormalCCContextEngine()

    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        await engine.initialize(mock_config, mock_hermes_home)

        response = {"content": "test"}
        context = {"session_id": "test_session"}

        await engine.update_from_response(response, context)

        assert engine._session_id == "test_session"
        assert engine._turn_counter == 1
