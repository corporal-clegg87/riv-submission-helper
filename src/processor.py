import uuid
from datetime import datetime
from typing import Optional
from .parser import parse_assignment_email, parse_submission_email, parse_return_email
from .storage import Database
from .models import Assignment, Submission, Grade, EmailMessage

class EmailProcessor:
    def __init__(self, db: Database):
        self.db = db
    
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
        
        # Try to parse as assignment
        assignment = parse_assignment_email(email_content, subject)
        if assignment:
            return self._handle_assignment(assignment, email_msg)
        
        # Try to parse as submission
        submission_data = parse_submission_email(email_content, subject)
        if submission_data:
            return self._handle_submission(submission_data, email_msg)
        
        # Try to parse as return
        return_data = parse_return_email(email_content, subject)
        if return_data:
            return self._handle_return(return_data, email_msg)
        
        # Unknown command
        email_msg.parse_result = 'UNKNOWN_COMMAND'
        self.db.save_email_message(email_msg)
        return "Unknown command. Please use ASSIGN, SUBMIT, or RETURN format."
    
    def _handle_assignment(self, assignment: Assignment, email_msg: EmailMessage) -> str:
        # Save assignment
        self.db.save_assignment(assignment)
        
        # Log success
        email_msg.parse_result = f'ASSIGNMENT_CREATED:{assignment.code}'
        self.db.save_email_message(email_msg)
        
        return f"Assignment '{assignment.title}' created with code {assignment.code}. Deadline: {assignment.deadline_at.strftime('%Y-%m-%d %H:%M')} CT."
    
    def _handle_submission(self, submission_data: tuple, email_msg: EmailMessage) -> str:
        assignment_code, student_id = submission_data
        
        # Find assignment
        assignment = self.db.get_assignment_by_code(assignment_code)
        if not assignment:
            email_msg.parse_result = 'ASSIGNMENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return f"Assignment {assignment_code} not found."
        
        # Check if already submitted
        existing = self.db.get_submission_by_assignment_and_student(assignment.id, student_id)
        if existing:
            email_msg.parse_result = 'DUPLICATE_SUBMISSION'
            self.db.save_email_message(email_msg)
            return "Submission already received. Contact admin to request changes."
        
        # Determine if on-time
        now = datetime.utcnow()
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
    
    def _handle_return(self, return_data: tuple, email_msg: EmailMessage) -> str:
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
