# TODO

Remaining work for FormalCC Hermes Plugin after Phase 1-3.

## Phase 4: Enterprise Features & PyPI Release

### Packaging & Distribution
- [ ] Bump version to `0.2.0` in `pyproject.toml`
- [ ] Add `MANIFEST.in` for non-Python files (plugin.yaml, README.md)
- [ ] Configure PyPI publishing via GitHub Actions
- [ ] Create `.github/workflows/publish.yml` for automated releases
- [ ] Add `python-semantic-release` for automated versioning
- [ ] Test `pip install formalcc-hermes-plugin` from PyPI

### GitHub Actions CI/CD
- [ ] Create `.github/workflows/ci.yml` for test runs on PRs
- [ ] Add matrix testing for Python 3.10, 3.11, 3.12, 3.13
- [ ] Add coverage reporting (codecov or similar)
- [ ] Add linting step (ruff, black --check)
- [ ] Add type checking step (mypy)

### Hermes Integration Testing
- [ ] Set up Hermes Agent locally for integration testing
- [ ] Test `hermes plugins install` flow end-to-end
- [ ] Verify memory prefetch is injected correctly in Hermes loop
- [ ] Verify context engine is called at correct token threshold
- [ ] Verify memory tools appear in model tool list
- [ ] Test `hermes formalcc-memory doctor` against live Runtime API
- [ ] Validate plugin.yaml schema against Hermes plugin loader

### Enterprise Features
- [ ] OAuth2 token support (in addition to API key)
- [ ] mTLS support for on-premise deployments
- [ ] Audit logging for all API calls
- [ ] Rate limiting with configurable quotas
- [ ] Metrics export (Prometheus/OpenTelemetry)
- [ ] Health check endpoint for Kubernetes liveness probes

### Performance
- [ ] Benchmark memory prefetch latency (target: < 200ms p99)
- [ ] Benchmark compile latency (target: < 500ms p99)
- [ ] Add connection pooling to RuntimeClient
- [ ] Add response caching for repeated queries
- [ ] Profile memory usage under load

## Code Coverage Improvements

### Low Coverage Files (< 60%)
- [ ] `plugins/memory/formalcc_memory/client.py` (39%) - add unit tests for sync_turn and session_end
- [ ] `shared/error_handler.py` (51%) - add tests for 403, 404, 429, 503 messages
- [ ] `shared/config_validator.py` (64%) - add tests for generate_config_file with overrides

### Medium Coverage Files (60-80%)
- [ ] `plugins/memory/formalcc_memory/provider.py` (74%) - add tests for save_config, get_config_schema
- [ ] `shared/resilience.py` (71%) - add tests for HALF_OPEN → CLOSED transition and async_retry
- [ ] `shared/runtime_client.py` (81%) - add tests for memory_sync_turn, session_end endpoints

### Target
- [ ] Increase overall coverage from 74% to 85%+

## Documentation

- [ ] Add architecture diagram (Mermaid or PNG) to README.md
- [ ] Add sequence diagram for memory prefetch flow
- [ ] Add sequence diagram for context compression flow
- [ ] Add troubleshooting FAQ section to USAGE.md
- [ ] Add migration guide for upgrading between versions
- [ ] Add `docs/DEPLOYMENT.md` for production deployment guide
- [ ] Add `docs/SECURITY.md` for security best practices

## Compatibility

- [ ] Test against Hermes 0.9.x
- [ ] Test against Hermes 1.0.x
- [ ] Add compatibility matrix to README.md
- [ ] Add deprecation warnings for breaking config changes
- [ ] Add `hermes formalcc-memory migrate` command for config migration

## Known Issues

- [ ] `plugins/memory/formalcc_memory/cli.py` - `status_command` import chain needs cleanup
- [ ] `shared/utils.py` - `generate_turn_id` and `truncate_text` uncovered (58%)
- [ ] Circuit breaker state is in-memory only - does not persist across restarts
- [ ] No retry on `memory_sync_turn` failures (fire-and-forget by design, but should log)
