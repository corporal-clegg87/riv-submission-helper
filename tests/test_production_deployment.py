#!/usr/bin/env python3
"""
Test production deployment for RIV Assignment System.
Validates Cloud Run deployment, environment configuration, and security.
"""

import os
import sys
import pytest
import subprocess
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api import app
from fastapi.testclient import TestClient

class TestProductionDeployment:
    """Test production deployment configuration."""
    
    def test_cloud_run_service_exists(self):
        """Test 1: Verify Cloud Run service is deployed."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Cloud Run service not found: {result.stderr}"
        
        service_info = json.loads(result.stdout)
        assert service_info['metadata']['name'] == 'riv-assignments', "Service name incorrect"
        assert service_info['status']['conditions'][0]['status'] == 'True', "Service not ready"
    
    def test_cloud_run_environment_variables(self):
        """Test 2: Verify environment variables are set correctly."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service info: {result.stderr}"
        
        service_info = json.loads(result.stdout)
        env_vars = service_info['spec']['template']['spec']['containers'][0]['env']
        
        # Check required environment variables
        env_dict = {env['name']: env['value'] for env in env_vars}
        
        assert 'APP_ENVIRONMENT' in env_dict, "APP_ENVIRONMENT not set"
        assert env_dict['APP_ENVIRONMENT'] == 'production', "APP_ENVIRONMENT not set to production"
        
        assert 'GCP_PROJECT_ID' in env_dict, "GCP_PROJECT_ID not set"
        assert env_dict['GCP_PROJECT_ID'] == project_id, "GCP_PROJECT_ID incorrect"
        
        assert 'DATABASE_URL' in env_dict, "DATABASE_URL not set"
        assert 'postgresql://' in env_dict['DATABASE_URL'], "DATABASE_URL not PostgreSQL"
    
    def test_cloud_run_secrets_configuration(self):
        """Test 3: Verify secrets are configured in Cloud Run."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service info: {result.stderr}"
        
        service_info = json.loads(result.stdout)
        env_vars = service_info['spec']['template']['spec']['containers'][0]['env']
        
        # Check for secret references
        secret_refs = [env for env in env_vars if 'secretKeyRef' in env]
        assert len(secret_refs) >= 2, "Secret references not found"
        
        # Check specific secret references
        secret_names = [ref['secretKeyRef']['name'] for ref in secret_refs]
        assert 'riv-basic-auth-user' in secret_names, "Username secret reference not found"
        assert 'riv-basic-auth-pass' in secret_names, "Password secret reference not found"
    
    def test_cloud_run_service_account(self):
        """Test 4: Verify service account is configured."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service info: {result.stderr}"
        
        service_info = json.loads(result.stdout)
        service_account = service_info['spec']['template']['spec']['serviceAccountName']
        
        assert service_account == f'riv-assignments-sa@{project_id}.iam.gserviceaccount.com', "Service account incorrect"
    
    def test_cloud_run_health_check(self):
        """Test 5: Verify health check endpoint responds."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Get service URL
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=value(status.url)'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service URL: {result.stderr}"
        service_url = result.stdout.strip()
        
        # Test health endpoint
        result = subprocess.run([
            'curl', '-f', f'{service_url}/health'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Health check failed: {result.stderr}"
        
        health_data = json.loads(result.stdout)
        assert health_data['status'] == 'healthy', "Health check not healthy"
    
    def test_cloud_run_authentication(self):
        """Test 6: Verify authentication works with secrets."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Get service URL
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=value(status.url)'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service URL: {result.stderr}"
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
        
        assert username_result.returncode == 0, "Failed to get username from Secret Manager"
        assert password_result.returncode == 0, "Failed to get password from Secret Manager"
        
        username = username_result.stdout.strip()
        password = password_result.stdout.strip()
        
        # Test authentication
        result = subprocess.run([
            'curl', '-u', f'{username}:{password}',
            f'{service_url}/api/assignments'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Authentication failed: {result.stderr}"
    
    def test_cloud_run_logs_clean(self):
        """Test 7: Verify no sensitive data in logs."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Check recent logs for sensitive data
        result = subprocess.run([
            'gcloud', 'logging', 'read',
            f'resource.type="cloud_run_revision" AND resource.labels.service_name="riv-assignments"',
            '--limit=50',
            '--format=json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to read logs: {result.stderr}"
        
        logs = json.loads(result.stdout)
        for log_entry in logs:
            log_text = log_entry.get('textPayload', '')
            assert 'password' not in log_text.lower(), "Password found in logs"
            assert 'secret' not in log_text.lower(), "Secret found in logs"
    
    def test_cloud_run_performance(self):
        """Test 8: Verify performance meets requirements."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Get service URL
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=value(status.url)'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service URL: {result.stderr}"
        service_url = result.stdout.strip()
        
        # Test response time
        start_time = time.time()
        result = subprocess.run([
            'curl', '-f', f'{service_url}/health'
        ], capture_output=True, text=True)
        end_time = time.time()
        
        assert result.returncode == 0, f"Health check failed: {result.stderr}"
        assert (end_time - start_time) < 2.0, "Response time too slow"
    
    def test_cloud_run_security_headers(self):
        """Test 9: Verify security headers are present."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Get service URL
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=value(status.url)'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service URL: {result.stderr}"
        service_url = result.stdout.strip()
        
        # Test headers
        result = subprocess.run([
            'curl', '-I', f'{service_url}/health'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get headers: {result.stderr}"
        
        headers = result.stdout.lower()
        assert 'https' in service_url, "Service not using HTTPS"
        assert 'x-frame-options' in headers or 'content-security-policy' in headers, "Security headers missing"
    
    def test_cloud_run_database_connectivity(self):
        """Test 10: Verify database connectivity from Cloud Run."""
        project_id = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION', 'us-central1')
        
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Get service URL
        result = subprocess.run([
            'gcloud', 'run', 'services', 'describe', 'riv-assignments',
            '--region', region,
            '--format=value(status.url)'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get service URL: {result.stderr}"
        service_url = result.stdout.strip()
        
        # Test health endpoint (which tests database connectivity)
        result = subprocess.run([
            'curl', '-f', f'{service_url}/health'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Health check failed: {result.stderr}"
        
        health_data = json.loads(result.stdout)
        assert health_data['status'] == 'healthy', "Database connectivity test failed"


class TestProductionSecurity:
    """Test production security configuration."""
    
    def test_no_hardcoded_credentials(self):
        """Test that no hardcoded credentials exist in code."""
        # Check source code for hardcoded credentials
        src_path = Path(__file__).parent.parent / 'src'
        
        for file_path in src_path.rglob('*.py'):
            with open(file_path, 'r') as f:
                content = f.read().lower()
                
                # Check for common hardcoded credential patterns
                assert 'password=' not in content, f"Hardcoded password found in {file_path}"
                assert 'admin123' not in content, f"Hardcoded password found in {file_path}"
                assert 'secret=' not in content, f"Hardcoded secret found in {file_path}"
    
    def test_environment_variables_secure(self):
        """Test that environment variables are properly configured."""
        # Check that sensitive environment variables are not set locally
        sensitive_vars = ['APP_BASIC_AUTH_USER', 'APP_BASIC_AUTH_PASS', 'DATABASE_URL']
        
        for var in sensitive_vars:
            if var in os.environ:
                # If set, should be using Secret Manager references
                value = os.environ[var]
                assert not value.startswith('postgresql://'), f"Sensitive {var} found in environment"
                assert not value.startswith('admin'), f"Sensitive {var} found in environment"
    
    def test_secret_manager_permissions(self):
        """Test Secret Manager permissions are correctly configured."""
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Check service account has Secret Manager access
        result = subprocess.run([
            'gcloud', 'projects', 'get-iam-policy', project_id,
            '--flatten=bindings[].members',
            '--format=json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get IAM policy: {result.stderr}"
        
        iam_policy = json.loads(result.stdout)
        service_account = f'serviceAccount:riv-assignments-sa@{project_id}.iam.gserviceaccount.com'
        
        # Check for Secret Manager access
        secret_access_found = False
        for binding in iam_policy.get('bindings', []):
            if binding['role'] == 'roles/secretmanager.secretAccessor':
                if service_account in binding['members']:
                    secret_access_found = True
                    break
        
        assert secret_access_found, "Service account missing Secret Manager access"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
