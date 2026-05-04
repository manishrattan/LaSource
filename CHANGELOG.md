# Changelog

All notable changes to LaSource are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-04

### Added

#### Exception Handling Architecture
- New `lasource/domain/exceptions.py` module with comprehensive exception hierarchy
- 8 custom exception classes for different error scenarios:
  - `LaSourceException` (base exception)
  - `LaSourceConfigError` - Configuration issues
  - `LaSourceProviderError` - Provider connectivity errors
  - `LaSourceAuthenticationError` - Authentication failures
  - `LaSourceSecurityError` - Security policy violations
  - `LaSourceValidationError` - Validation failures
  - `LaSourceHealthCheckError` - Health check failures
  - `LaSourceRateLimitError` - Rate limit exceeded
- Exception tracking with error codes and correlation IDs
- `to_dict()` method for JSON serialization of exceptions

#### Enhanced Core Components
- Updated `AbstractProvider` with `health_check()` abstract method
- Comprehensive error handling in all provider implementations
- Updated `ProviderFactory` with validation and proper exception handling
- Enhanced `ShieldMiddleware` with multi-layer exception handling
- Global exception handlers in FastAPI application
- Structured logging with correlation IDs throughout

#### Provider Improvements
- **Azure OpenAI Provider**:
  - Proper token retrieval with error handling
  - Health check implementation
  - Input validation for prompts
  - Response validation
  - Azure authentication error handling

- **Anthropic Provider**:
  - Stub implementation with proper error handling
  - Configuration validation
  - Clear error messages for not-yet-implemented features

#### Documentation
- New `LICENSE` file (MIT License)
- New `CONTRIBUTING.md` with comprehensive contributing guidelines
- Updated `README.md` with:
  - Quick start section
  - Installation instructions
  - Environment configuration guide
  - Usage examples
  - Testing instructions
  - Troubleshooting guide
  - Development workflow
- Updated `SPEC.md` with new "Error Handling & Exception Architecture" section
- New `QUICKSTART.md` for quick 5-minute setup
- New `.env.example` with all configuration options documented
- New `requirements.txt` with runtime dependencies
- New `requirements-dev.txt` with development dependencies

#### Security Enhancements
- Input validation at all entry points
- Safe error messages that don't expose internal details
- Proper logging without sensitive data
- Correlation IDs for end-to-end request tracing
- Rate limiting error handling

#### Logging Improvements
- Structured logging with context parameters
- Correlation IDs for request tracing
- Sanitized audit logs (no raw sensitive data)
- Proper error logging with stack traces
- Different log levels for different scenarios

### Changed
- Refactored middleware to use custom exceptions
- Improved FastAPI application setup with CORS, logging, and exception handlers
- Enhanced error responses to include correlation IDs
- Refactored provider implementations for consistent error handling

### Fixed
- Proper HTTP status code mapping for different error types
- Safe error responses without exposing internal implementation details
- Consistent error response format across all endpoints

### Security
- All exceptions properly caught and logged
- Sensitive data not exposed in error messages
- Correlation IDs for security audit trails
- Input validation on all public endpoints

## [0.9.0] - Initial Release (Pre-release)

### Added
- Initial LaSource framework structure
- Clean Architecture implementation
- Provider-agnostic interface with `AbstractProvider`
- PII scrubber and keyword blocker
- Rate limiting middleware
- JWT authentication validation
- Azure OpenAI provider stub
- React frontend with Vite
- Azure Bicep infrastructure templates

### Known Limitations
- Anthropic provider not fully implemented
- Gemini provider not implemented
- Cohere provider not implemented
- JWT validation is a stub (not validating against Azure AD keys)
- In-memory rate limiter (not distributed)

## Migration Guide

### From v0.9.0 to v1.0.0

#### Update Your Code

If you were catching generic `Exception`:

```python
# Old way
try:
    provider = ProviderFactory.get_provider()
except Exception as e:
    print(f"Error: {e}")

# New way
from lasource.domain.exceptions import LaSourceProviderError
try:
    provider = ProviderFactory.get_provider()
except LaSourceProviderError as e:
    print(f"Provider error: {e.message}")
```

#### Update Your Environment

Add the new recommended environment variables to your `.env`:

```bash
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
RATE_LIMIT_CAPACITY=100
RATE_LIMIT_REFILL_RATE=20.0
```

#### Update Your Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

#### No Database Migrations Needed

This release does not introduce any database changes.

## Future Roadmap

### v1.1.0 (Planned)
- Distributed rate limiting with Redis
- Full Anthropic provider implementation
- OpenTelemetry integration
- Database-backed audit logging
- Advanced JWT validation with Azure AD keys

### v1.2.0 (Planned)
- Gemini provider implementation
- Cohere provider implementation
- Request/response caching
- Enhanced monitoring and alerting
- Kubernetes deployment templates

### v2.0.0 (Long-term)
- GraphQL API
- WebSocket support for streaming responses
- Advanced analytics dashboard
- Custom provider SDK
- Enterprise authentication options

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/manishrattan/LaSource/issues
- Discussions: https://github.com/manishrattan/LaSource/discussions
- Documentation: See README.md and SPEC.md

## Acknowledgments

Thank you to all contributors who have helped make LaSource better!
