"""Additional tests to improve code coverage for low-coverage modules."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from shared.error_handler import ErrorHandler, ErrorRecovery
from shared.errors import RuntimeAPIError, TimeoutError as FormalCCTimeoutError
from shared.config_validator import ConfigValidator, ConfigGenerator
from shared.resilience import CircuitBreaker, CircuitBreakerConfig, CircuitState, async_retry
from shared.utils import generate_turn_id, validate_workspace_id, validate_tenant_id
from shared.runtime_client import RuntimeClient
from shared.models import MemorySyncTurnRequest, SessionEndRequest


# ============================================================
# error_handler.py - 403, 404, 429, 503, 500, ConnectionError
# ============================================================

class TestErrorHandlerExtended:

    def test_403_message(self):
        error = RuntimeAPIError("Forbidden", status_code=403)
        msg = ErrorHandler.get_user_friendly_message(error)
        assert "forbidden" in msg.lower()
        assert "workspace" in msg.lower()

    def test_404_message(self):
        error = RuntimeAPIError("Not found", status_code=404)
        msg = ErrorHandler.get_user_friendly_message(error)
        assert "not found" in msg.lower()
        assert "base_url" in msg.lower()

    def test_429_message(self):
        error = RuntimeAPIError("Rate limited", status_code=429)
        msg = ErrorHandler.get_user_friendly_message(error)
        assert "rate limit" in msg.lower()

    def test_503_message(self):
        error = RuntimeAPIError("Service unavailable", status_code=503)
        msg = ErrorHandler.get_user_friendly_message(error)
        assert "unavailable" in msg.lower()

    def test_500_message(self):
        error = RuntimeAPIError("Server error", status_code=500)
        msg = ErrorHandler.get_user_friendly_message(error)
        assert "server error" in msg.lower()

    def test_connection_error_message(self):
        error = ConnectionError("Connection refused")
        msg = ErrorHandler.get_user_friendly_message(error)
        assert "connection" in msg.lower()
        assert "network" in msg.lower()

    def test_unknown_error_message(self):
        error = ValueError("Something unexpected")
        msg = ErrorHandler.get_user_friendly_message(error)
        assert "error occurred" in msg.lower()

    def test_recovery_suggestions_503(self):
        error = RuntimeAPIError("Service unavailable", status_code=503)
        suggestions = ErrorHandler.get_recovery_suggestions(error)
        assert len(suggestions) > 0
        assert any("60" in s for s in suggestions)

    def test_recovery_suggestions_500(self):
        error = RuntimeAPIError("Server error", status_code=500)
        suggestions = ErrorHandler.get_recovery_suggestions(error)
        assert len(suggestions) > 0

    def test_recovery_suggestions_timeout(self):
        error = FormalCCTimeoutError("Timeout")
        suggestions = ErrorHandler.get_recovery_suggestions(error)
        assert len(suggestions) > 0
        assert any("FORMALCC_TIMEOUT" in s for s in suggestions)

    def test_recovery_suggestions_unknown(self):
        error = ValueError("Unknown")
        suggestions = ErrorHandler.get_recovery_suggestions(error)
        assert suggestions == []

    def test_handle_error_with_context(self, capsys):
        error = RuntimeAPIError("Unauthorized", status_code=401)
        ErrorHandler.handle_error(error, context="memory prefetch")
        captured = capsys.readouterr()
        assert "memory prefetch" in captured.out

    def test_handle_error_without_context(self, capsys):
        error = FormalCCTimeoutError("Timeout")
        ErrorHandler.handle_error(error)
        captured = capsys.readouterr()
        assert "Error" in captured.out

    def test_should_retry_connection_error(self):
        error = ConnectionError("Connection refused")
        assert ErrorRecovery.should_retry(error, 0, 3)

    def test_should_retry_500(self):
        error = RuntimeAPIError("Server error", status_code=500)
        assert ErrorRecovery.should_retry(error, 0, 3)

    def test_should_retry_502(self):
        error = RuntimeAPIError("Bad gateway", status_code=502)
        assert ErrorRecovery.should_retry(error, 0, 3)

    def test_should_retry_504(self):
        error = RuntimeAPIError("Gateway timeout", status_code=504)
        assert ErrorRecovery.should_retry(error, 0, 3)

    def test_should_not_retry_unknown(self):
        error = ValueError("Unknown")
        assert not ErrorRecovery.should_retry(error, 0, 3)

    def test_retry_delay_exponential_growth(self):
        error = FormalCCTimeoutError("Timeout")
        d0 = ErrorRecovery.get_retry_delay(error, 0)
        d1 = ErrorRecovery.get_retry_delay(error, 1)
        d2 = ErrorRecovery.get_retry_delay(error, 2)
        assert d1 > d0
        assert d2 > d1

    def test_retry_delay_max_cap(self):
        error = FormalCCTimeoutError("Timeout")
        delay = ErrorRecovery.get_retry_delay(error, 100)
        assert delay <= 30.0

    def test_rate_limit_delay_max_cap(self):
        error = RuntimeAPIError("Rate limited", status_code=429)
        delay = ErrorRecovery.get_retry_delay(error, 100)
        assert delay <= 60.0


# ============================================================
# config_validator.py - generate_config_file with overrides
# ============================================================

class TestConfigGeneratorExtended:

    def test_generate_config_file_with_overrides(self, tmp_path):
        import json
        config_file = tmp_path / "config.json"
        ConfigGenerator.generate_config_file(
            config_file,
            overrides={"workspace_id": "ws_custom", "timeout_s": 60}
        )
        with open(config_file) as f:
            config = json.load(f)
        assert config["workspace_id"] == "ws_custom"
        assert config["timeout_s"] == 60
        assert config["base_url"] == "https://api.formsy.ai"

    def test_generate_config_file_creates_parent_dirs(self, tmp_path):
        config_file = tmp_path / "nested" / "dir" / "config.json"
        ConfigGenerator.generate_config_file(config_file)
        assert config_file.exists()

    def test_validate_config_missing_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = ConfigValidator.validate_config({
                "api_key_env": "FORMALCC_API_KEY",
                "base_url": "https://api.formsy.ai",
            })
        assert any("API key" in w for w in result.warnings)

    def test_validate_config_trailing_slash_url(self):
        result = ConfigValidator.validate_base_url("https://api.formsy.ai/")
        assert result.valid
        assert any("/" in w for w in result.warnings)

    def test_validate_config_localhost_http(self):
        result = ConfigValidator.validate_base_url("http://localhost:8080")
        assert result.valid
        assert len(result.warnings) == 0

    def test_validate_timeout_long_warning(self):
        result = ConfigValidator.validate_timeout(200)
        assert result.valid
        assert any("long" in w for w in result.warnings)

    def test_validate_empty_workspace_id(self):
        result = ConfigValidator.validate_workspace_id("")
        assert not result.valid

    def test_validate_empty_api_key(self):
        result = ConfigValidator.validate_api_key("")
        assert not result.valid
        assert any("required" in e for e in result.errors)

    def test_validate_empty_base_url(self):
        result = ConfigValidator.validate_base_url("")
        assert not result.valid


# ============================================================
# resilience.py - HALF_OPEN → CLOSED, async_retry
# ============================================================

class TestResilienceExtended:

    def test_circuit_breaker_half_open_to_closed(self):
        """Test HALF_OPEN transitions to CLOSED after enough successes."""
        cb = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout_seconds=0,
        ))

        # Force open
        def fail(): raise RuntimeError("fail")
        with pytest.raises(RuntimeError):
            cb.call(fail)
        assert cb.state.state == CircuitState.OPEN

        # Force half-open by backdating last_failure_time
        from datetime import datetime, timedelta
        cb.state.last_failure_time = datetime.now() - timedelta(seconds=10)

        # Two successes should close it
        def succeed(): return "ok"
        cb.call(succeed)
        assert cb.state.state == CircuitState.HALF_OPEN
        cb.call(succeed)
        assert cb.state.state == CircuitState.CLOSED

    def test_circuit_breaker_half_open_failure_reopens(self):
        """Test HALF_OPEN transitions back to OPEN on failure."""
        cb = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=1,
            success_threshold=2,
            timeout_seconds=0,
        ))

        def fail(): raise RuntimeError("fail")

        # Open the circuit
        with pytest.raises(RuntimeError):
            cb.call(fail)

        # Backdate to trigger half-open
        from datetime import datetime, timedelta
        cb.state.last_failure_time = datetime.now() - timedelta(seconds=10)

        # Fail in half-open → back to open
        with pytest.raises(RuntimeError):
            cb.call(fail)
        assert cb.state.state == CircuitState.OPEN

    def test_circuit_breaker_get_state(self):
        cb = CircuitBreaker()
        state = cb.get_state()
        assert state["state"] == "closed"
        assert state["failure_count"] == 0
        assert state["last_failure"] is None

    def test_circuit_breaker_open_raises_immediately(self):
        from shared.resilience import CircuitBreakerOpenError
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))

        def fail(): raise RuntimeError("fail")
        with pytest.raises(RuntimeError):
            cb.call(fail)

        # Now open - should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(fail)

    @pytest.mark.asyncio
    async def test_async_retry_success(self):
        """Test async_retry succeeds on first try."""
        async def succeed():
            return "ok"

        result = await async_retry(succeed, max_retries=2, base_delay=0.01)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_async_retry_eventual_success(self):
        """Test async_retry succeeds after retries."""
        attempts = []

        async def eventually():
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("not yet")
            return "ok"

        result = await async_retry(eventually, max_retries=3, base_delay=0.01)
        assert result == "ok"
        assert len(attempts) == 3

    @pytest.mark.asyncio
    async def test_async_retry_all_fail(self):
        """Test async_retry raises after all retries exhausted."""
        async def always_fail():
            raise RuntimeError("always")

        with pytest.raises(RuntimeError):
            await async_retry(always_fail, max_retries=2, base_delay=0.01)


# ============================================================
# utils.py - generate_turn_id, validate_workspace_id, validate_tenant_id
# ============================================================

class TestUtilsExtended:

    def test_generate_turn_id_format(self):
        turn_id = generate_turn_id("sess_abc", 1)
        assert turn_id == "sess_abc_turn_0001"

    def test_generate_turn_id_padding(self):
        turn_id = generate_turn_id("sess_abc", 42)
        assert turn_id == "sess_abc_turn_0042"

    def test_validate_workspace_id_none(self):
        result = validate_workspace_id(None)
        assert result == "ws_default"

    def test_validate_workspace_id_empty(self):
        result = validate_workspace_id("")
        assert result == "ws_default"

    def test_validate_workspace_id_valid(self):
        result = validate_workspace_id("ws_custom")
        assert result == "ws_custom"

    def test_validate_tenant_id_none(self):
        result = validate_tenant_id(None)
        assert result is None

    def test_validate_tenant_id_value(self):
        result = validate_tenant_id("acme")
        assert result == "acme"


# ============================================================
# runtime_client.py - memory_sync_turn, session_end
# ============================================================

@pytest.mark.asyncio
async def test_runtime_client_memory_sync_turn():
    """Test memory_sync_turn endpoint."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai")

        async with client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {}
            mock_response.content = b""
            mock_response.raise_for_status = lambda: None
            client._client.request = AsyncMock(return_value=mock_response)

            request = MemorySyncTurnRequest(
                workspace_id="ws_test",
                session_id="sess_123",
                turn_id="turn_001",
                user_message="Hello",
                assistant_message="Hi there",
            )

            await client.memory_sync_turn(request)
            client._client.request.assert_called_once()


