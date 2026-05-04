# LaSource Product Specification

## Executive Summary
LaSource is an enterprise-grade AI Governance Framework that acts as a secure reverse-proxy (Shield) between internal applications and external Generative AI providers. By intercepting all inbound and outbound traffic, it acts as a centralized enforcement point for security, compliance, telemetry, and observability.

LaSource allows organizations to adopt multiple top-tier models (Azure OpenAI, Anthropic, Gemini, Cohere) without duplicating the security engineering effort. The client applications are isolated from provider logic by a strictly implemented **Clean Architecture**. This platform is 100% Open Source, meaning organizations and developers can confidently build and monetize their own GenAI proxy businesses or enterprise SaaS products on top of LaSource.

## Architecture & Tenets
1. **Clean Architecture / Dependency Inversion**:
   - The Core Domain (PII Scrubbing, Validation) has zero external dependencies.
   - The Application Layer (FastAPI Shield Middleware) orchestrates but does not know how to generate content.
   - The Infrastructure Layer (Provider Factory, Key Vault client) deals with external state and APIs.
2. **Zero-Trust Networking**: 
   - Public network access to the backing AI models is explicitly disabled (e.g. `publicNetworkAccess: "Disabled"` in Azure Bicep).
   - Only Private Endpoints and Private Links within the designated VNETs can access the resources.
3. **Provider-Agnostic Interface**:
   - `ILLMProvider / AbstractProvider` manages all vendor specifics.
   - Adding a new vendor to the enterprise portfolio requires one class implementation in `lavoie.infrastructure` and NO updates to the client applications.

## Feature Set

### 1. Unified Authentication & Edge Protection
- **Azure Entra ID Mapping**: Validates inbound enterprise JWT tokens and maps identity before allowing traffic downstream to any vendor.
- **Rate Limiting**: Protects downstream inference engines from being overwhelmed. Limits are enforced at the Shield level.

### 2. The PII Scrubber (Data Loss Prevention)
- **Inline Sanitization Pipeline**: Driven by the `PIIScrubber` domain service.
- **Regex Detectors**:
  - `EMAIL`: Replaces all emails with `[REDACTED EMAIL]`
  - `SSN`: Detects and removes Social Security Numbers.
  - `CREDIT_CARD`: Detects and hides PANs.
  - `PHONE`: Automatically obscures phone numbers.
- **Keyword Deny List**: Prevents restricted internal terms (e.g., `top secret`, `internal_use_only`) from accidentally escaping the company network via prompts. Immediate HTTP 400 rejection upon detection.

### 3. Native Telemetry & Audit Store
- **X-Correlation-ID Generation**: Generates and attaches a UUID correlation header to all requests and traces.
- **OpenTelemetry Standardized**: Uses Semantic Conventions (e.g., `gen_ai.request.model`) across all vendors uniformly.
- **Persistent Audit Pipeline**: Streams scrubbed payloads and outputs to a centralized log store (like Azure Application Insights or an OpenSearch cluster) using asynchronous thread-safe logging. 

