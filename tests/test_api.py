import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_process_assignment_email():
    """Test processing an assignment creation email."""
    response = client.post("/api/process-email", json={
        "subject": "ASSIGN Test Assignment",
        "body": "Title: Math Homework\nClass: Math 8\nDeadline: 2025-01-20 23:59 CT\nInstructions: Complete problems 1-10",
        "from_email": "teacher@example.com",
        "to_email": "assignments@example.com",
        "message_id": "test123@example.com"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "Assignment 'Math Homework' created" in data["response"]

def test_process_submission_email():
    """Test processing a student submission email."""
    # First create an assignment
    client.post("/api/process-email", json={
        "subject": "ASSIGN Test Assignment",
        "body": "Title: Math Homework\nClass: Math 8\nDeadline: 2025-01-20 23:59 CT",
        "from_email": "teacher@example.com",
        "to_email": "assignments@example.com",
        "message_id": "assign123@example.com"
    })
    
    # Then submit to it
    response = client.post("/api/process-email", json={
        "subject": "SUBMIT MATH8-0120",
        "body": "StudentID: STU001",
        "from_email": "student@example.com",
        "to_email": "assignments@example.com",
        "message_id": "submit123@example.com"
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
    # First create an assignment
    client.post("/api/process-email", json={
        "subject": "ASSIGN Test Assignment",
        "body": "Title: Math Homework\nClass: Math 8\nDeadline: 2025-01-20 23:59 CT",
        "from_email": "teacher@example.com",
        "to_email": "assignments@example.com",
        "message_id": "assign456@example.com"
    })
    
    response = client.get("/api/assignments/MATH8-0120/status")
    assert response.status_code == 200
    data = response.json()
    assert "assignment" in data
    assert "submissions" in data
    assert data["assignment"]["code"] == "MATH8-0120"
