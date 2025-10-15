import uuid
from datetime import datetime, timedelta
from typing import Optional
from .parser import parse_assignment_email, parse_submission_email, parse_grade_email, parse_return_email
from .storage import Database
from .models import Assignment, Submission, Grade, EmailMessage, Teacher, Class

class EmailProcessor:
    def __init__(self, db: Database):
        self.db = db
        self._cache = {}  # Simple session cache for email processing
    
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
        assignment_data = parse_assignment_email(email_content, subject)
        if assignment_data:
            return self._handle_assignment(assignment_data, email_msg)
        
        # Try to parse as submission
        submission_data = parse_submission_email(email_content, subject)
        if submission_data:
            return self._handle_submission(submission_data, email_msg)
        
        # Try to parse as grade
        grade_data = parse_grade_email(email_content, subject)
        if grade_data:
            return self._handle_grade(grade_data, email_msg)
        
        # Try to parse as return (legacy)
        return_data = parse_return_email(email_content, subject)
        if return_data:
            return self._handle_return(return_data, email_msg)
        
        # Unknown command
        email_msg.parse_result = 'UNKNOWN_COMMAND'
        self.db.save_email_message(email_msg)
        return "Unknown command. Please use ASSIGN, SUBMIT, or GRADE format."
    
    def _validate_teacher_authorization(self, email: str) -> Optional[Teacher]:
        """Validate teacher is authorized. Returns Teacher or None."""
        if email not in self._cache:
            self._cache[email] = self.db.get_teacher_by_email(email)
        return self._cache[email]
    
    def _validate_class_exists(self, class_name: str) -> Optional[Class]:
        """Validate class exists. Returns Class or None."""
        cache_key = f"class_{class_name}"
        if cache_key not in self._cache:
            self._cache[cache_key] = self.db.get_class_by_name(class_name)
        return self._cache[cache_key]
    
    def _handle_assignment(self, assignment_data: dict, email_msg: EmailMessage) -> str:
        # Validate teacher is whitelisted
        teacher = self._validate_teacher_authorization(email_msg.from_email)
        if not teacher:
            email_msg.parse_result = 'TEACHER_NOT_WHITELISTED'
            self.db.save_email_message(email_msg)
            return f"Error: Email {email_msg.from_email} is not authorized to create assignments."
        
        # Validate class exists
        class_obj = self._validate_class_exists(assignment_data['class_name'])
        if not class_obj:
            email_msg.parse_result = 'CLASS_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return f"Error: Class '{assignment_data['class_name']}' not found."
        
        # Create assignment object
        assignment = Assignment(
            id=str(uuid.uuid4()),
            code=assignment_data['code'],
            class_id=class_obj.id,
            title=assignment_data['title'],
            instructions=assignment_data.get('instructions', ''),
            deadline_at=assignment_data['deadline_at'],
            deadline_tz='CT',
            created_by_teacher_id=teacher.id,
            status='SCHEDULED',
            grace_days=7,
            created_at=datetime.utcnow()
        )
        
        # Save assignment
        self.db.save_assignment(assignment)
        
        # Log success
        email_msg.parse_result = f'ASSIGNMENT_CREATED:{assignment.code}'
        self.db.save_email_message(email_msg)
        
        return f"Assignment '{assignment.title}' created successfully. Code: {assignment.code}"
    
    def _handle_submission(self, submission_data: tuple, email_msg: EmailMessage) -> str:
        assignment_code, student_id = submission_data
        
        # Find assignment
        assignment = self.db.get_assignment_by_code(assignment_code)
        if not assignment:
            email_msg.parse_result = 'ASSIGNMENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return f"Assignment {assignment_code} not found."
        
        # Validate student exists
        student = self.db.get_student_by_id(student_id)
        if not student:
            email_msg.parse_result = 'STUDENT_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return f"Student {student_id} not found."
        
        # Validate student is enrolled in the class
        if not self.db.is_student_enrolled_in_class(student_id, assignment.class_id):
            email_msg.parse_result = 'STUDENT_NOT_ENROLLED'
            self.db.save_email_message(email_msg)
            return f"Student {student_id} is not enrolled in this class."
        
        # Check if already submitted
        existing = self.db.get_submission_by_assignment_and_student(assignment.id, student_id)
        if existing:
            email_msg.parse_result = 'DUPLICATE_SUBMISSION'
            self.db.save_email_message(email_msg)
            return "Submission already received. Contact admin to request changes."
        
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
    
    def _handle_grade(self, grade_data: dict, email_msg: EmailMessage) -> str:
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
