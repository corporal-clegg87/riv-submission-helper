from typing import Dict, Optional, Tuple
from ..exceptions import ValidationError
from ..parser import parse_assignment_email, parse_submission_email, parse_grade_email, parse_return_email

class EmailParser:
    """Service responsible for parsing email content into structured data."""
    
    def parse_assignment(self, content: str, subject: str) -> Optional[Dict]:
        """Parse ASSIGN email and return assignment data or None if invalid."""
        try:
            return parse_assignment_email(content, subject)
        except ValidationError:
            return None
    
    def parse_submission(self, content: str, subject: str) -> Optional[Tuple[str, str]]:
        """Parse SUBMIT email and return (assignment_code, student_id) or None if invalid."""
        try:
            return parse_submission_email(content, subject)
        except ValidationError:
            return None
    
    def parse_grade(self, content: str, subject: str) -> Optional[Dict]:
        """Parse GRADE email and return grade data or None if invalid."""
        try:
            return parse_grade_email(content, subject)
        except ValidationError:
            return None
    
    def parse_return(self, content: str, subject: str) -> Optional[Tuple[str, str, Dict]]:
        """Parse RETURN email and return (assignment_code, student_id, grade_data) or None."""
        try:
            return parse_return_email(content, subject)
        except ValidationError:
            return None
    
    def parse_email(self, content: str, subject: str) -> Dict:
        """Parse email and return type and data."""
        # Try assignment parsing
        assignment_data = self.parse_assignment(content, subject)
        if assignment_data:
            return {'type': 'assignment', 'data': assignment_data}
        
        # Try submission parsing
        submission_data = self.parse_submission(content, subject)
        if submission_data:
            return {'type': 'submission', 'data': submission_data}
        
        # Try grade parsing
        grade_data = self.parse_grade(content, subject)
        if grade_data:
            return {'type': 'grade', 'data': grade_data}
        
        # Try return parsing
        return_data = self.parse_return(content, subject)
        if return_data:
            return {'type': 'return', 'data': return_data}
        
        return {'type': 'unknown', 'data': None}
