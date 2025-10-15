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

def test_optimized_queries():
    """Test optimized query methods prevent N+1 queries."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = f"sqlite:///{tmp.name}"
    
    try:
        db = Database(db_path)
        
        # Setup minimal test data
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
        
        # Test get_all_assignments_with_classes
        results = db.get_all_assignments_with_classes()
        assert isinstance(results, list)
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
        assert len(results) == 1
        assignment_result, class_name = results[0]
        assert assignment_result.code == "ENG7-0115"
        assert class_name == "English 7"
        
        # Test get_assignment_with_class_by_code
        result = db.get_assignment_with_class_by_code("ENG7-0115")
        assert result is not None
        assignment, class_name = result
        assert assignment.code == "ENG7-0115"
        assert class_name == "English 7"
        
    finally:
        if os.path.exists(db_path.replace("sqlite:///", "")):
            os.unlink(db_path.replace("sqlite:///", ""))

def test_performance_improvement():
    """Benchmark N+1 fix performance."""
    import time
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = f"sqlite:///{tmp.name}"
    
    try:
        db = Database(db_path)
        
        # Setup test data with multiple assignments
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
        
        # Create 10 assignments
        for i in range(10):
            assignment = Assignment(
                id=f"test-{i}",
                code=f"ENG7-{i:02d}15",
                class_id="class-1",
                title=f"Test Assignment {i}",
                instructions="Test instructions",
                deadline_at=datetime(2025, 1, 15, 23, 59),
                deadline_tz="CT",
                created_by_teacher_id="teacher-1",
                status="SCHEDULED",
                grace_days=7,
                created_at=datetime.utcnow()
            )
            db.save_assignment(assignment)
        
        # Test optimized method
        start = time.time()
        results = db.get_all_assignments_with_classes()
        optimized_time = time.time() - start
        
        # Verify results
        assert len(results) == 10
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
        
        # Performance should be fast (under 0.1 seconds for 10 records)
        assert optimized_time < 0.1
        
    finally:
        if os.path.exists(db_path.replace("sqlite:///", "")):
            os.unlink(db_path.replace("sqlite:///", ""))
