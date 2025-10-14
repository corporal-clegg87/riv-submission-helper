import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_process_assignment_email():
    """Test processing an assignment creation email."""
    import time
    unique_id = str(int(time.time() * 1000))[-6:]
    response = client.post("/api/process-email", json={
        "subject": f"ASSIGN Test Assignment {unique_id}",
        "body": f"Title: Math Homework {unique_id}\nClass: Math{unique_id}\nDeadline: 2025-01-20 23:59 CT\nInstructions: Complete problems 1-10",
        "from_email": "teacher@example.com",
        "to_email": "assignments@example.com",
        "message_id": f"test{unique_id}@example.com"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "created with code" in data["response"]

def test_process_submission_email():
    """Test processing a student submission email."""
    import time
    unique_id = str(int(time.time() * 1000))[-6:]
    
    # First create an assignment
    client.post("/api/process-email", json={
        "subject": f"ASSIGN Test Assignment {unique_id}",
        "body": f"Title: Math Homework {unique_id}\nClass: Math{unique_id}\nDeadline: 2025-01-20 23:59 CT",
        "from_email": "teacher@example.com",
        "to_email": "assignments@example.com",
        "message_id": f"assign{unique_id}@example.com"
    })
    
    # Then submit to it
    class_code = f"MATH{unique_id}"[:8]
    response = client.post("/api/process-email", json={
        "subject": f"SUBMIT {class_code}-0120",
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
    import time
    unique_id = str(int(time.time() * 1000))[-6:]
    
    # First create an assignment
    client.post("/api/process-email", json={
        "subject": f"ASSIGN Test Assignment {unique_id}",
        "body": f"Title: Math Homework {unique_id}\nClass: Math{unique_id}\nDeadline: 2025-01-20 23:59 CT",
        "from_email": "teacher@example.com",
        "to_email": "assignments@example.com",
        "message_id": f"assign{unique_id}@example.com"
    })
    
    class_code = f"MATH{unique_id}"[:8]
    response = client.get(f"/api/assignments/{class_code}-0120/status")
    assert response.status_code == 200
    data = response.json()
    assert "assignment" in data
    assert "submissions" in data
    assert data["assignment"]["code"] == f"{class_code}-0120"
