import pytest
import tempfile
import os
from datetime import datetime
from src.storage import Database
from src.processor import EmailProcessor
from src.models import Student, Teacher, Class, Term, Parent, Enrollment

def test_email_processing():
    """Test end-to-end email processing."""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = f"sqlite:///{tmp.name}"
    
    try:
        db = Database(db_path)
        processor = EmailProcessor(db)
        
        # Set up supporting data first
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
            email="teacher@test.com",
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
            email="parent@test.com"
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
            subject="ASSIGN",
            message_id="msg-123"
        )
        
        assert "Assignment 'Test Assignment' created successfully" in response
        assert "ENGLISH7-0115" in response
        
        # Test submission processing
        submission_email = "StudentID: STU001\nHere is my work."
        
        response = processor.process_email(
            email_content=submission_email,
            from_email="student@test.com",
            to_emails=["assignments@test.com"],
            subject="SUBMIT ENGLISH7-0115",
            message_id="msg-124"
        )
        
        assert "Submission received" in response
        assert "STU001" in response
        
        # Test grade processing
        grade_email = """
        Grade: A-
        Feedback: Good work!
        """
        
        response = processor.process_email(
            email_content=grade_email,
            from_email="teacher@test.com",
            to_emails=["assignments@test.com"],
            subject="GRADE ENGLISH7-0115 STU001",
            message_id="msg-125"
        )
        
        assert "Grade recorded" in response
        assert "STU001" in response
        assert "A-" in response
        
    finally:
        # Clean up
        if os.path.exists(db_path.replace("sqlite:///", "")):
            os.unlink(db_path.replace("sqlite:///", ""))
