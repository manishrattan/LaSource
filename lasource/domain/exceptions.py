"""
LaSource Custom Exceptions Module

This module defines domain-specific exceptions for the LaSource AI Governance Framework.
All custom exceptions inherit from LaSourceException for easy catching and handling.

Exception Hierarchy:
- LaSourceException (base)
  - LaSourceConfigError (configuration issues)
  - LaSourceProviderError (AI provider connectivity/API errors)
  - LaSourceAuthenticationError (authentication/authorization failures)
  - LaSourceSecurityError (security policy violations)
  - LaSourceValidationError (request validation failures)
  - LaSourceHealthCheckError (health check failures)
"""


class LaSourceException(Exception):
    """Base exception for all LaSource errors."""
    
    def __init__(self, message: str, error_code: str = "LASOURCE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary for JSON response."""
        return {
            "error_code": self.error_code,
            "message": self.message
        }


class LaSourceConfigError(LaSourceException):
    """Raised when configuration is invalid or missing required environment variables."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="CONFIG_ERROR")


class LaSourceProviderError(LaSourceException):
    """Raised when there's an issue connecting to or calling an AI provider."""
    
    def __init__(self, message: str, provider_name: str = None):
        self.provider_name = provider_name
        full_message = f"Provider Error ({provider_name}): {message}" if provider_name else f"Provider Error: {message}"
        super().__init__(full_message, error_code="PROVIDER_ERROR")


class LaSourceAuthenticationError(LaSourceException):
    """Raised when JWT validation or authentication fails."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="AUTHENTICATION_ERROR")


class LaSourceSecurityError(LaSourceException):
    """Raised when a security policy violation is detected (PII, keywords, etc.)."""
    
    def __init__(self, message: str, violation_type: str = None):
        self.violation_type = violation_type
        full_message = f"Security Violation ({violation_type}): {message}" if violation_type else f"Security Violation: {message}"
        super().__init__(full_message, error_code="SECURITY_ERROR")


class LaSourceValidationError(LaSourceException):
    """Raised when request validation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="VALIDATION_ERROR")


class LaSourceHealthCheckError(LaSourceException):
    """Raised when health check fails for a provider."""
    
    def __init__(self, message: str, provider_name: str = None):
        self.provider_name = provider_name
        full_message = f"Health Check Failed ({provider_name}): {message}" if provider_name else f"Health Check Failed: {message}"
        super().__init__(full_message, error_code="HEALTH_CHECK_ERROR")


class LaSourceRateLimitError(LaSourceException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str, client_id: str = None):
        self.client_id = client_id
        full_message = f"Rate Limit Exceeded (Client: {client_id}): {message}" if client_id else f"Rate Limit Exceeded: {message}"
        super().__init__(full_message, error_code="RATE_LIMIT_ERROR")
