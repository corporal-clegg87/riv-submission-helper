#!/usr/bin/env python3
"""
Setup Secret Manager for RIV Assignment System.
Creates secrets, configures IAM, and sets up Cloud Run integration.
"""

import os
import sys
import subprocess
import secrets
import string
from pathlib import Path

def generate_secure_password(length=32):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_secrets():
    """Create secrets in Secret Manager."""
    print("🔐 Creating secrets in Secret Manager...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        print("❌ GCP_PROJECT_ID environment variable not set")
        return False
    
    # Generate secure password
    password = generate_secure_password()
    username = "riv_admin_2024"
    
    # Create username secret
    print("  - Creating username secret...")
    result = subprocess.run([
        'gcloud', 'secrets', 'create', 'riv-basic-auth-user',
        '--data-file=-'
    ], input=username, text=True, capture_output=True)
    
    if result.returncode != 0:
        if "already exists" in result.stderr:
            print("  ⚠️  Username secret already exists")
        else:
            print(f"❌ Failed to create username secret: {result.stderr}")
            return False
    else:
        print("  ✅ Username secret created")
    
    # Create password secret
    print("  - Creating password secret...")
    result = subprocess.run([
        'gcloud', 'secrets', 'create', 'riv-basic-auth-pass',
        '--data-file=-'
    ], input=password, text=True, capture_output=True)
    
    if result.returncode != 0:
        if "already exists" in result.stderr:
            print("  ⚠️  Password secret already exists")
        else:
            print(f"❌ Failed to create password secret: {result.stderr}")
            return False
    else:
        print("  ✅ Password secret created")
    
    # Save credentials for reference
    with open('.secret_manager_credentials.txt', 'w') as f:
        f.write(f"Username: {username}\n")
        f.write(f"Password: {password}\n")
        f.write(f"Project: {project_id}\n")
    
    print(f"  📝 Credentials saved to .secret_manager_credentials.txt")
    print(f"  🔑 Username: {username}")
    print(f"  🔑 Password: {password}")
    
    return True

def configure_iam():
    """Configure IAM permissions for secrets."""
    print("\n🔒 Configuring IAM permissions...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    if not project_id:
        print("❌ GCP_PROJECT_ID environment variable not set")
        return False
    
    service_account = f'riv-assignments-sa@{project_id}.iam.gserviceaccount.com'
    
    # Grant access to username secret
    print("  - Configuring username secret access...")
    result = subprocess.run([
        'gcloud', 'secrets', 'add-iam-policy-binding', 'riv-basic-auth-user',
        '--member', f'serviceAccount:{service_account}',
        '--role', 'roles/secretmanager.secretAccessor'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to configure username secret access: {result.stderr}")
        return False
    
    print("  ✅ Username secret access configured")
    
    # Grant access to password secret
    print("  - Configuring password secret access...")
    result = subprocess.run([
        'gcloud', 'secrets', 'add-iam-policy-binding', 'riv-basic-auth-pass',
        '--member', f'serviceAccount:{service_account}',
        '--role', 'roles/secretmanager.secretAccessor'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to configure password secret access: {result.stderr}")
        return False
    
    print("  ✅ Password secret access configured")
    
    return True

def update_cloud_run():
    """Update Cloud Run service to use secrets."""
    print("\n🚀 Updating Cloud Run service...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("❌ GCP_PROJECT_ID environment variable not set")
        return False
    
    # Get current service configuration
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region,
        '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to get service configuration: {result.stderr}")
        return False
    
    # Update service with secret references
    print("  - Updating service with secret references...")
    result = subprocess.run([
        'gcloud', 'run', 'services', 'update', 'riv-assignments',
        '--region', region,
        '--set-secrets', 'APP_BASIC_AUTH_USER=riv-basic-auth-user:latest,APP_BASIC_AUTH_PASS=riv-basic-auth-pass:latest'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to update service: {result.stderr}")
        return False
    
    print("  ✅ Service updated with secret references")
    
    return True

def verify_setup():
    """Verify Secret Manager setup."""
    print("\n🔍 Verifying setup...")
    
    # Test secret access
    print("  - Testing secret access...")
    result = subprocess.run([
        'gcloud', 'secrets', 'versions', 'access', 'latest',
        '--secret=riv-basic-auth-user'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to access username secret: {result.stderr}")
        return False
    
    username = result.stdout.strip()
    if username != "riv_admin_2024":
        print(f"❌ Username secret incorrect: {username}")
        return False
    
    print("  ✅ Username secret accessible")
    
    # Test password access
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
    
    print("  ✅ Password secret accessible")
    
    # Test service health
    print("  - Testing service health...")
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region,
        '--format=value(status.url)'
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
    
    print("  ✅ Service health check passed")
    
    return True

def main():
    """Main setup function."""
    print("🔐 RIV Assignment System - Secret Manager Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not os.getenv('GCP_PROJECT_ID'):
        print("❌ GCP_PROJECT_ID environment variable not set")
        sys.exit(1)
    
    # Step 1: Create secrets
    if not create_secrets():
        print("❌ Failed to create secrets")
        sys.exit(1)
    
    # Step 2: Configure IAM
    if not configure_iam():
        print("❌ Failed to configure IAM")
        sys.exit(1)
    
    # Step 3: Update Cloud Run
    if not update_cloud_run():
        print("❌ Failed to update Cloud Run service")
        sys.exit(1)
    
    # Step 4: Verify setup
    if not verify_setup():
        print("❌ Setup verification failed")
        sys.exit(1)
    
    print("\n🎉 Secret Manager setup completed successfully!")
    print("✅ System is ready for production use")
    print("\n📝 Next steps:")
    print("  1. Test authentication with the provided credentials")
    print("  2. Run production tests: python scripts/run_production_tests.py")
    print("  3. Monitor service logs for any issues")

if __name__ == "__main__":
    main()
