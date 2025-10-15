import re
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple
from .models import Assignment

def parse_assignment_email(email_body: str, subject: str) -> Optional[Dict]:
    """Parse ASSIGN email and return assignment data or None if invalid."""
    if not subject.strip().upper().startswith('ASSIGN'):
        return None
    
    # Extract key:value pairs from body
    fields = {}
    for line in email_body.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            fields[key.strip().lower()] = value.strip()
    
    # Validate required fields
    required = ['title', 'class', 'deadline']
    for field in required:
        if field not in fields:
            return None
    
    # Parse deadline (expects YYYY-MM-DD [HH:mm] CT format)
    try:
        deadline_str = fields['deadline'].replace('CT', '').strip()
        if ' ' in deadline_str:
            deadline_at = datetime.strptime(deadline_str, '%Y-%m-%d %H:%M')
        else:
            deadline_at = datetime.strptime(deadline_str, '%Y-%m-%d')
            deadline_at = deadline_at.replace(hour=23, minute=59)
    except ValueError:
        return None
    
    # Generate assignment code
    class_code = fields['class'].replace(' ', '').upper()[:8]
    date_code = deadline_at.strftime('%m%d')
    code = f"{class_code}-{date_code}"
    
    return {
        'code': code,
        'title': fields['title'],
        'class_name': fields['class'],
        'deadline_at': deadline_at,
        'instructions': fields.get('instructions', ''),
        'rubric': fields.get('rubric', '')
    }

def parse_submission_email(email_body: str, subject: str) -> Optional[Tuple[str, str]]:
    """Parse SUBMIT email and return (assignment_code, student_id) or None if invalid."""
    match = re.match(r'SUBMIT\s+(\S+)', subject.upper())
    if not match:
        return None
    
    assignment_code = match.group(1)
    
    # Extract StudentID from body
    student_id = None
    for line in email_body.split('\n'):
        line = line.strip()
        if line.upper().startswith('STUDENTID:'):
            student_id = line.split(':', 1)[1].strip()
            break
    
    if not student_id:
        return None
    
    return (assignment_code, student_id)

def parse_grade_email(email_body: str, subject: str) -> Optional[Dict]:
    """Parse GRADE email and return grade data or None if invalid."""
    match = re.match(r'GRADE\s+(\S+)\s+(\S+)', subject.upper())
    if not match:
        return None
    
    assignment_code = match.group(1)
    student_id = match.group(2)
    
    # Extract grade and feedback from body
    grade_data = {}
    for line in email_body.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            grade_data[key.strip().lower()] = value.strip()
    
    # Validate required fields
    if 'grade' not in grade_data:
        return None
    
    return {
        'assignment_code': assignment_code,
        'student_id': student_id,
        'grade_value': grade_data['grade'],
        'feedback_text': grade_data.get('feedback', '')
    }

def parse_return_email(email_body: str, subject: str) -> Optional[Tuple[str, str, Dict]]:
    """Parse RETURN email and return (assignment_code, student_id, grade_data) or None."""
    match = re.match(r'RETURN\s+(\S+)\s+(\S+)', subject.upper())
    if not match:
        return None
    
    assignment_code = match.group(1)
    student_id = match.group(2)
    
    # Extract grade and feedback
    grade_data = {}
    for line in email_body.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            grade_data[key.strip().lower()] = value.strip()
    
    return (assignment_code, student_id, grade_data)
