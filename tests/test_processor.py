import pytest
import tempfile
import os
import uuid
from datetime import datetime
from src.storage import Database
from src.processor import EmailProcessor
from src.models import Student, Teacher, Class, Term, Parent, Enrollment

@pytest.fixture
def test_database_with_data():
    """Fixture providing a database with test data."""
    # Use unique identifiers to avoid conflicts
    unique_suffix = str(uuid.uuid4())[:8]
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = f"sqlite:///{tmp.name}"
    
    try:
        db = Database(db_path)
        
        # Set up supporting data
        term = Term(
            id=f"term-1-{unique_suffix}",
            name="FALL",
            year=2024,
            start_date=datetime(2024, 9, 1),
            end_date=datetime(2024, 12, 15)
        )
        db.save_term(term)
        
        teacher = Teacher(
            id=f"teacher-1-{unique_suffix}",
            email=f"teacher-{unique_suffix}@test.com",
            first_name="Jane",
            last_name="Smith"
        )
        db.save_teacher(teacher)
        
        class_obj = Class(
            id=f"class-1-{unique_suffix}",
            term_id=f"term-1-{unique_suffix}",
            name="English 7",
            teacher_id=f"teacher-1-{unique_suffix}"
        )
        db.save_class(class_obj)
        
        student = Student(
            id=f"student-1-{unique_suffix}",
            student_id=f"STU001-{unique_suffix}",
            first_name="John",
            last_name="Doe"
        )
        db.save_student(student)
        
        parent = Parent(
            id=f"parent-1-{unique_suffix}",
            email=f"parent-{unique_suffix}@test.com"
        )
        db.save_parent(parent)
        
        enrollment = Enrollment(
            id=f"enrollment-1-{unique_suffix}",
            class_id=f"class-1-{unique_suffix}",
            student_id=f"STU001-{unique_suffix}",
            parent_id=f"parent-1-{unique_suffix}",
            joined_at=datetime.utcnow()
        )
        db.save_enrollment(enrollment)
        
        yield db, unique_suffix
    finally:
        if os.path.exists(db_path.replace("sqlite:///", "")):
            os.unlink(db_path.replace("sqlite:///", ""))

def test_email_processing(test_database_with_data):
    """Test end-to-end email processing."""
    db, unique_suffix = test_database_with_data
    processor = EmailProcessor(db)

    # Test assignment creation
    assignment_email = """
    Title: Test Assignment
    Class: English 7
    Deadline: 2025-01-15 23:59 CT
    """

    # Use the unique teacher email from the test data
    teacher_email = f"teacher-{unique_suffix}@test.com"

    response = processor.process_email(
        email_content=assignment_email,
        from_email=teacher_email,
        to_emails=["assignments@test.com"],
        subject="ASSIGN",
        message_id="msg-123"
    )

    assert "Assignment 'Test Assignment' created successfully" in response
    assert "ENGLISH7-0115" in response
    
    # Test submission processing
    submission_email = f"StudentID: STU001-{unique_suffix}\nHere is my work."
    
    response = processor.process_email(
        email_content=submission_email,
        from_email="student@test.com",
        to_emails=["assignments@test.com"],
        subject="SUBMIT ENGLISH7-0115",
        message_id="msg-124"
    )
    
    assert "Submission received" in response
    assert f"STU001-{unique_suffix}" in response
    
    # Test grade processing
    grade_email = """
    Grade: A-
    Feedback: Good work!
    """
    
    response = processor.process_email(
        email_content=grade_email,
        from_email=teacher_email,
        to_emails=["assignments@test.com"],
        subject=f"GRADE ENGLISH7-0115 STU001-{unique_suffix}",
        message_id="msg-125"
    )
    
    assert "Grade recorded" in response
    assert f"STU001-{unique_suffix}" in response
    assert "A-" in response
    
    # Test service separation by verifying individual services work
    assert hasattr(processor, 'email_parser')
    assert hasattr(processor, 'assignment_service')
    assert hasattr(processor, 'submission_service')
    assert hasattr(processor, 'grade_service')