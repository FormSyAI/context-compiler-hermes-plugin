"""Tests for Phase 2 enhancements."""

import pytest
from pathlib import Path
from shared.config_validator import ConfigValidator, ConfigGenerator
from shared.resilience import CircuitBreaker, CircuitState, RetryStrategy
from shared.error_handler import ErrorHandler, ErrorRecovery
from shared.errors import RuntimeAPIError, TimeoutError as FormalCCTimeoutError


class TestConfigValidator:
    """Tests for configuration validation."""

    def test_validate_api_key_valid(self):
        """Test valid API key validation."""
        result = ConfigValidator.validate_api_key("fsy_live_abc123def456ghi789")
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_api_key_invalid_format(self):
        """Test invalid API key format."""
        result = ConfigValidator.validate_api_key("invalid_key")
        assert not result.valid
        assert any("format" in error.lower() for error in result.errors)

    def test_validate_api_key_too_short(self):
        """Test API key too short."""
        result = ConfigValidator.validate_api_key("fsy_live_short")
        assert not result.valid

    def test_validate_api_key_test_warning(self):
        """Test warning for test API key."""
        result = ConfigValidator.validate_api_key("fsy_test_abc123def456ghi789")
        assert result.valid
        assert len(result.warnings) > 0

    def test_validate_base_url_valid(self):
        """Test valid base URL."""
        result = ConfigValidator.validate_base_url("https://api.formsy.ai")
        assert result.valid

    def test_validate_base_url_invalid(self):
        """Test invalid base URL."""
        result = ConfigValidator.validate_base_url("not-a-url")
        assert not result.valid

    def test_validate_base_url_http_warning(self):
        """Test warning for HTTP URL."""
        result = ConfigValidator.validate_base_url("http://api.example.com")
        assert result.valid
        assert len(result.warnings) > 0

    def test_validate_timeout_valid(self):
        """Test valid timeout."""
        result = ConfigValidator.validate_timeout(30)
        assert result.valid

    def test_validate_timeout_invalid(self):
        """Test invalid timeout."""
        result = ConfigValidator.validate_timeout(-5)
        assert not result.valid

    def test_validate_timeout_warning_short(self):
        """Test warning for short timeout."""
        result = ConfigValidator.validate_timeout(2)
        assert result.valid
        assert len(result.warnings) > 0

    def test_validate_workspace_id_valid(self):
        """Test valid workspace ID."""
        result = ConfigValidator.validate_workspace_id("ws_default")
        assert result.valid

    def test_validate_workspace_id_warning(self):
        """Test warning for workspace ID without prefix."""
        result = ConfigValidator.validate_workspace_id("default")
        assert result.valid
        assert len(result.warnings) > 0


class TestConfigGenerator:
    """Tests for configuration generation."""

    def test_generate_default_config(self):
        """Test default config generation."""
        config = ConfigGenerator.generate_default_config()
        assert config["base_url"] == "https://api.formsy.ai"
        assert config["workspace_id"] == "ws_default"
        assert config["timeout_s"] == 30

    def test_generate_config_file(self, tmp_path):
        """Test config file generation."""
        config_file = tmp_path / "test-config.json"
        ConfigGenerator.generate_config_file(config_file)
        assert config_file.exists()

        import json
        with open(config_file) as f:
            config = json.load(f)
        assert "base_url" in config

    def test_generate_env_template(self, tmp_path):
        """Test .env template generation."""
        env_file = tmp_path / ".env"
        ConfigGenerator.generate_env_template(env_file)
        assert env_file.exists()

        content = env_file.read_text()
        assert "FORMALCC_API_KEY" in content


