"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path


@pytest.fixture
def mock_hermes_home(tmp_path):
    """Create a temporary Hermes home directory."""
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    return hermes_home


@pytest.fixture
def mock_config():
    """Mock configuration dictionary."""
    return {
        "formalcc": {
            "base_url": "https://api.formsy.ai",
            "api_key_env": "FORMALCC_API_KEY",
            "workspace_id": "ws_test",
            "timeout_s": 30,
        }
    }


@pytest.fixture
def mock_runtime_client():
    """Mock RuntimeClient."""
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock()
    return client


@pytest.fixture
def sample_memory_prefetch_response():
    """Sample memory prefetch response."""
    return {
        "memory_block": "Test memory content",
        "retrieved_count": 5,
        "elapsed_ms": 100,
    }


@pytest.fixture
def sample_compile_bundle():
    """Sample compile bundle."""
    return {
        "scene": "coding",
        "compiled_messages": [
            {"role": "system", "content": "Focus on validators.py"},
        ],
        "evidence_units": [],
        "supported_claims": [],
        "advisory": {
            "recommended_action": "patch",
            "rationale_tail": "Prefer minimal changes",
        },
        "metrics": {"elapsed_ms": 150},
    }


@pytest.fixture
def sample_messages():
    """Sample OpenAI-style messages."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Fix the bug in validators.py"},
        {"role": "assistant", "content": "I'll help you fix that."},
    ]
