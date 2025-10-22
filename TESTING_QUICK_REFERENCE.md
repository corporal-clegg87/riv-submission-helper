# Secret Manager Testing Quick Reference

## 🚀 Quick Start Commands

### Development Testing
```bash
# 1. Set up dev environment
export APP_BASIC_AUTH_USER="dev_admin"
export APP_BASIC_AUTH_PASS="dev_password_123"
unset GCP_PROJECT_ID  # Ensure no GCP project set

# 2. Start application
python server.py

# 3. Test authentication
curl -u dev_admin:dev_password_123 http://localhost:8000/api/assignments
```

### Production Testing
```bash
# 1. Set up production environment
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# 2. Test Secret Manager setup
python scripts/test_secret_manager_setup.py

# 3. Test production deployment
python scripts/validate_production_deployment.py
```

## 🔍 Key Differences

| Aspect | Development | Production |
|--------|-------------|------------|
| **Credential Source** | Environment variables | Secret Manager |
| **GCP_PROJECT_ID** | Not set | Required |
| **Database** | SQLite/PostgreSQL | Cloud SQL |
| **Authentication** | `APP_BASIC_AUTH_*` | Secret Manager secrets |
| **Caching** | 5-minute TTL | 5-minute TTL |
| **Fallback** | N/A | Env vars if Secret Manager fails |

## 🧪 Test Commands

### Unit Tests
```bash
# All tests (mocked Secret Manager)
pytest tests/ -v

# Secret Manager specific tests
pytest tests/test_secret_manager.py -v

# API authentication tests
pytest tests/test_api.py -v
```

### Integration Tests
```bash
# Test Secret Manager setup
python scripts/test_secret_manager_setup.py

# Test production deployment
python scripts/validate_production_deployment.py

# Test credential caching
python -c "
from src.api import get_secret_manager_credentials
import time
start = time.time()
creds = get_secret_manager_credentials()
print(f'Credential fetch: {time.time() - start:.3f}s')
"
```

### Manual Testing
```bash
# Development
curl -u dev_admin:dev_password_123 http://localhost:8000/api/assignments

# Production
curl -u riv_admin_2024:$(gcloud secrets versions access latest --secret=riv-basic-auth-pass) \
  https://your-service-url.run.app/api/assignments
```

## 🐛 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `ImportError: No module named 'google.cloud'` | Install: `pip install google-cloud-secret-manager` |
| `Failed to initialize Secret Manager client` | Expected in dev, app falls back to env vars |
| `401 Unauthorized` | Check credentials match Secret Manager values |
| `Secret not found` | Run `python scripts/setup_secret_manager.py` |
| Slow authentication | Check credential caching (5min TTL) |

## 📊 Monitoring Commands

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit=20

# Test health endpoint
curl https://your-service-url.run.app/health

# Check Secret Manager access
gcloud secrets versions access latest --secret=riv-basic-auth-user
gcloud secrets versions access latest --secret=riv-basic-auth-pass
```

## ✅ Testing Checklist

### Development
- [ ] App starts without `GCP_PROJECT_ID`
- [ ] Auth works with env vars
- [ ] All tests pass
- [ ] Wrong creds return 401

### Production
- [ ] Secret Manager secrets exist
- [ ] Service account has permissions
- [ ] Auth works with Secret Manager
- [ ] Fallback works when Secret Manager fails
- [ ] Performance is good (caching works)

### Both
- [ ] Web interface loads
- [ ] API endpoints work
- [ ] Error handling is graceful
- [ ] Logs show correct credential source