class TestCircuitBreaker:
    """Tests for circuit breaker."""

    def test_circuit_breaker_closed_initially(self):
        """Test circuit breaker starts closed."""
        cb = CircuitBreaker()
        assert cb.state.state == CircuitState.CLOSED

    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures."""
        cb = CircuitBreaker()

        def failing_func():
            raise RuntimeError("Test error")

        # Trigger failures
        for _ in range(5):
            with pytest.raises(RuntimeError):
                cb.call(failing_func)

        assert cb.state.state == CircuitState.OPEN

    def test_circuit_breaker_success_resets_count(self):
        """Test successful call resets failure count."""
        cb = CircuitBreaker()

        def success_func():
            return "success"

        # Some failures
        def failing_func():
            raise RuntimeError("Test error")

        for _ in range(2):
            with pytest.raises(RuntimeError):
                cb.call(failing_func)

        # Success resets
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state.failure_count == 0


class TestRetryStrategy:
    """Tests for retry strategy."""

    def test_retry_strategy_success_first_try(self):
        """Test successful call on first try."""
        strategy = RetryStrategy(max_retries=3)

        def success_func():
            return "success"

        result = strategy.execute(success_func)
        assert result == "success"

    def test_retry_strategy_eventual_success(self):
        """Test eventual success after retries."""
        strategy = RetryStrategy(max_retries=3, base_delay=0.01)
        attempts = []

        def eventually_succeeds():
            attempts.append(1)
            if len(attempts) < 3:
                raise RuntimeError("Not yet")
            return "success"

        result = strategy.execute(eventually_succeeds)
        assert result == "success"
        assert len(attempts) == 3

    def test_retry_strategy_all_failures(self):
        """Test all retries fail."""
        strategy = RetryStrategy(max_retries=2, base_delay=0.01)

        def always_fails():
            raise RuntimeError("Always fails")

        with pytest.raises(RuntimeError):
            strategy.execute(always_fails)


class TestErrorHandler:
    """Tests for error handler."""

    def test_get_user_friendly_message_401(self):
        """Test user-friendly message for 401 error."""
        error = RuntimeAPIError("Unauthorized", status_code=401)
        message = ErrorHandler.get_user_friendly_message(error)
        assert "Authentication failed" in message
        assert "API key" in message

    def test_get_user_friendly_message_timeout(self):
        """Test user-friendly message for timeout."""
        error = FormalCCTimeoutError("Request timed out")
        message = ErrorHandler.get_user_friendly_message(error)
        assert "timed out" in message.lower()
        assert "network" in message.lower()

    def test_get_recovery_suggestions_401(self):
        """Test recovery suggestions for 401 error."""
        error = RuntimeAPIError("Unauthorized", status_code=401)
        suggestions = ErrorHandler.get_recovery_suggestions(error)
        assert len(suggestions) > 0
        assert any("validate" in s.lower() for s in suggestions)


class TestErrorRecovery:
    """Tests for error recovery."""

    def test_should_retry_timeout(self):
        """Test retry decision for timeout."""
        error = FormalCCTimeoutError("Timeout")
        assert ErrorRecovery.should_retry(error, 0, 3)
        assert not ErrorRecovery.should_retry(error, 3, 3)

    def test_should_retry_503(self):
        """Test retry decision for 503 error."""
        error = RuntimeAPIError("Service unavailable", status_code=503)
        assert ErrorRecovery.should_retry(error, 0, 3)

    def test_should_not_retry_401(self):
        """Test no retry for 401 error."""
        error = RuntimeAPIError("Unauthorized", status_code=401)
        assert not ErrorRecovery.should_retry(error, 0, 3)

    def test_get_retry_delay_rate_limit(self):
        """Test retry delay for rate limit."""
        error = RuntimeAPIError("Rate limited", status_code=429)
        delay = ErrorRecovery.get_retry_delay(error, 0)
        assert delay >= 5.0

    def test_get_retry_delay_exponential(self):
        """Test exponential backoff."""
        error = FormalCCTimeoutError("Timeout")
        delay1 = ErrorRecovery.get_retry_delay(error, 0)
        delay2 = ErrorRecovery.get_retry_delay(error, 1)
        assert delay2 > delay1
