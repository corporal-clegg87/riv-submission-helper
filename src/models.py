from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship, DeclarativeBase

class Base(DeclarativeBase):
    pass

class TermName(str, Enum):
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    FALL = "FALL"
    WINTER = "WINTER"

class Student(BaseModel):
    id: str
    student_id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    status: str = 'ACTIVE'

class Teacher(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    status: str = 'ACTIVE'

class Parent(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str = 'ACTIVE'

class Term(BaseModel):
    id: str
    name: TermName
    year: int
    start_date: datetime
    end_date: datetime

class Class(BaseModel):
    id: str
    term_id: str
    name: str
    subject: Optional[str] = None
    teacher_id: str
    roster_version: int = 1
    status: str = 'ACTIVE'

class Enrollment(BaseModel):
    id: str
    class_id: str
    student_id: str
    parent_id: str
    active: bool = True
    joined_at: datetime
    left_at: Optional[datetime] = None

class Assignment(BaseModel):
    id: str
    code: str
    class_id: str
    title: str
    instructions: Optional[str] = None
    deadline_at: datetime
    deadline_tz: str = 'CT'
    created_by_teacher_id: str
    status: str = 'SCHEDULED'
    grace_days: int = 7
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
    class_id = Column(String, ForeignKey('classes.id'), nullable=False)
    title = Column(String, nullable=False)
    instructions = Column(Text)
    deadline_at = Column(DateTime, nullable=False)
    deadline_tz = Column(String, default='CT')
    created_by_teacher_id = Column(String, ForeignKey('teachers.id'), nullable=False)
    status = Column(String, default='SCHEDULED')
    grace_days = Column(Integer, default=7)
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

class TermDB(Base):
    __tablename__ = 'terms'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

class TeacherDB(Base):
    __tablename__ = 'teachers'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default='ACTIVE')
    __table_args__ = (Index('idx_teacher_email', 'email'),)

class StudentDB(Base):
    __tablename__ = 'students'
    
    id = Column(String, primary_key=True)
    student_id = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    status = Column(String, nullable=False, default='ACTIVE')
    __table_args__ = (Index('idx_student_id', 'student_id'),)

class ParentDB(Base):
    __tablename__ = 'parents'
    
    id = Column(String, primary_key=True)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default='ACTIVE')

class ClassDB(Base):
    __tablename__ = 'classes'
    
    id = Column(String, primary_key=True)
    term_id = Column(String, ForeignKey('terms.id'), nullable=False)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    teacher_id = Column(String, ForeignKey('teachers.id'), nullable=False)
    roster_version = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default='ACTIVE')
    __table_args__ = (Index('idx_class_name', 'name'),)

class EnrollmentDB(Base):
    __tablename__ = 'enrollments'
    
    id = Column(String, primary_key=True)
    class_id = Column(String, ForeignKey('classes.id'), nullable=False)
    student_id = Column(String, ForeignKey('students.id'), nullable=False)
    parent_id = Column(String, ForeignKey('parents.id'), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    joined_at = Column(DateTime, nullable=False)
    left_at = Column(DateTime, nullable=True)
    __table_args__ = (Index('idx_enrollment_lookup', 'student_id', 'class_id', 'active'),)
