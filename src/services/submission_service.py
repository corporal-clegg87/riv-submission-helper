import uuid
from datetime import datetime, timedelta
from typing import Tuple
from ..exceptions import ValidationError, NotFoundError, ErrorCodes
from ..storage import Database
from ..models import Submission, EmailMessage

class SubmissionService:
    """Service responsible for submission processing and validation."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def process_submission(self, submission_data: Tuple[str, str], email_msg: EmailMessage) -> str:
        """Process submission with validation."""
        assignment_code, student_id = submission_data
        
        # Find assignment
        try:
            assignment = self.db.get_assignment_by_code(assignment_code)
        except NotFoundError as e:
            email_msg.parse_result = 'ASSIGNMENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return str(e)
        
        # Validate student exists
        try:
            student = self.db.get_student_by_id(student_id)
        except NotFoundError as e:
            email_msg.parse_result = 'STUDENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return str(e)
        
        # Validate student is enrolled in the class
        if not self.db.is_student_enrolled_in_class(student_id, assignment.class_id):
            email_msg.parse_result = 'STUDENT_NOT_ENROLLED'
            self.db.save_email_message(email_msg)
            raise ValidationError(f"Student {student_id} is not enrolled in this class.", ErrorCodes.STUDENT_NOT_ENROLLED)
        
        # Check if already submitted
        existing = self.db.get_submission_by_assignment_and_student(assignment.id, student_id)
        if existing:
            email_msg.parse_result = 'DUPLICATE_SUBMISSION'
            self.db.save_email_message(email_msg)
            raise ValidationError("Submission already received. Contact admin to request changes.", ErrorCodes.DUPLICATE_SUBMISSION)
        
        # Determine if on-time (including grace period)
        now = datetime.utcnow()
        grace_deadline = assignment.deadline_at + timedelta(days=assignment.grace_days)
        on_time = now <= assignment.deadline_at
        
        # Create submission
        submission = Submission(
            id=str(uuid.uuid4()),
            assignment_id=assignment.id,
            student_id=student_id,
            received_at=now,
            on_time=on_time,
            status='RECEIVED'
        )
        
        self.db.save_submission(submission)
        
        email_msg.parse_result = f'SUBMISSION_RECEIVED:{submission.id}'
        self.db.save_email_message(email_msg)
        
        status = "on time" if on_time else "late"
        return f"Submission received {status} for {assignment_code} (Student {student_id})."
