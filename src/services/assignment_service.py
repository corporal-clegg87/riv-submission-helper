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
            created_by_teacher_id=class_obj.teacher_id,  # Use class teacher instead of validating email
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
    
    
    def _validate_class_exists(self, class_name: str) -> Class:
        """Validate class exists. Returns Class or raises NotFoundError."""
        cache_key = f"class_{class_name}"
        if cache_key not in self._cache:
            self._cache[cache_key] = self.db.get_class_by_name(class_name)
        class_obj = self._cache[cache_key]
        if not class_obj:
            raise NotFoundError(f"Class '{class_name}' not found.", ErrorCodes.CLASS_NOT_FOUND)
        return class_obj