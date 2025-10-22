# Secret Manager Authentication Testing Guide

This guide explains how to test the Secret Manager authentication feature in both development and production environments.

## 🔧 Environment Configuration

### Development Environment
- **Purpose**: Local development and testing
- **Authentication**: Uses environment variables (`APP_BASIC_AUTH_USER`, `APP_BASIC_AUTH_PASS`)
- **Secret Manager**: Not required, falls back to env vars
- **Database**: SQLite (default) or local PostgreSQL

### Production Environment  
- **Purpose**: Cloud Run deployment with secure credential management
- **Authentication**: Uses Google Cloud Secret Manager
- **Fallback**: Environment variables if Secret Manager fails
- **Database**: Cloud SQL PostgreSQL

## 🧪 Testing Strategies

### 1. Development Testing (Local)

#### Setup Development Environment
```bash
# 1. Set up environment variables (no Secret Manager needed)
export APP_BASIC_AUTH_USER="dev_admin"
export APP_BASIC_AUTH_PASS="dev_password_123"
export APP_ENVIRONMENT="development"

# 2. Run the application
python server.py
```

#### Test Authentication in Development
```bash
# Test basic authentication
curl -u dev_admin:dev_password_123 http://localhost:8000/api/assignments

# Test web interface
curl -u dev_admin:dev_password_123 http://localhost:8000/

# Test with wrong credentials (should fail)
curl -u wrong_user:wrong_pass http://localhost:8000/api/assignments
```

#### Run Unit Tests
```bash
# Run all tests (mocked Secret Manager)
pytest tests/ -v

# Run specific Secret Manager tests
pytest tests/test_secret_manager.py -v

# Run API tests with authentication
pytest tests/test_api.py -v
```

### 2. Production Testing (Cloud Run)

#### Prerequisites
```bash
# 1. Set up GCP project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID

# 2. Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# 3. Create secrets (run setup script)
python scripts/setup_secret_manager.py
```

#### Test Secret Manager Setup
```bash
# Test Secret Manager configuration
python scripts/test_secret_manager_setup.py

# Test production deployment validation
python scripts/validate_production_deployment.py
```

#### Test Authentication in Production
```bash
# Get production URL
PROD_URL="https://your-service-url.run.app"

# Test authentication with Secret Manager credentials
curl -u riv_admin_2024:$(gcloud secrets versions access latest --secret=riv-basic-auth-pass) $PROD_URL/api/assignments

# Test web interface
curl -u riv_admin_2024:$(gcloud secrets versions access latest --secret=riv-basic-auth-pass) $PROD_URL/
```

## 🔍 Detailed Testing Scenarios

### Scenario 1: Development Environment Testing

**Goal**: Verify fallback to environment variables works correctly

```bash
# 1. Start application without GCP_PROJECT_ID
unset GCP_PROJECT_ID
python server.py

# 2. Test authentication
curl -u dev_admin:dev_password_123 http://localhost:8000/health
# Expected: 200 OK

curl -u dev_admin:dev_password_123 http://localhost:8000/api/assignments  
# Expected: 200 OK with assignments list

# 3. Test wrong credentials
curl -u wrong:wrong http://localhost:8000/api/assignments
# Expected: 401 Unauthorized
```

### Scenario 2: Production Environment Testing

**Goal**: Verify Secret Manager integration works correctly

```bash
# 1. Deploy to Cloud Run with GCP_PROJECT_ID set
gcloud run deploy riv-assignments \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars GCP_PROJECT_ID=$GCP_PROJECT_ID

# 2. Test Secret Manager access
python scripts/test_secret_manager_setup.py
# Expected: All tests pass

# 3. Test production authentication
curl -u riv_admin_2024:$(gcloud secrets versions access latest --secret=riv-basic-auth-pass) \
  https://your-service-url.run.app/api/assignments
# Expected: 200 OK
```

### Scenario 3: Fallback Testing

**Goal**: Verify graceful fallback when Secret Manager fails

```bash
# 1. Temporarily break Secret Manager access
gcloud secrets remove-iam-policy-binding riv-basic-auth-user \
  --member="serviceAccount:riv-assignments-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 2. Test fallback behavior
curl -u riv_admin_2024:fallback_password https://your-service-url.run.app/api/assignments
# Expected: Should fall back to environment variables or fail gracefully

# 3. Restore access
gcloud secrets add-iam-policy-binding riv-basic-auth-user \
  --member="serviceAccount:riv-assignments-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 🚀 Automated Testing

### Run All Tests
```bash
# Development tests (mocked Secret Manager)
pytest tests/ -v --tb=short

# Production tests (requires GCP setup)
pytest tests/test_secret_manager.py -v
pytest tests/test_production_deployment.py -v
```

### Test Credential Caching
```bash
# Test caching behavior
python -c "
import time
from src.api import get_secret_manager_credentials

# First call (should hit Secret Manager)
start = time.time()
creds1 = get_secret_manager_credentials()
print(f'First call: {time.time() - start:.3f}s')

# Second call (should use cache)
start = time.time()
creds2 = get_secret_manager_credentials()
print(f'Second call: {time.time() - start:.3f}s')

print(f'Credentials match: {creds1 == creds2}')
"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Secret Manager Not Available in Development
```
Error: Failed to initialize Secret Manager client
Solution: This is expected in development. The app will fall back to environment variables.
```

#### 2. Authentication Fails in Production
```bash
# Check Secret Manager access
gcloud secrets versions access latest --secret=riv-basic-auth-user
gcloud secrets versions access latest --secret=riv-basic-auth-pass

# Check service account permissions
gcloud projects get-iam-policy $GCP_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:riv-assignments-sa@$GCP_PROJECT_ID.iam.gserviceaccount.com"
```

#### 3. Caching Issues
```bash
# Clear credential cache (restart application)
# Or wait 5 minutes for TTL to expire
```

### Debug Logging

Enable debug logging to see credential source:
```bash
export LOG_LEVEL=DEBUG
python server.py
```

Look for these log messages:
- `"Using cached credentials"` - Cache hit
- `"Using Secret Manager credentials"` - Secret Manager used
- `"Using environment variable credentials"` - Fallback to env vars

## 📊 Monitoring in Production

### Health Checks
```bash
# Basic health check (no auth required)
curl https://your-service-url.run.app/health

# Authenticated health check
curl -u riv_admin_2024:$(gcloud secrets versions access latest --secret=riv-basic-auth-pass) \
  https://your-service-url.run.app/api/assignments
```

### Log Monitoring
```bash
# View application logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"

# Filter for authentication logs
gcloud logging read "resource.type=cloud_run_revision AND textPayload:\"credentials\"" \
  --limit=20
```

## ✅ Testing Checklist

### Development Testing
- [ ] Application starts without GCP_PROJECT_ID
- [ ] Authentication works with environment variables
- [ ] All unit tests pass
- [ ] Wrong credentials return 401
- [ ] Caching works correctly

### Production Testing  
- [ ] Secret Manager secrets exist
- [ ] Service account has proper permissions
- [ ] Authentication works with Secret Manager
- [ ] Fallback works when Secret Manager fails
- [ ] Performance is acceptable (caching reduces API calls)
- [ ] Logs show correct credential source

### Integration Testing
- [ ] End-to-end email processing works
- [ ] Web interface loads with authentication
- [ ] API endpoints respond correctly
- [ ] Database operations work
- [ ] Error handling is graceful

This testing approach ensures your Secret Manager authentication works correctly in both development and production environments! 🎯
