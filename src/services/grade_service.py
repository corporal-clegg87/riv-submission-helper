import uuid
from datetime import datetime
from typing import Dict, Tuple, Optional
from ..storage import Database
from ..models import Grade, EmailMessage, Teacher

class GradeService:
    """Service responsible for grade processing and validation."""
    
    def __init__(self, db: Database):
        self.db = db
        self._cache = {}
    
    def process_grade(self, grade_data: dict, email_msg: EmailMessage) -> str:
        """Process grade with validation."""
        assignment_code = grade_data['assignment_code']
        student_id = grade_data['student_id']
        
        # Validate teacher is whitelisted
        teacher = self._validate_teacher_authorization(email_msg.from_email)
        if not teacher:
            email_msg.parse_result = 'TEACHER_NOT_WHITELISTED'
            self.db.save_email_message(email_msg)
            return f"Error: Email {email_msg.from_email} is not authorized to grade assignments."
        
        # Find assignment
        assignment = self.db.get_assignment_by_code(assignment_code)
        if not assignment:
            email_msg.parse_result = 'ASSIGNMENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return f"Assignment {assignment_code} not found."
        
        # Check if student has submitted
        submission = self.db.get_submission_by_assignment_and_student(assignment.id, student_id)
        if not submission:
            email_msg.parse_result = 'NO_SUBMISSION_FOUND'
            self.db.save_email_message(email_msg)
            return f"No submission found for student {student_id} on assignment {assignment_code}."
        
        # Create grade
        grade = Grade(
            id=str(uuid.uuid4()),
            assignment_id=assignment.id,
            student_id=student_id,
            grade_value=grade_data['grade_value'],
            feedback_text=grade_data.get('feedback_text', ''),
            graded_at=datetime.utcnow()
        )
        
        self.db.save_grade(grade)
        
        email_msg.parse_result = f'GRADE_RECEIVED:{grade.id}'
        self.db.save_email_message(email_msg)
        
        return f"Grade recorded for student {student_id} on assignment {assignment_code}: {grade.grade_value}"
    
    def process_return(self, return_data: Tuple[str, str, Dict], email_msg: EmailMessage) -> str:
        """Process return (legacy grade format)."""
        assignment_code, student_id, grade_data = return_data
        
        # Find assignment
        assignment = self.db.get_assignment_by_code(assignment_code)
        if not assignment:
            email_msg.parse_result = 'ASSIGNMENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return f"Assignment {assignment_code} not found."
        
        # Check if student has submitted
        submission = self.db.get_submission_by_assignment_and_student(assignment.id, student_id)
        if not submission:
            email_msg.parse_result = 'NO_SUBMISSION_FOUND'
            self.db.save_email_message(email_msg)
            return f"No submission found for student {student_id} on assignment {assignment_code}."
        
        # Create grade
        grade = Grade(
            id=str(uuid.uuid4()),
            assignment_id=assignment.id,
            student_id=student_id,
            grade_value=grade_data.get('grade', ''),
            feedback_text=grade_data.get('feedback', ''),
            graded_at=datetime.utcnow()
        )
        
        self.db.save_grade(grade)
        
        email_msg.parse_result = f'GRADE_RECEIVED:{grade.id}'
        self.db.save_email_message(email_msg)
        
        return f"Grade recorded for student {student_id} on assignment {assignment_code}: {grade.grade_value}"
    
    def _validate_teacher_authorization(self, email: str) -> Optional[Teacher]:
        """Validate teacher is authorized. Returns Teacher or None."""
        if email not in self._cache:
            self._cache[email] = self.db.get_teacher_by_email(email)
        return self._cache[email]
