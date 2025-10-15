import pytest
import time
import tempfile
import os
import re
from datetime import datetime
from fastapi.testclient import TestClient
from src.api import app
from src.models import Student, Teacher, Class, Term, Parent, Enrollment

client = TestClient(app)

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
    })
    
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
    })

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
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "Submission received" in data["response"]

def test_list_assignments():
    """Test listing all assignments."""
    response = client.get("/api/assignments")
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
    })

    # Use the known assignment code format
    response = client.get("/api/assignments/MATH7-0120/status")
    assert response.status_code == 200
    data = response.json()
    assert "assignment" in data
    assert "submissions" in data
    assert data["assignment"]["code"] == "MATH7-0120"
