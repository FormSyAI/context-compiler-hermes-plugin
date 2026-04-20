# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-20

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