### 4. Dynamic Provider Routing & Secret Management
- **The Provider Factory**: Evaluates `LA_SOURCE_PROVIDER` at runtime, hot-switching between backend APIs.
- **Cloud-Native Secrets**: Uses Azure `SecretClient` (`azure.keyvault.secrets`) securely fetching `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, and `COHERE_API_KEY` from Key Vault using Default Azure Credentials (Managed Identity), falling back to local Environment Variables.

### 5. Liveness Probing & Health Architecture
- **/healthz**: Standardized check indicating whether the configured underlying AI Provider is reachable and responsive, resolving to HTTP 200 or 503.

## Deployment Stack
- **Web App / Client Viewer**: React + Vite Front-End
- **Proxy**: FastAPI (Python) running ASGI on Uvicorn
- **Infrastructure as Code (IaC)**: Azure Bicep templates for provisioning the AI workspace and Private Endpoints.
- **CI/CD**: GitHub Actions workflows configured for strict scanning and compliant deployment.

## Error Handling & Exception Architecture

LaSource implements a comprehensive exception hierarchy for consistent error handling across all layers:

### Exception Types

#### 1. **LaSourceException** (Base)
- Base exception for all LaSource errors
- All custom exceptions inherit from this class
- Provides `to_dict()` method for JSON serialization
- Includes `error_code` and `message` properties

#### 2. **LaSourceConfigError**
- **When Raised:** Configuration is invalid or missing required environment variables
- **HTTP Status:** 500
- **Example:** `AZURE_OPENAI_ENDPOINT` not set, unsupported provider selected
- **Resolution:** Check environment variables and configuration files

#### 3. **LaSourceProviderError**
- **When Raised:** Issues connecting to or calling an AI provider
- **HTTP Status:** 502 (Bad Gateway)
- **Examples:**
  - Provider API is unreachable
  - Authentication with provider fails
  - API response is malformed
- **Resolution:** Check network connectivity, credentials, and provider status

#### 4. **LaSourceAuthenticationError**
- **When Raised:** JWT validation or Azure Entra ID authentication fails
- **HTTP Status:** 403 (Forbidden)
- **Examples:**
  - Missing authorization header
  - Expired or invalid JWT token
  - Insufficient permissions
- **Resolution:** Provide valid Azure Entra ID JWT token with proper claims

#### 5. **LaSourceSecurityError**
- **When Raised:** Security policy violations detected
- **HTTP Status:** 400 (Bad Request)
- **Examples:**
  - PII data detected in request
  - Forbidden keywords found
  - Rate limit exceeded
- **Resolution:** Sanitize request, remove sensitive data, retry after rate limit window

#### 6. **LaSourceValidationError**
- **When Raised:** Request validation fails
- **HTTP Status:** 400 (Bad Request)
- **Examples:**
  - Empty prompt
  - Missing required fields
  - Invalid data format
- **Resolution:** Validate input and retry with correct data

#### 7. **LaSourceHealthCheckError**
- **When Raised:** Health check for a provider fails
- **HTTP Status:** 503 (Service Unavailable)
- **Examples:**
  - Provider is unreachable
  - Provider response timeout
- **Resolution:** Check provider status and network connectivity

#### 8. **LaSourceRateLimitError**
- **When Raised:** Rate limit is exceeded
- **HTTP Status:** 429 (Too Many Requests)
- **Resolution:** Reduce request frequency and retry after delay

### Error Response Format

All errors follow a consistent JSON format:

```json
{
  "error_code": "PROVIDER_ERROR",
  "message": "Provider error message",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Exception Handling in Middleware

The Shield Middleware implements multi-layer exception handling:

1. **Rate Limiting Layer**: Catches and handles `LaSourceRateLimitError`
2. **Authentication Layer**: Catches and handles `LaSourceAuthenticationError`
3. **Security Layer**: Catches and handles `LaSourceSecurityError`
4. **Provider Layer**: Catches and handles `LaSourceProviderError`
5. **Global Handler**: Catches all unexpected exceptions and returns safe error response

### Exception Handling in Providers

Each provider implementation must:

1. Validate input parameters before processing
2. Catch provider-specific exceptions
3. Convert provider errors to LaSource exceptions
4. Include provider name in error context
5. Log errors with full stack traces (DEBUG level)

Example:

```python
def generate_response(self, prompt: str) -> str:
    """Generate response with proper exception handling."""
    if not prompt or not prompt.strip():
        raise LaSourceValidationError("Prompt cannot be empty")
    
    try:
        response = self.client.call_api(prompt)
        return response
    except ProviderTimeoutError as e:
        raise LaSourceProviderError(
            f"Request timed out: {str(e)}",
            provider_name="azure-openai"
        )
    except ProviderAuthError as e:
        raise LaSourceProviderError(
            f"Authentication failed: {str(e)}",
            provider_name="azure-openai"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise LaSourceProviderError(
            f"Unexpected error: {str(e)}",
            provider_name="azure-openai"
        )
```

### Logging Strategy

LaSource implements structured logging with correlation IDs:

```python
# Error logging
logger.error(
    "ProviderError",
    extra={
        "correlation_id": correlation_id,
        "provider": "azure-openai",
        "error": str(exception)
    },
    exc_info=True  # Include full stack trace
)

# Info logging (sanitized)
logger.info(
    "RequestProcessed",
    extra={
        "correlation_id": correlation_id,
        "status": "success",
        "response_length": len(response)
    }
)
```

### Error Recovery Strategies

#### Transient Errors (Retry-able)
- Network timeouts: Retry with exponential backoff
- Rate limits: Retry after delay
- Temporary provider outages: Retry after delay

#### Permanent Errors (Non-retry-able)
- Configuration errors: Fix configuration and restart
- Authentication failures: Fix credentials
- Invalid requests: Fix input data

### Best Practices for Error Handling

1. **Always provide context**: Include correlation IDs and provider names
2. **Never expose internal details**: Return safe error messages to clients
3. **Log everything**: Use correlation IDs to trace requests end-to-end
4. **Fail fast**: Validate input early and reject invalid requests
5. **Handle edge cases**: Consider null values, timeouts, and network errors
6. **Test error paths**: Include negative test cases for all error scenarios
