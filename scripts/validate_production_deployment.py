#!/usr/bin/env python3
"""
Production deployment validation script.
Comprehensive validation of production deployment including security, performance, and functionality.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def validate_secret_manager():
    """Validate Secret Manager configuration."""
    print("🔐 Validating Secret Manager...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        print("❌ GCP_PROJECT_ID not set")
        return False
    
    # Check secrets exist
    result = subprocess.run([
        'gcloud', 'secrets', 'list', '--filter=name:riv-basic-auth', '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to list secrets: {result.stderr}")
        return False
    
    secrets = json.loads(result.stdout)
    secret_names = [secret['name'].split('/')[-1] for secret in secrets]
    
    if 'riv-basic-auth-user' not in secret_names:
        print("❌ Username secret not found")
        return False
    
    if 'riv-basic-auth-pass' not in secret_names:
        print("❌ Password secret not found")
        return False
    
    print("✅ Secret Manager configuration valid")
    return True

def validate_cloud_run():
    """Validate Cloud Run service configuration."""
    print("🚀 Validating Cloud Run service...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("❌ GCP_PROJECT_ID not set")
        return False
    
    # Get service info
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region, '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get service info: {result.stderr}")
        return False
    
    service_info = json.loads(result.stdout)
    
    # Check service is ready
    if service_info['status']['conditions'][0]['status'] != 'True':
        print("❌ Service not ready")
        return False
    
    # Check environment variables
    env_vars = service_info['spec']['template']['spec']['containers'][0]['env']
    env_dict = {}
    for env in env_vars:
        if 'value' in env:
            env_dict[env['name']] = env['value']
        elif 'valueFrom' in env:
            env_dict[env['name']] = f"[SECRET: {env['valueFrom']['secretKeyRef']['name']}]"
    
    if env_dict.get('APP_ENVIRONMENT') != 'production':
        print("❌ APP_ENVIRONMENT not set to production")
        return False
    
    if env_dict.get('GCP_PROJECT_ID') != project_id:
        print("❌ GCP_PROJECT_ID incorrect")
        return False
    
    # Check secret references
    secret_refs = [env for env in env_vars if 'valueFrom' in env and 'secretKeyRef' in env.get('valueFrom', {})]
    if len(secret_refs) < 2:
        print("❌ Secret references not found")
        return False
    
    secret_names = [ref['valueFrom']['secretKeyRef']['name'] for ref in secret_refs]
    if 'riv-basic-auth-user' not in secret_names:
        print("❌ Username secret reference not found")
        return False
    
    if 'riv-basic-auth-pass' not in secret_names:
        print("❌ Password secret reference not found")
        return False
    
    print("✅ Cloud Run service configuration valid")
    return True

def validate_database_connectivity():
    """Validate database connectivity."""
    print("🗄️  Validating database connectivity...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("❌ GCP_PROJECT_ID not set")
        return False
    
    # Get service URL
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region, '--format=value(status.url)'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get service URL: {result.stderr}")
        return False
    
    service_url = result.stdout.strip()
    
    # Test health endpoint
    result = subprocess.run([
        'curl', '-f', f'{service_url}/health'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Health check failed: {result.stderr}")
        return False
    
    health_data = json.loads(result.stdout)
    if health_data['status'] != 'healthy':
        print(f"❌ Service not healthy: {health_data}")
        return False
    
    print("✅ Database connectivity valid")
    return True

def validate_authentication():
    """Validate authentication system."""
    print("🔒 Validating authentication...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("❌ GCP_PROJECT_ID not set")
        return False
    
    # Get service URL
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region, '--format=value(status.url)'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get service URL: {result.stderr}")
        return False
    
    service_url = result.stdout.strip()
    
    # Get credentials from Secret Manager
    username_result = subprocess.run([
        'gcloud', 'secrets', 'versions', 'access', 'latest',
        '--secret=riv-basic-auth-user'
    ], capture_output=True, text=True)
    
    password_result = subprocess.run([
        'gcloud', 'secrets', 'versions', 'access', 'latest',
        '--secret=riv-basic-auth-pass'
    ], capture_output=True, text=True)
    
    if username_result.returncode != 0:
        print("❌ Failed to get username from Secret Manager")
        return False
    
    if password_result.returncode != 0:
        print("❌ Failed to get password from Secret Manager")
        return False
    
    username = username_result.stdout.strip()
    password = password_result.stdout.strip()
    
    # Test authentication
    result = subprocess.run([
        'curl', '-u', f'{username}:{password}',
        f'{service_url}/api/assignments'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Authentication failed: {result.stderr}")
        return False
    
    # Test with wrong credentials
    result = subprocess.run([
        'curl', '-u', 'wrong:credentials',
        f'{service_url}/api/assignments'
    ], capture_output=True, text=True)
    
    # Should return error message
    if 'Incorrect username or password' not in result.stdout:
        print("❌ Authentication should fail with wrong credentials")
        return False
    
    print("✅ Authentication system valid")
    return True

def validate_security():
    """Validate security configuration."""
    print("🛡️  Validating security...")
    
    # Check for hardcoded credentials
    src_path = Path(__file__).parent.parent / 'src'
    for file_path in src_path.rglob('*.py'):
        with open(file_path, 'r') as f:
            content = f.read().lower()
            if 'password=' in content or 'admin123' in content:
                print(f"❌ Hardcoded credentials found in {file_path}")
                return False
    
    # Check environment variables
    sensitive_vars = ['APP_BASIC_AUTH_USER', 'APP_BASIC_AUTH_PASS', 'DATABASE_URL']
    for var in sensitive_vars:
        if var in os.environ:
            value = os.environ[var]
            if value.startswith('postgresql://') or value.startswith('admin'):
                print(f"❌ Sensitive {var} found in environment")
                return False
    
    # Check logs for sensitive data
    result = subprocess.run([
        'gcloud', 'logging', 'read',
        'resource.type="cloud_run_revision" AND resource.labels.service_name="riv-assignments"',
        '--limit=50', '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        logs = json.loads(result.stdout)
        for log_entry in logs:
            log_text = log_entry.get('textPayload', '')
            if 'password' in log_text.lower() or 'secret' in log_text.lower():
                print(f"❌ Sensitive data found in logs: {log_text}")
                return False
    
    print("✅ Security configuration valid")
    return True

def validate_performance():
    """Validate performance requirements."""
    print("⚡ Validating performance...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("❌ GCP_PROJECT_ID not set")
        return False
    
    # Get service URL
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region, '--format=value(status.url)'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get service URL: {result.stderr}")
        return False
    
    service_url = result.stdout.strip()
    
    # Test response time
    start_time = time.time()
    result = subprocess.run([
        'curl', '-f', f'{service_url}/health'
    ], capture_output=True, text=True)
    end_time = time.time()
    
    if result.returncode != 0:
        print(f"❌ Health check failed: {result.stderr}")
        return False
    
    response_time = end_time - start_time
    if response_time > 2.0:
        print(f"❌ Response time too slow: {response_time:.2f}s")
        return False
    
    print(f"✅ Performance valid (response time: {response_time:.2f}s)")
    return True

def validate_monitoring():
    """Validate monitoring configuration."""
    print("📊 Validating monitoring...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        print("❌ GCP_PROJECT_ID not set")
        return False
    
    # Check if monitoring is configured
    result = subprocess.run([
        'gcloud', 'monitoring', 'dashboards', 'list',
        '--filter=displayName:"RIV Assignments"',
        '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("⚠️  Monitoring dashboards not found")
    else:
        dashboards = json.loads(result.stdout)
        if len(dashboards) > 0:
            print("✅ Monitoring dashboards configured")
        else:
            print("⚠️  No monitoring dashboards found")
    
    # Check logging configuration
    result = subprocess.run([
        'gcloud', 'logging', 'read',
        'resource.type="cloud_run_revision" AND resource.labels.service_name="riv-assignments"',
        '--limit=1', '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("⚠️  Logging not configured")
    else:
        print("✅ Logging configured")
    
    return True

def main():
    """Main validation function."""
    print("🔍 RIV Assignment System - Production Deployment Validation")
    print("=" * 60)
    
    # Check prerequisites
    if not os.getenv('GCP_PROJECT_ID'):
        print("❌ GCP_PROJECT_ID environment variable not set")
        sys.exit(1)
    
    # Run all validations
    validations = [
        validate_secret_manager,
        validate_cloud_run,
        validate_database_connectivity,
        validate_authentication,
        validate_security,
        validate_performance,
        validate_monitoring
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        if validation():
            passed += 1
        else:
            print(f"❌ {validation.__name__} failed")
    
    print(f"\n📊 Validation Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All validations passed!")
        print("✅ Production deployment is ready")
        sys.exit(0)
    else:
        print("❌ Some validations failed")
        print("🔧 Please fix the issues before proceeding")
        sys.exit(1)

if __name__ == "__main__":
    main()
