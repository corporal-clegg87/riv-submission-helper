import pytest
import tempfile
import os
from src.storage import Database
from src.processor import EmailProcessor

def test_email_processing():
    """Test end-to-end email processing."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = Database(db_path)
        processor = EmailProcessor(db)
        
        # Test assignment creation
        assignment_email = """
        Title: Test Assignment
        Class: English 7
        Deadline: 2025-01-15 23:59 CT
        """
        
        response = processor.process_email(
            email_content=assignment_email,
            from_email="teacher@test.com",
            to_emails=["assignments@test.com"],
            subject="ASSIGN Test",
            message_id="msg-123"
        )
        
        assert "Assignment 'Test Assignment' created" in response
        assert "ENG7-0115" in response
        
        # Test submission processing
        submission_email = "StudentID: STU001\nHere is my work."
        
        response = processor.process_email(
            email_content=submission_email,
            from_email="student@test.com",
            to_emails=["assignments@test.com"],
            subject="SUBMIT ENG7-0115",
            message_id="msg-124"
        )
        
        assert "Submission received" in response
        assert "STU001" in response
        
        # Test return processing
        return_email = """
        Grade: A-
        Feedback: Good work!
        """
        
        response = processor.process_email(
            email_content=return_email,
            from_email="teacher@test.com",
            to_emails=["assignments@test.com"],
            subject="RETURN ENG7-0115 STU001",
            message_id="msg-125"
        )
        
        assert "Grade recorded" in response
        assert "STU001" in response
        assert "A-" in response
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