@pytest.mark.asyncio
async def test_runtime_client_session_end():
    """Test session_end endpoint."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai")

        async with client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {}
            mock_response.content = b""
            mock_response.raise_for_status = lambda: None
            client._client.request = AsyncMock(return_value=mock_response)

            request = SessionEndRequest(
                workspace_id="ws_test",
                session_id="sess_123",
            )

            await client.session_end(request)
            client._client.request.assert_called_once()


@pytest.mark.asyncio
async def test_runtime_client_memory_search():
    """Test memory_search endpoint."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai")

        async with client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = lambda: {"results": ["item1"]}
            mock_response.content = b'{"results": ["item1"]}'
            mock_response.raise_for_status = lambda: None
            client._client.request = AsyncMock(return_value=mock_response)

            result = await client.memory_search(
                workspace_id="ws_test",
                session_id="sess_123",
                query="authentication",
                limit=5,
            )

            assert result["results"] == ["item1"]


@pytest.mark.asyncio
async def test_runtime_client_403_error():
    """Test 403 error handling."""
    with patch.dict("os.environ", {"FORMALCC_API_KEY": "fsy_test_123"}):
        client = RuntimeClient(base_url="https://api.formsy.ai")

        async with client:
            mock_response = AsyncMock()
            mock_response.status_code = 403
            mock_response.content = b"Forbidden"
            mock_response.raise_for_status = lambda: None
            client._client.request = AsyncMock(return_value=mock_response)

            from shared.errors import RuntimeAPIError
            with pytest.raises(RuntimeAPIError) as exc_info:
                from shared.models import MemoryPrefetchRequest
                await client.memory_prefetch(MemoryPrefetchRequest(
                    workspace_id="ws_test",
                    session_id="sess_123",
                    turn_id="turn_001",
                    query="test",
                ))
            assert exc_info.value.status_code == 403


