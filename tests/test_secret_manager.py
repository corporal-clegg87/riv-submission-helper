#!/usr/bin/env python3
"""
Test Secret Manager integration for RIV Assignment System.
Validates secret creation, access, and application integration.
"""

import os
import sys
import pytest
import subprocess
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api import app, settings
from fastapi.testclient import TestClient

class TestSecretManager:
    """Test Secret Manager integration."""
    
    def test_secret_manager_credentials_exist(self):
        """Test 1: Verify secrets exist in Secret Manager."""
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Check if secrets exist
        result = subprocess.run([
            'gcloud', 'secrets', 'list', 
            '--filter=name:riv-basic-auth',
            '--format=json'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to list secrets: {result.stderr}"
        
        secrets = json.loads(result.stdout)
        secret_names = [secret['name'].split('/')[-1] for secret in secrets]
        
        assert 'riv-basic-auth-user' in secret_names, "Username secret not found"
        assert 'riv-basic-auth-pass' in secret_names, "Password secret not found"
    
    def test_secret_manager_access(self):
        """Test 2: Verify service account can access secrets."""
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Test username secret access
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest',
            '--secret=riv-basic-auth-user'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to access username secret: {result.stderr}"
        assert result.stdout.strip() == "riv_admin_2024", "Username secret incorrect"  # EXAMPLE_USERNAME
        
        # Test password secret access
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest',
            '--secret=riv-basic-auth-pass'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to access password secret: {result.stderr}"
        assert len(result.stdout.strip()) > 20, "Password secret too short"
    
    def test_secret_manager_iam_permissions(self):
        """Test 3: Verify IAM permissions for secrets."""
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Check username secret IAM
        result = subprocess.run([
            'gcloud', 'secrets', 'get-iam-policy', 'riv-basic-auth-user'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get IAM policy: {result.stderr}"
        assert 'roles/secretmanager.secretAccessor' in result.stdout, "Missing secret accessor role"
        assert f'serviceAccount:riv-assignments-sa@{project_id}.iam.gserviceaccount.com' in result.stdout, "Service account not found in IAM"
        
        # Check password secret IAM
        result = subprocess.run([
            'gcloud', 'secrets', 'get-iam-policy', 'riv-basic-auth-pass'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to get IAM policy: {result.stderr}"
        assert 'roles/secretmanager.secretAccessor' in result.stdout, "Missing secret accessor role"
        assert f'serviceAccount:riv-assignments-sa@{project_id}.iam.gserviceaccount.com' in result.stdout, "Service account not found in IAM"
    
    def test_application_health_check(self):
        """Test 4: Health check endpoint works without authentication."""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data["status"] == "healthy", "Health check not healthy"
        assert "timestamp" in data, "Missing timestamp in health response"
    
    def test_admin_authentication_with_secrets(self):
        """Test 5: Admin authentication with Secret Manager credentials."""
        # Mock Secret Manager client
        with patch('src.api.get_secret_manager_credentials') as mock_get_creds:
            mock_get_creds.return_value = ("TEST_ADMIN", "TEST_PASSWORD")
            
            client = TestClient(app)
            
            # Test successful authentication
            response = client.get("/api/assignments", auth=("TEST_ADMIN", "TEST_PASSWORD"))
            assert response.status_code == 200, f"Authentication failed: {response.text}"
    
    def test_environment_variables_clean(self):
        """Test 6: Verify credentials are not in environment variables."""
        # Check that basic auth credentials are not in environment
        env_vars = os.environ
        assert 'APP_BASIC_AUTH_USER' not in env_vars, "Username found in environment variables"
        assert 'APP_BASIC_AUTH_PASS' not in env_vars, "Password found in environment variables"
    
    def test_secret_manager_integration(self):
        """Test 7: Verify Secret Manager integration in application."""
        # Mock Secret Manager client
        with patch('src.api.get_secret_manager_credentials') as mock_get_creds:
            mock_get_creds.return_value = ("test_user", "test_pass")
            
            # Test that the application uses Secret Manager credentials
            client = TestClient(app)
            response = client.get("/api/assignments", auth=("test_user", "test_pass"))
            assert response.status_code == 200, "Secret Manager integration failed"
    
    def test_authentication_error_handling(self):
        """Test 8: Error handling for invalid credentials."""
        client = TestClient(app)
        
        # Test with wrong credentials
        response = client.get("/api/assignments", auth=("wrong_user", "wrong_pass"))
        assert response.status_code == 401, "Should return 401 for invalid credentials"
        
        # Test with missing credentials
        response = client.get("/api/assignments")
        assert response.status_code == 401, "Should return 401 for missing credentials"
    
    def test_secret_manager_performance(self):
        """Test 9: Performance of Secret Manager calls."""
        import time
        
        with patch('src.api.get_secret_manager_credentials') as mock_get_creds:
            mock_get_creds.return_value = ("test_user", "test_pass")
            
            start_time = time.time()
            client = TestClient(app)
            response = client.get("/api/assignments", auth=("test_user", "test_pass"))
            end_time = time.time()
            
            assert response.status_code == 200, "Authentication failed"
            assert (end_time - start_time) < 2.0, "Secret Manager call too slow"
    
    def test_secret_manager_fallback(self):
        """Test 10: Fallback behavior when Secret Manager fails."""
        # Test that the function falls back to environment variables when Secret Manager fails
        with patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'}, clear=False):
            with patch('src.api.get_secret_client') as mock_get_client:
                # Mock Secret Manager client to raise an exception
                mock_client = MagicMock()
                mock_client.access_secret_version.side_effect = Exception("Secret Manager unavailable")
                mock_get_client.return_value = mock_client
                
                # Mock the settings to use fallback credentials
                with patch('src.api.settings') as mock_settings:
                    mock_settings.basic_auth_user = 'fallback_user'
                    mock_settings.basic_auth_pass = 'fallback_pass'
                    
                    # Clear the credential cache to force fresh lookup
                    from src.api import _credential_cache
                    _credential_cache.clear()
                    
                    client = TestClient(app)
                    
                    # Should fall back to environment variables
                    response = client.get("/api/assignments", auth=("fallback_user", "fallback_pass"))
                    assert response.status_code == 200, "Fallback to environment variables failed"


class TestSecretManagerCLI:
    """Test Secret Manager CLI commands."""
    
    def test_create_secrets_command(self):
        """Test secret creation commands."""
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Test username secret exists
        result = subprocess.run([
            'gcloud', 'secrets', 'describe', 'riv-basic-auth-user'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Username secret not found: {result.stderr}"
        
        # Test password secret exists
        result = subprocess.run([
            'gcloud', 'secrets', 'describe', 'riv-basic-auth-pass'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Password secret not found: {result.stderr}"
    
    def test_secret_rotation(self):
        """Test secret rotation capability."""
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            pytest.skip("GCP_PROJECT_ID not set")
        
        # Test that we can create new versions
        new_password = "new_test_password_456"
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'add', 'riv-basic-auth-pass',
            '--data-file=-'
        ], input=new_password, text=True, capture_output=True)
        
        assert result.returncode == 0, f"Failed to rotate password: {result.stderr}"
        
        # Verify new version is accessible
        result = subprocess.run([
            'gcloud', 'secrets', 'versions', 'access', 'latest',
            '--secret=riv-basic-auth-pass'
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Failed to access rotated password: {result.stderr}"
        assert result.stdout.strip() == new_password, "Rotated password not accessible"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
