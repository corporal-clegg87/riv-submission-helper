import uuid
from datetime import datetime
from typing import Optional
from ..exceptions import ValidationError, AuthorizationError, NotFoundError, ErrorCodes
from ..storage import Database
from ..models import Assignment, Teacher, Class, EmailMessage

class AssignmentService:
    """Service responsible for assignment creation and validation."""
    
    def __init__(self, db: Database):
        self.db = db
        self._cache = {}
    
    def create_assignment(self, assignment_data: dict, email_msg: EmailMessage) -> str:
        """Create assignment with validation."""
        # Validate teacher authorization
        try:
            teacher = self._validate_teacher_authorization(email_msg.from_email)
        except AuthorizationError as e:
            email_msg.parse_result = 'TEACHER_NOT_WHITELISTED'
            self.db.save_email_message(email_msg)
            return str(e)
        
        # Validate class exists
        try:
            class_obj = self._validate_class_exists(assignment_data['class_name'])
        except NotFoundError as e:
            email_msg.parse_result = 'CLASS_NOT_FOUND'
            self.db.save_email_message(email_msg)
            return str(e)
        
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
    
    def _validate_teacher_authorization(self, email: str) -> Teacher:
        """Validate teacher is authorized. Returns Teacher or raises AuthorizationError."""
        if email not in self._cache:
            try:
                self._cache[email] = self.db.get_teacher_by_email(email)
            except NotFoundError:
                raise AuthorizationError(f"Email {email} is not authorized to create assignments.", ErrorCodes.TEACHER_NOT_WHITELISTED)
        teacher = self._cache[email]
        if not teacher:
            raise AuthorizationError(f"Email {email} is not authorized to create assignments.", ErrorCodes.TEACHER_NOT_WHITELISTED)
        return teacher
    
    def _validate_class_exists(self, class_name: str) -> Class:
        """Validate class exists. Returns Class or raises NotFoundError."""
        cache_key = f"class_{class_name}"
        if cache_key not in self._cache:
            self._cache[cache_key] = self.db.get_class_by_name(class_name)
        class_obj = self._cache[cache_key]
        if not class_obj:
            raise NotFoundError(f"Class '{class_name}' not found.", ErrorCodes.CLASS_NOT_FOUND)
        return class_obj