# ============================================================
# memory client.py - sync_turn, session_end
# ============================================================

@pytest.mark.asyncio
async def test_memory_client_sync_turn_success():
    """Test MemoryClient.sync_turn success."""
    from plugins.memory.formalcc_memory.client import MemoryClient

    mock_runtime = AsyncMock()
    mock_runtime.memory_sync_turn = AsyncMock()

    client = MemoryClient(mock_runtime)
    await client.sync_turn(
        workspace_id="ws_test",
        session_id="sess_123",
        turn_id="turn_001",
        user_message="Hello",
        assistant_message="Hi",
    )

    mock_runtime.memory_sync_turn.assert_called_once()


@pytest.mark.asyncio
async def test_memory_client_sync_turn_failure():
    """Test MemoryClient.sync_turn handles failure gracefully."""
    from plugins.memory.formalcc_memory.client import MemoryClient

    mock_runtime = AsyncMock()
    mock_runtime.memory_sync_turn = AsyncMock(side_effect=RuntimeError("fail"))

    client = MemoryClient(mock_runtime)
    # Should not raise
    await client.sync_turn(
        workspace_id="ws_test",
        session_id="sess_123",
        turn_id="turn_001",
        user_message="Hello",
        assistant_message="Hi",
    )


@pytest.mark.asyncio
async def test_memory_client_prefetch_success():
    """Test MemoryClient.prefetch success."""
    from plugins.memory.formalcc_memory.client import MemoryClient
    from shared.models import MemoryPrefetchResponse

    mock_runtime = AsyncMock()
    mock_runtime.memory_prefetch = AsyncMock(
        return_value=MemoryPrefetchResponse(
            memory_block="Test memory",
            retrieved_count=3,
            elapsed_ms=50,
        )
    )

    client = MemoryClient(mock_runtime)
    result = await client.prefetch(
        workspace_id="ws_test",
        session_id="sess_123",
        turn_id="turn_001",
        query="test query",
    )

    assert result == "Test memory"


@pytest.mark.asyncio
async def test_memory_client_prefetch_with_hints():
    """Test MemoryClient.prefetch with hints."""
    from plugins.memory.formalcc_memory.client import MemoryClient
    from shared.models import MemoryPrefetchResponse

    mock_runtime = AsyncMock()
    mock_runtime.memory_prefetch = AsyncMock(
        return_value=MemoryPrefetchResponse(
            memory_block="Coding context",
            retrieved_count=5,
            elapsed_ms=80,
        )
    )

    client = MemoryClient(mock_runtime)
    result = await client.prefetch(
        workspace_id="ws_test",
        session_id="sess_123",
        turn_id="turn_001",
        query="fix bug",
        hints={"scene": "coding", "repo_id": "org/repo"},
    )

    assert result == "Coding context"
    call_args = mock_runtime.memory_prefetch.call_args
    assert call_args[0][0].hints == {"scene": "coding", "repo_id": "org/repo"}
