import pytest
import tempfile
import os
import uuid
from datetime import datetime
from src.storage import Database
from src.services.email_parser import EmailParser
from src.services.assignment_service import AssignmentService
from src.services.submission_service import SubmissionService
from src.services.grade_service import GradeService
from src.models import Student, Teacher, Class, Term, Parent, Enrollment, EmailMessage

@pytest.fixture
def test_database_with_data():
    """Fixture providing a database with test data."""
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

class TestEmailParser:
    """Test EmailParser service following Single Responsibility Principle."""
    
    def test_parse_assignment(self):
        """Test assignment parsing."""
        parser = EmailParser()
        content = "Title: Test Assignment\nClass: English 7\nDeadline: 2025-01-15 23:59 CT"
        result = parser.parse_assignment(content, "ASSIGN")
        assert result is not None
        assert result['title'] == "Test Assignment"
        assert result['class_name'] == "English 7"
    
    def test_parse_submission(self):
        """Test submission parsing."""
        parser = EmailParser()
        content = "StudentID: STU001\nHere is my work."
        result = parser.parse_submission(content, "SUBMIT ENG7-0115")
        assert result is not None
        assert result[0] == "ENG7-0115"
        assert result[1] == "STU001"
    
    def test_parse_grade(self):
        """Test grade parsing."""
        parser = EmailParser()
        content = "Grade: A-\nFeedback: Good work!"
        result = parser.parse_grade(content, "GRADE ENG7-0115 STU001")
        assert result is not None
        assert result['assignment_code'] == "ENG7-0115"
        assert result['student_id'] == "STU001"
        assert result['grade_value'] == "A-"
    
    def test_parse_email_unknown(self):
        """Test unknown email parsing."""
        parser = EmailParser()
        result = parser.parse_email("Random content", "UNKNOWN")
        assert result['type'] == 'unknown'
        assert result['data'] is None

class TestAssignmentService:
    """Test AssignmentService following Single Responsibility Principle."""
    
    def test_create_assignment_success(self, test_database_with_data):
        """Test successful assignment creation."""
        db, unique_suffix = test_database_with_data
        service = AssignmentService(db)
        
        assignment_data = {
            'code': 'ENG7-0115',
            'title': 'Test Assignment',
            'class_name': 'English 7',
            'deadline_at': datetime(2025, 1, 15, 23, 59),
            'instructions': 'Test instructions'
        }
        
        email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email=f"teacher-{unique_suffix}@test.com",
            to_emails=["assignments@test.com"],
            subject="ASSIGN",
            message_id="msg-123",
            processed_at=datetime.utcnow()
        )
        
        response = service.create_assignment(assignment_data, email_msg)
        assert "Assignment 'Test Assignment' created successfully" in response
        assert "ENG7-0115" in response
    
    def test_create_assignment_any_teacher(self, test_database_with_data):
        """Test assignment creation with any teacher (authorization removed)."""
        db, unique_suffix = test_database_with_data
        service = AssignmentService(db)
        
        assignment_data = {
            'code': 'ENG7-0115',
            'title': 'Test Assignment',
            'class_name': 'English 7',
            'deadline_at': datetime(2025, 1, 15, 23, 59)
        }
        
        email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email="any_teacher@test.com",
            to_emails=["assignments@test.com"],
            subject="ASSIGN",
            message_id="msg-123",
            processed_at=datetime.utcnow()
        )
        
        response = service.create_assignment(assignment_data, email_msg)
        assert "created successfully" in response

class TestSubmissionService:
    """Test SubmissionService following Single Responsibility Principle."""
    
    def test_process_submission_success(self, test_database_with_data):
        """Test successful submission processing."""
        db, unique_suffix = test_database_with_data
        service = SubmissionService(db)
        
        # First create an assignment
        assignment_data = {
            'code': 'ENG7-0115',
            'title': 'Test Assignment',
            'class_name': 'English 7',
            'deadline_at': datetime(2025, 1, 15, 23, 59)
        }
        
        assignment_service = AssignmentService(db)
        email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email=f"teacher-{unique_suffix}@test.com",
            to_emails=["assignments@test.com"],
            subject="ASSIGN",
            message_id="msg-123",
            processed_at=datetime.utcnow()
        )
        
        assignment_service.create_assignment(assignment_data, email_msg)
        
        # Now test submission
        submission_data = ("ENG7-0115", f"STU001-{unique_suffix}")
        submission_email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email="student@test.com",
            to_emails=["assignments@test.com"],
            subject="SUBMIT ENG7-0115",
            message_id="msg-124",
            processed_at=datetime.utcnow()
        )
        
        response = service.process_submission(submission_data, submission_email_msg)
        assert "Submission received" in response
        assert f"STU001-{unique_suffix}" in response

class TestGradeService:
    """Test GradeService following Single Responsibility Principle."""
    
    def test_process_grade_success(self, test_database_with_data):
        """Test successful grade processing."""
        db, unique_suffix = test_database_with_data
        service = GradeService(db)
        
        # First create assignment and submission
        assignment_service = AssignmentService(db)
        submission_service = SubmissionService(db)
        
        assignment_data = {
            'code': 'ENG7-0115',
            'title': 'Test Assignment',
            'class_name': 'English 7',
            'deadline_at': datetime(2025, 1, 15, 23, 59)
        }
        
        email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email=f"teacher-{unique_suffix}@test.com",
            to_emails=["assignments@test.com"],
            subject="ASSIGN",
            message_id="msg-123",
            processed_at=datetime.utcnow()
        )
        
        assignment_service.create_assignment(assignment_data, email_msg)
        
        submission_data = ("ENG7-0115", f"STU001-{unique_suffix}")
        submission_email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email="student@test.com",
            to_emails=["assignments@test.com"],
            subject="SUBMIT ENG7-0115",
            message_id="msg-124",
            processed_at=datetime.utcnow()
        )
        
        submission_service.process_submission(submission_data, submission_email_msg)
        
        # Now test grading
        grade_data = {
            'assignment_code': 'ENG7-0115',
            'student_id': f"STU001-{unique_suffix}",
            'grade_value': 'A-',
            'feedback_text': 'Good work!'
        }
        
        grade_email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email=f"teacher-{unique_suffix}@test.com",
            to_emails=["assignments@test.com"],
            subject=f"GRADE ENG7-0115 STU001-{unique_suffix}",
            message_id="msg-125",
            processed_at=datetime.utcnow()
        )
        
        response = service.process_grade(grade_data, grade_email_msg)
        assert "Grade recorded" in response
        assert f"STU001-{unique_suffix}" in response
        assert "A-" in response
