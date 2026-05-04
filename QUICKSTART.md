# LaSource Quick Start Guide

Welcome to LaSource! This guide will help you get up and running quickly.

## 5-Minute Setup

### 1. Clone and Install

```bash
git clone https://github.com/manishrattan/LaSource.git
cd LaSource

# Create Python environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
npm install
```

### 2. Configure

```bash
cp .env.example .env

# Edit .env and set:
# LA_SOURCE_PROVIDER=azure-openai
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

### 3. Run

```bash
# Terminal 1: Start backend
uvicorn src.lavoie.application.main:app --reload

# Terminal 2: Start frontend (new terminal)
npm run dev
```

### 4. Verify

```bash
curl -H "Authorization: Bearer test-token" \
  http://localhost:8000/healthz
```

## Folder Structure Explained

```
LaSource/
├── lasource/               # Core domain logic
│   ├── domain/            # Business logic (no external deps)
│   │   ├── exceptions.py  # All error types
│   │   └── provider.py    # Provider interface
│   ├── middleware/        # FastAPI middleware
│   │   └── shield.py      # Security layer
│   └── providers/         # AI provider implementations
│       ├── azure_openai.py
│       └── anthropic_provider.py
├── src/                   # Application layer
│   └── lavoie/
│       ├── application/   # FastAPI app
│       └── infrastructure/
├── tests/                 # Test suite
├── README.md              # Full documentation
├── CONTRIBUTING.md        # Contribution guidelines
└── SPEC.md               # Architecture specification
```

## Common Tasks

### Run Tests

```bash
pytest tests/ -v
```

### Check Code Quality

```bash
black lasource/ src/
flake8 lasource/ src/
mypy lasource/ src/
```

### Add a New Provider

1. Create `lasource/providers/my_provider.py`
2. Inherit from `AbstractProvider`
3. Implement `generate_response()` and `health_check()`
4. Register in `ProviderFactory.SUPPORTED_PROVIDERS`
5. Add tests and documentation

See [CONTRIBUTING.md](./CONTRIBUTING.md) for detailed instructions.

### View API Documentation

After running the server, visit:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

## Exception Handling

LaSource uses custom exceptions for consistent error handling:

```python
from lasource.domain.exceptions import (
    LaSourceProviderError,
    LaSourceAuthenticationError,
    LaSourceSecurityError
)

try:
    provider = ProviderFactory.get_provider()
except LaSourceProviderError as e:
    print(f"Provider error: {e.message}")
except LaSourceAuthenticationError as e:
    print(f"Auth error: {e.message}")
```

## Environment Variables

### Required
- `LA_SOURCE_PROVIDER`: The AI provider to use
- `LA_SOURCE_MODEL`: Model name
- `AZURE_OPENAI_ENDPOINT`: For Azure OpenAI (if using)

### Optional
- `LOG_LEVEL`: Logging level (default: INFO)
- `CORS_ORIGINS`: Allowed CORS origins
- `RATE_LIMIT_CAPACITY`: Rate limit tokens (default: 100)

See `.env.example` for all options.

## Troubleshooting

### Port Already in Use

```bash
# Use different port
uvicorn main:app --port 8001
```

### Module Not Found

```bash
# Make sure you're in the venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Authentication Errors

```bash
# Make sure your Azure credentials are configured
az account show
```

### PII Detection Issues

Edit `lasource/middleware/shield.py` to adjust patterns or keywords.

## Next Steps

1. **Read the docs**: Check [README.md](./README.md) for full documentation
2. **Explore code**: Look at examples in `tests/` directory
3. **Contribute**: See [CONTRIBUTING.md](./CONTRIBUTING.md) to contribute
4. **Deploy**: Review [SPEC.md](./SPEC.md) for deployment options

## Need Help?

- GitHub Issues: https://github.com/manishrattan/LaSource/issues
- Discussions: https://github.com/manishrattan/LaSource/discussions
- Documentation: Check README.md and SPEC.md

## License

LaSource is released under the [MIT License](./LICENSE).

---

Happy coding! 🚀
