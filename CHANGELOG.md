# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - Phase 3
- Integration tests for memory prefetch injection, scene routing, tool dispatch
- End-to-end tests simulating full Hermes agent scenarios
- API reference documentation (docs/API.md)
- Usage examples (examples/usage_examples.py)
- Test coverage for concurrent operations
- Session lifecycle tests
- Profile isolation tests

### Improved
- Test coverage increased to 74% (from 72%)
- Total test count: 63 tests (all passing)
- Documentation completeness

## [0.3.0] - 2026-04-20

### Added
- Integration tests for all key scenarios
  - Memory prefetch injection
  - Scene routing (coding/vision/general)
  - Tool dispatch (sequential and concurrent)
  - Focus topic support
  - Graceful degradation
  - Profile isolation
  - Session lifecycle
  - Advisory injection
- End-to-end tests simulating full Hermes agent loop
  - Coding task with memory and context compression
  - Vision/document analysis task
  - Memory tool usage
  - Error recovery
  - Multi-turn conversation
  - Concurrent operations
- API reference documentation (`docs/API.md`)
- Usage examples (`examples/usage_examples.py`)

### Improved
- Test coverage increased to 74%
- Total test count: 63 tests (100% passing)

## [0.2.0] - 2026-04-20



### Added
- Initial implementation of formalcc-memory provider
- Initial implementation of formalcc-engine context engine
- Shared runtime client for FormalCC Runtime API
- Memory prefetch, sync, and session management
- Context compilation with scene routing
- Memory tools (cc_memory_search, cc_memory_profile)
- Configuration management with env var overrides
- CLI commands for diagnostics
- Graceful degradation on API unavailability
- Unit tests for core components
- Documentation and README files

### Features
- Memory Provider
  - Prefetch memory before model calls
  - Async turn synchronization
  - Session end handling
  - Memory search and profile tools

- Context Engine
  - Context compilation via Runtime API
  - Server-side scene routing (coding/vision/general)
  - Focus topic support
  - Advisory message injection
  - Graceful fallback to original messages

- Shared Components
  - HTTP client with auth and error handling
  - Pydantic models for API contracts
  - Configuration management
  - Utility functions

### Documentation
- Comprehensive design document
- Installation and usage guide
- Plugin-specific READMEs
- Test suite with fixtures

[0.1.0]: https://github.com/your-org/formalcc-hermes-plugin/releases/tag/v0.1.0
