import pytest
import time
import tempfile
import os
import re
from datetime import datetime
from unittest.mock import patch
from fastapi.testclient import TestClient
from src.api import app
from src.models import Student, Teacher, Class, Term, Parent, Enrollment

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_secret_manager():
    """Mock Secret Manager credentials for all tests."""
    with patch('src.api.get_secret_manager_credentials') as mock_get_creds:
        mock_get_creds.return_value = ("admin", "admin")
        yield mock_get_creds

@pytest.fixture(autouse=True)
def setup_test_data():
    """Set up test data for each test."""
    from src.api import db
    
    try:
        # Create term
        term = Term(
            id="api-test-term-1",
            name="FALL",
            year=2024,
            start_date=datetime(2024, 9, 1),
            end_date=datetime(2024, 12, 15)
        )
        db.save_term(term)
    except Exception:
        pass  # Already exists
    
    try:
        # Create teacher
        teacher = Teacher(
            id="api-test-teacher-1",
            email="teacher@rivendell-academy.co.uk",
            first_name="Test",
            last_name="Teacher"
        )
        db.save_teacher(teacher)
    except Exception:
        pass  # Already exists
    
    try:
        # Create class
        class_obj = Class(
            id="api-test-class-1",
            term_id="api-test-term-1",
            name="Math 7",
            teacher_id="api-test-teacher-1"
        )
        db.save_class(class_obj)
    except Exception:
        pass  # Already exists
    
    try:
        # Create student
        student = Student(
            id="api-test-student-1",
            student_id="STU001",
            first_name="Test",
            last_name="Student"
        )
        db.save_student(student)
    except Exception:
        pass  # Already exists
    
    try:
        # Create parent
        parent = Parent(
            id="api-test-parent-1",
            email="parent@example.com"
        )
        db.save_parent(parent)
    except Exception:
        pass  # Already exists
    
    try:
        # Create enrollment
        enrollment = Enrollment(
            id="api-test-enrollment-1",
            class_id="api-test-class-1",
            student_id="STU001",
            parent_id="api-test-parent-1",
            joined_at=datetime.utcnow()
        )
        db.save_enrollment(enrollment)
    except Exception:
        pass  # Already exists

def test_process_assignment_email():
    """Test processing an assignment creation email."""
    unique_id = str(int(time.time() * 1000))[-6:]
    # Use unique date to avoid code conflicts - use timestamp to ensure uniqueness
    timestamp = int(time.time())
    unique_date = f"2025-{timestamp % 12 + 1:02d}-{timestamp % 28 + 1:02d}"
    response = client.post("/api/process-email", json={
            "subject": "ASSIGN",
            "body": f"Title: Math Homework {unique_id}\nClass: Math 7\nDeadline: {unique_date} 23:59 CT\nInstructions: Complete problems 1-10",
            "from_email": "teacher@rivendell-academy.co.uk",
            "to_email": "assignments@example.com",
            "message_id": f"test{unique_id}@example.com"
        }, auth=("admin", "admin"))
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "created successfully" in data["response"]
    # Verify assignment code format matches expected pattern
    assert re.search(r'[A-Z0-9]+-[0-9]{4}', data["response"])

def test_process_submission_email():
    """Test processing a student submission email."""
    unique_id = str(int(time.time() * 1000))[-6:]
    # Use unique date to avoid code conflicts
    timestamp = int(time.time())
    unique_date = f"2025-{timestamp % 12 + 1:02d}-{timestamp % 28 + 1:02d}"

    # First create an assignment using seeded class
    response = client.post("/api/process-email", json={
            "subject": "ASSIGN",
            "body": f"Title: Math Homework {unique_id}\nClass: Math 7\nDeadline: {unique_date} 23:59 CT",
            "from_email": "teacher@rivendell-academy.co.uk",
            "to_email": "assignments@example.com",
            "message_id": f"assign{unique_id}@example.com"
        }, auth=("admin", "admin"))

    # Extract assignment code from response - use the unique date
    date_code = unique_date.replace("-", "")[4:]  # Extract MMDD from YYYY-MM-DD
    assignment_code = f"MATH7-{date_code}"

    # Then submit to it
    response = client.post("/api/process-email", json={
            "subject": f"SUBMIT {assignment_code}",
            "body": "StudentID: STU001",
            "from_email": "student@example.com",
            "to_email": "assignments@example.com",
            "message_id": f"submit{unique_id}@example.com"
        }, auth=("admin", "admin"))

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "Submission received" in data["response"]

def test_list_assignments():
    """Test listing all assignments."""
    response = client.get("/api/assignments", auth=("admin", "admin"))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_assignment_status():
    """Test getting assignment status."""
    unique_id = str(int(time.time() * 1000))[-6:]

    # First create an assignment using seeded class
    client.post("/api/process-email", json={
            "subject": "ASSIGN",
            "body": f"Title: Math Homework {unique_id}\nClass: Math 7\nDeadline: 2025-01-20 23:59 CT",
            "from_email": "teacher@rivendell-academy.co.uk",
            "to_email": "assignments@example.com",
            "message_id": f"assign{unique_id}@example.com"
        }, auth=("admin", "admin"))

    # Use the known assignment code format
    response = client.get("/api/assignments/MATH7-0120/status", auth=("admin", "admin"))
    assert response.status_code == 200
    data = response.json()
    assert "assignment" in data
    assert "submissions" in data
    assert data["assignment"]["code"] == "MATH7-0120"

def test_monitoring_metrics_authenticated():
    """Test getting monitoring metrics with authentication."""
    response = client.get("/api/monitoring/metrics", auth=("admin", "admin"))
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "cloud_run" in data
    assert "cloud_sql" in data
    assert "application" in data
    assert "status" in data
    
    # Check that all sections have required keys
    assert "timestamp" in data["cloud_run"]
    assert "timestamp" in data["cloud_sql"]
    assert "timestamp" in data["application"]

def test_monitoring_metrics_unauthenticated():
    """Test that monitoring metrics endpoint requires authentication."""
    response = client.get("/api/monitoring/metrics")
    assert response.status_code == 401

def test_monitoring_metrics_structure():
    """Test that monitoring metrics response has expected structure."""
    response = client.get("/api/monitoring/metrics", auth=("admin", "admin"))
    assert response.status_code == 200
    data = response.json()
    
    # Check cloud_run metrics structure
    cloud_run = data["cloud_run"]
    expected_cloud_run_keys = ["request_count", "avg_latency_ms", "error_rate", "active_instances", "timestamp"]
    for key in expected_cloud_run_keys:
        assert key in cloud_run
    
    # Check cloud_sql metrics structure
    cloud_sql = data["cloud_sql"]
    expected_cloud_sql_keys = ["active_connections", "cpu_utilization", "timestamp"]
    for key in expected_cloud_sql_keys:
        assert key in cloud_sql
    
    # Check application metrics structure
    application = data["application"]
    expected_application_keys = ["uptime_seconds", "environment", "timestamp"]
    for key in expected_application_keys:
        assert key in application
