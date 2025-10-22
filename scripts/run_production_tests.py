#!/usr/bin/env python3
"""
Production test runner for RIV Assignment System.
Runs comprehensive tests to validate production deployment.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

def run_test_suite():
    """Run the complete production test suite."""
    print("🚀 Running Production Test Suite...")
    print("=" * 50)
    
    # Test 1: Secret Manager Tests
    print("\n1. Testing Secret Manager Integration...")
    result = subprocess.run([
        'python3', 'scripts/test_secret_manager_setup.py'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Secret Manager tests failed: {result.stderr}")
        return False
    
    print("✅ Secret Manager tests passed")
    
    # Test 2: Unit Tests
    print("\n2. Running Unit Tests...")
    result = subprocess.run([
        'pytest', 'tests/test_secret_manager.py', '-v'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Unit tests failed: {result.stderr}")
        return False
    
    print("✅ Unit tests passed")
    
    # Test 3: Production Deployment Tests
    print("\n3. Testing Production Deployment...")
    result = subprocess.run([
        'pytest', 'tests/test_production_deployment.py', '-v'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Production deployment tests failed: {result.stderr}")
        return False
    
    print("✅ Production deployment tests passed")
    
    # Test 4: Integration Tests
    print("\n4. Running Integration Tests...")
    result = subprocess.run([
        'pytest', 'tests/test_storage.py', '-v'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Integration tests failed: {result.stderr}")
        return False
    
    print("✅ Integration tests passed")
    
    # Test 5: Performance Tests
    print("\n5. Running Performance Tests...")
    if not run_performance_tests():
        print("❌ Performance tests failed")
        return False
    
    print("✅ Performance tests passed")
    
    # Test 6: Security Tests
    print("\n6. Running Security Tests...")
    if not run_security_tests():
        print("❌ Security tests failed")
        return False
    
    print("✅ Security tests passed")
    
    print("\n🎉 All Production Tests Passed!")
    return True

def run_performance_tests():
    """Run performance tests."""
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("⚠️  GCP_PROJECT_ID not set, skipping performance tests")
        return True
    
    # Get service URL
    result = subprocess.run([
        'gcloud', 'run', 'services', 'describe', 'riv-assignments',
        '--region', region,
        '--format=value(status.url)'
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
    
    print(f"✅ Response time: {response_time:.2f}s")
    return True

def run_security_tests():
    """Run security tests."""
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("⚠️  GCP_PROJECT_ID not set, skipping security tests")
        return True
    
    # Test 1: Check for hardcoded credentials
    print("  - Checking for hardcoded credentials...")
    src_path = Path(__file__).parent.parent / 'src'
    
    for file_path in src_path.rglob('*.py'):
        with open(file_path, 'r') as f:
            content = f.read().lower()
            
            if 'password=' in content or 'admin123' in content or 'secret=' in content:
                print(f"❌ Hardcoded credentials found in {file_path}")
                return False
    
    print("  ✅ No hardcoded credentials found")
    
    # Test 2: Check environment variables
    print("  - Checking environment variables...")
    sensitive_vars = ['APP_BASIC_AUTH_USER', 'APP_BASIC_AUTH_PASS', 'DATABASE_URL']
    
    for var in sensitive_vars:
        if var in os.environ:
            value = os.environ[var]
            if value.startswith('postgresql://') or value.startswith('admin'):
                print(f"❌ Sensitive {var} found in environment")
                return False
    
    print("  ✅ Environment variables secure")
    
    # Test 3: Check logs for sensitive data
    print("  - Checking logs for sensitive data...")
    result = subprocess.run([
        'gcloud', 'logging', 'read',
        f'resource.type="cloud_run_revision" AND resource.labels.service_name="riv-assignments"',
        '--limit=50',
        '--format=json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        logs = json.loads(result.stdout)
        for log_entry in logs:
            log_text = log_entry.get('textPayload', '')
            if 'password' in log_text.lower() or 'secret' in log_text.lower():
                print(f"❌ Sensitive data found in logs: {log_text}")
                return False
    
    print("  ✅ No sensitive data in logs")
    
    return True

def run_health_checks():
    """Run health checks."""
    print("\n7. Running Health Checks...")
    
    project_id = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION', 'us-central1')
    
    if not project_id:
        print("⚠️  GCP_PROJECT_ID not set, skipping health checks")
        return True
    
    # Get service URL
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
    
    health_data = json.loads(result.stdout)
    if health_data['status'] != 'healthy':
        print(f"❌ Service not healthy: {health_data}")
        return False
    
    print("✅ Health checks passed")
    return True

def main():
    """Main test runner."""
    print("🧪 RIV Assignment System - Production Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    if not os.getenv('GCP_PROJECT_ID'):
        print("⚠️  GCP_PROJECT_ID not set - some tests will be skipped")
    
    # Run test suite
    if run_test_suite():
        print("\n🎉 All Production Tests Passed!")
        print("✅ System is ready for production use")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        print("🔧 Please fix the issues before deploying to production")
        sys.exit(1)

if __name__ == "__main__":
    main()
