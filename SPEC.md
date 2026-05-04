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
