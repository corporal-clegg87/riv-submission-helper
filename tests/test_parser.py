import pytest
from datetime import datetime
from src.parser import parse_assignment_email, parse_submission_email, parse_return_email

def test_parse_assignment_valid():
    """Test valid assignment email parsing."""
    subject = "ASSIGN"
    body = """
    Title: Essay on Climate Change
    Class: English 7
    Deadline: 2025-01-15 23:59 CT
    Instructions: Write 500 words on climate change impacts.
    """
    
    assignment_data = parse_assignment_email(body, subject)
    assert assignment_data is not None
    assert assignment_data['title'] == "Essay on Climate Change"
    assert assignment_data['class_name'] == "English 7"
    assert assignment_data['deadline_at'] == datetime(2025, 1, 15, 23, 59)
    assert assignment_data['code'].startswith("ENGLISH7")

def test_parse_assignment_invalid():
    """Test invalid assignment email parsing."""
    subject = "ASSIGN"
    body = "Title: Test\nClass: Test"  # Missing deadline
    
    assignment = parse_assignment_email(body, subject)
    assert assignment is None

def test_parse_submission_valid():
    """Test valid submission email parsing."""
    subject = "SUBMIT ENG7-0115"
    body = "StudentID: STU001\nHere is my essay."
    
    result = parse_submission_email(body, subject)
    assert result is not None
    assignment_code, student_id = result
    assert assignment_code == "ENG7-0115"
    assert student_id == "STU001"

def test_parse_return_valid():
    """Test valid return email parsing."""
    subject = "RETURN ENG7-0115 STU001"
    body = """
    Grade: A-
    Feedback: Good work on the introduction, but conclusion needs more detail.
    """
    
    result = parse_return_email(body, subject)
    assert result is not None
    assignment_code, student_id, grade_data = result
    assert assignment_code == "ENG7-0115"
    assert student_id == "STU001"
    assert grade_data['grade'] == "A-"
