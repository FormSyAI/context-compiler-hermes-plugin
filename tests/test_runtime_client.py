"""Tests for Runtime API client."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from shared.runtime_client import RuntimeClient
from shared.models import MemoryPrefetchRequest, CompileRequest
from shared.errors import RuntimeAPIError, TimeoutError as FormalCCTimeoutError


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    client = RuntimeClient(
        base_url="https://api.formsy.ai",
        api_key_env="FORMALCC_API_KEY",
        timeout_s=30,
    )

    assert client.base_url == "https://api.formsy.ai"
    assert client.timeout_s == 30


@pytest.mark.asyncio
async def test_memory_prefetch_success(sample_memory_prefetch_response):
    """Test successful memory prefetch."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai")

        async with client:
            # Mock the HTTP client
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: sample_memory_prefetch_response
            mock_response.content = b"test"
            mock_response.raise_for_status = lambda: None

            client._client.request = AsyncMock(return_value=mock_response)

            request = MemoryPrefetchRequest(
                workspace_id="ws_test",
                session_id="sess_123",
                turn_id="turn_001",
                query="test query",
            )

            response = await client.memory_prefetch(request)

            assert response.memory_block == "Test memory content"
            assert response.retrieved_count == 5


@pytest.mark.asyncio
async def test_compile_success(sample_compile_bundle):
    """Test successful compile."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai")

        async with client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {"bundle": sample_compile_bundle}
            mock_response.content = b"test"
            mock_response.raise_for_status = lambda: None

            client._client.request = AsyncMock(return_value=mock_response)

            request = CompileRequest(
                workspace_id="ws_test",
                session_id="sess_123",
                turn_id="turn_001",
            )

            response = await client.compile(request)

            assert response.bundle.scene == "coding"
            assert len(response.bundle.compiled_messages) == 1


@pytest.mark.asyncio
async def test_request_timeout():
    """Test request timeout handling."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai", timeout_s=1)

        async with client:
            client._client.request = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

            request = MemoryPrefetchRequest(
                workspace_id="ws_test",
                session_id="sess_123",
                turn_id="turn_001",
                query="test",
            )

            with pytest.raises(FormalCCTimeoutError):
                await client.memory_prefetch(request)


@pytest.mark.asyncio
async def test_request_401_error():
    """Test 401 authentication error."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai")

        async with client:
            mock_response = AsyncMock()
            mock_response.status_code = 401

            client._client.request = AsyncMock(return_value=mock_response)

            request = MemoryPrefetchRequest(
                workspace_id="ws_test",
                session_id="sess_123",
                turn_id="turn_001",
                query="test",
            )

            with pytest.raises(RuntimeAPIError) as exc_info:
                await client.memory_prefetch(request)

            assert exc_info.value.status_code == 401
