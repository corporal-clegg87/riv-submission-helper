# Agent Rules

## Secret Management

**NEVER hardcode secrets in source code.** Use Secret Manager or environment variables.

### Allowed Locations
- `tests/` - Mark with `TEST_` prefix
- `docs/` - Mark with `EXAMPLE_` prefix  
- `scripts/` - Mark with `EXAMPLE_` prefix
- `config/` - Mark with `EXAMPLE_` prefix

### Blocked Locations
- `src/`, `api/`, `core/`, `lib/` - Main application code
- Production deployment files

### Secret Management Pattern
```python
# ✅ CORRECT - Use environment variables
username = os.getenv('APP_BASIC_AUTH_USER')
password = os.getenv('APP_BASIC_AUTH_PASS')

# ✅ CORRECT - Use Secret Manager
credentials = get_secret_manager_credentials()

# ✅ CORRECT - Test data
TEST_USERNAME = "test_admin"
EXAMPLE_PASSWORD = "example_pass"

# ❌ WRONG - Hardcoded in source
username = "riv_admin_2024"
password = "secret_password"
```

### Environment Variables
- Development: `APP_BASIC_AUTH_USER`, `APP_BASIC_AUTH_PASS`
- Production: Use Secret Manager with IAM
- Testing: Use `TEST_` prefixed variables

### Validation
- Check for hardcoded secrets in code reviews
- Use Secret Manager in production
- Environment variables for local development
- Test credentials clearly marked
