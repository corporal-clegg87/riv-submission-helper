import uuid
from datetime import datetime
from typing import Dict, Tuple, Optional
from ..exceptions import AuthorizationError, NotFoundError, ErrorCodes
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
        try:
            teacher = self._validate_teacher_authorization(email_msg.from_email)
        except AuthorizationError as e:
            email_msg.parse_result = 'TEACHER_NOT_WHITELISTED'
            self.db.save_email_message(email_msg)
            return str(e)
        
        # Find assignment
        try:
            assignment = self.db.get_assignment_by_code(assignment_code)
        except NotFoundError as e:
            email_msg.parse_result = 'ASSIGNMENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return str(e)
        
        # Check if student has submitted
        try:
            submission = self.db.get_submission_by_assignment_and_student(assignment.id, student_id)
        except NotFoundError as e:
            email_msg.parse_result = 'NO_SUBMISSION_FOUND'
            self.db.save_email_message(email_msg)
            return str(e)
        
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
        try:
            assignment = self.db.get_assignment_by_code(assignment_code)
        except NotFoundError as e:
            email_msg.parse_result = 'ASSIGNMENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return str(e)
        
        # Check if student has submitted
        try:
            submission = self.db.get_submission_by_assignment_and_student(assignment.id, student_id)
        except NotFoundError as e:
            email_msg.parse_result = 'NO_SUBMISSION_FOUND'
            self.db.save_email_message(email_msg)
            return str(e)
        
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
    
    def _validate_teacher_authorization(self, email: str) -> Teacher:
        """Validate teacher is authorized. Returns Teacher or raises AuthorizationError."""
        if email not in self._cache:
            try:
                self._cache[email] = self.db.get_teacher_by_email(email)
            except NotFoundError:
                raise AuthorizationError(f"Email {email} is not authorized to grade assignments.", ErrorCodes.TEACHER_NOT_WHITELISTED)
        teacher = self._cache[email]
        if not teacher:
            raise AuthorizationError(f"Email {email} is not authorized to grade assignments.", ErrorCodes.TEACHER_NOT_WHITELISTED)
        return teacher
