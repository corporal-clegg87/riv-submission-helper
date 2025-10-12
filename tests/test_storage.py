import pytest
import tempfile
import os
from datetime import datetime
from src.storage import Database
from src.models import Assignment, Submission, Grade

def test_database_operations():
    """Test basic database operations."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = Database(db_path)
        
        # Test assignment save and retrieve
        assignment = Assignment(
            id="test-123",
            code="ENG7-0115",
            title="Test Assignment",
            class_name="English 7",
            deadline_at=datetime(2025, 1, 15, 23, 59),
            deadline_tz="CT",
            instructions="Test instructions",
            status="SCHEDULED",
            created_at=datetime.utcnow()
        )
        
        db.save_assignment(assignment)
        retrieved = db.get_assignment_by_code("ENG7-0115")
        
        assert retrieved is not None
        assert retrieved.title == "Test Assignment"
        assert retrieved.code == "ENG7-0115"
        
        # Test submission save
        submission = Submission(
            id="sub-123",
            assignment_id="test-123",
            student_id="STU001",
            received_at=datetime.utcnow(),
            on_time=True,
            status="RECEIVED"
        )
        
        db.save_submission(submission)
        retrieved_sub = db.get_submission_by_assignment_and_student("test-123", "STU001")
        
        assert retrieved_sub is not None
        assert retrieved_sub.student_id == "STU001"
        assert retrieved_sub.on_time == True
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)
