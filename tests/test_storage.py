import pytest
import tempfile
import os
from datetime import datetime
from typing import Optional
from src.storage import Database
from src.models import Assignment, Submission, Grade, Student, Teacher, Class, Term, Parent, Enrollment

def test_database_operations():
    """Test basic database operations."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = f"sqlite:///{tmp.name}"
    
    try:
        db = Database(db_path)
        
        # First create supporting data
        term = Term(
            id="term-1",
            name="FALL",
            year=2024,
            start_date=datetime(2024, 9, 1),
            end_date=datetime(2024, 12, 15)
        )
        db.save_term(term)
        
        teacher = Teacher(
            id="teacher-1",
            email="teacher@example.com",
            first_name="Jane",
            last_name="Smith"
        )
        db.save_teacher(teacher)
        
        class_obj = Class(
            id="class-1",
            term_id="term-1",
            name="English 7",
            teacher_id="teacher-1"
        )
        db.save_class(class_obj)
        
        student = Student(
            id="student-1",
            student_id="STU001",
            first_name="John",
            last_name="Doe"
        )
        db.save_student(student)
        
        parent = Parent(
            id="parent-1",
            email="parent@example.com"
        )
        db.save_parent(parent)
        
        enrollment = Enrollment(
            id="enrollment-1",
            class_id="class-1",
            student_id="STU001",
            parent_id="parent-1",
            joined_at=datetime.utcnow()
        )
        db.save_enrollment(enrollment)
        
        # Test assignment save and retrieve
        assignment = Assignment(
            id="test-123",
            code="ENG7-0115",
            class_id="class-1",
            title="Test Assignment",
            instructions="Test instructions",
            deadline_at=datetime(2025, 1, 15, 23, 59),
            deadline_tz="CT",
            created_by_teacher_id="teacher-1",
            status="SCHEDULED",
            grace_days=7,
            created_at=datetime.utcnow()
        )
        
        db.save_assignment(assignment)
        retrieved = db.get_assignment_by_code("ENG7-0115")
        
        assert retrieved is not None
        assert retrieved.title == "Test Assignment"
        assert retrieved.code == "ENG7-0115"
        assert retrieved.class_id == "class-1"
        
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
        
        # Test enrollment validation
        is_enrolled = db.is_student_enrolled_in_class("STU001", "class-1")
        assert is_enrolled == True
        
    finally:
        # Clean up
        if os.path.exists(db_path.replace("sqlite:///", "")):
            os.unlink(db_path.replace("sqlite:///", ""))
