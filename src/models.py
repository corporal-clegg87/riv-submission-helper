from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Assignment(BaseModel):
    id: str
    code: str
    title: str
    class_name: str
    deadline_at: datetime
    deadline_tz: str = 'CT'
    instructions: Optional[str] = None
    status: str = 'SCHEDULED'
    created_at: datetime

class Submission(BaseModel):
    id: str
    assignment_id: str
    student_id: str
    received_at: datetime
    on_time: bool
    status: str = 'RECEIVED'

class Grade(BaseModel):
    id: str
    assignment_id: str
    student_id: str
    grade_value: str
    feedback_text: Optional[str] = None
    graded_at: datetime

class EmailMessage(BaseModel):
    id: str
    direction: str  # 'IN' or 'OUT'
    from_email: str
    to_emails: List[str]
    subject: str
    message_id: str
    processed_at: datetime
    parse_result: Optional[str] = None

class AssignmentDB(Base):
    __tablename__ = 'assignments'
    
    id = Column(String, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    deadline_at = Column(DateTime, nullable=False)
    deadline_tz = Column(String, default='CT')
    instructions = Column(Text)
    status = Column(String, default='SCHEDULED')
    created_at = Column(DateTime, default=datetime.utcnow)

class SubmissionDB(Base):
    __tablename__ = 'submissions'
    
    id = Column(String, primary_key=True)
    assignment_id = Column(String, nullable=False)
    student_id = Column(String, nullable=False)
    received_at = Column(DateTime, nullable=False)
    on_time = Column(Boolean, nullable=False)
    status = Column(String, default='RECEIVED')

class GradeDB(Base):
    __tablename__ = 'grades'
    
    id = Column(String, primary_key=True)
    assignment_id = Column(String, nullable=False)
    student_id = Column(String, nullable=False)
    grade_value = Column(String, nullable=False)
    feedback_text = Column(Text)
    graded_at = Column(DateTime, default=datetime.utcnow)

class EmailMessageDB(Base):
    __tablename__ = 'email_messages'
    
    id = Column(String, primary_key=True)
    direction = Column(String, nullable=False)
    from_email = Column(String, nullable=False)
    to_emails = Column(Text)  # JSON string
    subject = Column(String, nullable=False)
    message_id = Column(String, unique=True, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    parse_result = Column(Text)
