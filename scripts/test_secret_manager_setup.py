#!/usr/bin/env python3
"""
Test script for Secret Manager setup validation.
Run this script to verify Secret Manager configuration is correct.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def test_secret_manager_setup():
    """Test Secret Manager setup and configuration."""
    print("🔍 Testing Secret Manager setup...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        print("❌ GCP_PROJECT_ID environment variable not set")
        return False
    
    print(f"✅ Project ID: {project_id}")
    
    # Test 1: Verify secrets exist
    print("\n1. Testing secret existence...")
    result = subprocess.run([
        'gcloud', 'secrets', 'list', 
        '--filter=name:riv-basic-auth',
        '--format=json'
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
    
    print("✅ All secrets exist")
    
    # Test 2: Verify secret access
    print("\n2. Testing secret access...")
    
    # Test username secret
    result = subprocess.run([
        'gcloud', 'secrets', 'versions', 'access', 'latest',
        '--secret=riv-basic-auth-user'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to access username secret: {result.stderr}")
        return False
    
    username = result.stdout.strip()
    if username != "riv_admin_2024":  # EXAMPLE_USERNAME
        print(f"❌ Username secret incorrect: {username}")
        return False
    
    print("✅ Username secret accessible")
    
    # Test password secret
    result = subprocess.run([
        'gcloud', 'secrets', 'versions', 'access', 'latest',
        '--secret=riv-basic-auth-pass'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to access password secret: {result.stderr}")
        return False
    
    password = result.stdout.strip()
    if len(password) < 20:
        print("❌ Password secret too short")
        return False
    
    print("✅ Password secret accessible")
    
    # Test 3: Verify IAM permissions
    print("\n3. Testing IAM permissions...")
    
    # Check username secret IAM
    result = subprocess.run([
        'gcloud', 'secrets', 'get-iam-policy', 'riv-basic-auth-user'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get IAM policy for username secret: {result.stderr}")
        return False
    
    if 'roles/secretmanager.secretAccessor' not in result.stdout:
        print("❌ Missing secret accessor role for username secret")
        return False
    
    if f'serviceAccount:riv-assignments-sa@{project_id}.iam.gserviceaccount.com' not in result.stdout:
        print("❌ Service account not found in username secret IAM")
        return False
    
    print("✅ Username secret IAM correct")
    
    # Check password secret IAM
    result = subprocess.run([
        'gcloud', 'secrets', 'get-iam-policy', 'riv-basic-auth-pass'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get IAM policy for password secret: {result.stderr}")
        return False
    
    if 'roles/secretmanager.secretAccessor' not in result.stdout:
        print("❌ Missing secret accessor role for password secret")
        return False
    
    if f'serviceAccount:riv-assignments-sa@{project_id}.iam.gserviceaccount.com' not in result.stdout:
        print("❌ Service account not found in password secret IAM")
        return False
    
    print("✅ Password secret IAM correct")
    
    # Test 4: Verify Cloud Run service configuration
    print("\n4. Testing Cloud Run service configuration...")
    
    region = os.getenv('GCP_REGION', 'us-central1')
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region,
        '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Cloud Run service not found: {result.stderr}")
        return False
    
    service_info = json.loads(result.stdout)
    env_vars = service_info['spec']['template']['spec']['containers'][0]['env']
    
    # Check for secret references
    secret_refs = [env for env in env_vars if 'valueFrom' in env and 'secretKeyRef' in env.get('valueFrom', {})]
    if len(secret_refs) < 2:
        print("❌ Secret references not found in Cloud Run service")
        return False
    
    secret_names = [ref['valueFrom']['secretKeyRef']['name'] for ref in secret_refs]
    if 'riv-basic-auth-user' not in secret_names:
        print("❌ Username secret reference not found in Cloud Run service")
        return False
    
    if 'riv-basic-auth-pass' not in secret_names:
        print("❌ Password secret reference not found in Cloud Run service")
        return False
    
    print("✅ Cloud Run service configured with secrets")
    
    # Test 5: Verify service account
    print("\n5. Testing service account configuration...")
    
    service_account = service_info['spec']['template']['spec']['serviceAccountName']
    expected_service_account = f'riv-assignments-sa@{project_id}.iam.gserviceaccount.com'
    
    if service_account != expected_service_account:
        print(f"❌ Service account incorrect: {service_account}")
        return False
    
    print("✅ Service account configured correctly")
    
    # Test 6: Test service connectivity
    print("\n6. Testing service connectivity...")
    
    service_url = service_info['status']['url']
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
    
    print("✅ Service connectivity working")
    
    # Test 7: Test authentication
    print("\n7. Testing authentication...")
    
    result = subprocess.run([
        'curl', '-u', f'{username}:{password}',
        f'{service_url}/api/assignments'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Authentication failed: {result.stderr}")
        return False
    
    print("✅ Authentication working")
    
    print("\n🎉 All Secret Manager tests passed!")
    return True

def main():
    """Main test function."""
    if test_secret_manager_setup():
        print("\n✅ Secret Manager setup is correct!")
        sys.exit(0)
    else:
        print("\n❌ Secret Manager setup has issues!")
        sys.exit(1)

if __name__ == "__main__":
    main()
