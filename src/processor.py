import uuid
from datetime import datetime, timedelta
from typing import Optional
from .storage import Database
from .models import Assignment, Submission, Grade, EmailMessage, Teacher, Class
from .services.email_parser import EmailParser
from .services.assignment_service import AssignmentService
from .services.submission_service import SubmissionService
from .services.grade_service import GradeService

class EmailProcessor:
    def __init__(self, db: Database):
        self.db = db
        self.email_parser = EmailParser()
        self.assignment_service = AssignmentService(db)
        self.submission_service = SubmissionService(db)
        self.grade_service = GradeService(db)
    
    def process_email(self, email_content: str, from_email: str, to_emails: list, subject: str, message_id: str) -> str:
        """Process incoming email and return response message."""
        # Log the email
        email_msg = EmailMessage(
            id=str(uuid.uuid4()),
            direction='IN',
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            message_id=message_id,
            processed_at=datetime.utcnow(),
            parse_result=None
        )
        
        # Parse email to determine type and data
        parsed = self.email_parser.parse_email(email_content, subject)
        
        if parsed['type'] == 'assignment':
            return self.assignment_service.create_assignment(parsed['data'], email_msg)
        elif parsed['type'] == 'submission':
            return self.submission_service.process_submission(parsed['data'], email_msg)
        elif parsed['type'] == 'grade':
            return self.grade_service.process_grade(parsed['data'], email_msg)
        elif parsed['type'] == 'return':
            return self.grade_service.process_return(parsed['data'], email_msg)
        
        # Unknown command
        email_msg.parse_result = 'UNKNOWN_COMMAND'
        self.db.save_email_message(email_msg)
        return "Unknown command. Please use ASSIGN, SUBMIT, or GRADE format."
