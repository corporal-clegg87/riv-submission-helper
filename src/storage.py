import json
import uuid
from typing import Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Assignment, Submission, Grade, EmailMessage, AssignmentDB, SubmissionDB, GradeDB, EmailMessageDB
from datetime import datetime

class Database:
    def __init__(self, db_path: str = 'assignments.db'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        from .models import Base
        Base.metadata.create_all(self.engine)
    
    def save_assignment(self, assignment: Assignment) -> None:
        with self.SessionLocal() as session:
            db_assignment = AssignmentDB(
                id=assignment.id,
                code=assignment.code,
                title=assignment.title,
                class_name=assignment.class_name,
                deadline_at=assignment.deadline_at,
                deadline_tz=assignment.deadline_tz,
                instructions=assignment.instructions,
                status=assignment.status,
                created_at=assignment.created_at
            )
            session.add(db_assignment)
            session.commit()
    
    def get_assignment_by_code(self, code: str) -> Optional[Assignment]:
        with self.SessionLocal() as session:
            db_assignment = session.query(AssignmentDB).filter_by(code=code).first()
            if not db_assignment:
                return None
            return Assignment(
                id=db_assignment.id,
                code=db_assignment.code,
                title=db_assignment.title,
                class_name=db_assignment.class_name,
                deadline_at=db_assignment.deadline_at,
                deadline_tz=db_assignment.deadline_tz,
                instructions=db_assignment.instructions,
                status=db_assignment.status,
                created_at=db_assignment.created_at
            )
    
    def get_all_assignments(self) -> List[Assignment]:
        with self.SessionLocal() as session:
            db_assignments = session.query(AssignmentDB).all()
            return [
                Assignment(
                    id=assignment.id,
                    code=assignment.code,
                    title=assignment.title,
                    class_name=assignment.class_name,
                    deadline_at=assignment.deadline_at,
                    deadline_tz=assignment.deadline_tz,
                    instructions=assignment.instructions,
                    status=assignment.status,
                    created_at=assignment.created_at
                )
                for assignment in db_assignments
            ]
    
    def save_submission(self, submission: Submission) -> None:
        with self.SessionLocal() as session:
            db_submission = SubmissionDB(
                id=submission.id,
                assignment_id=submission.assignment_id,
                student_id=submission.student_id,
                received_at=submission.received_at,
                on_time=submission.on_time,
                status=submission.status
            )
            session.add(db_submission)
            session.commit()
    
    def get_submission_by_assignment_and_student(self, assignment_id: str, student_id: str) -> Optional[Submission]:
        with self.SessionLocal() as session:
            db_submission = session.query(SubmissionDB).filter_by(
                assignment_id=assignment_id, 
                student_id=student_id
            ).first()
            if not db_submission:
                return None
            return Submission(
                id=db_submission.id,
                assignment_id=db_submission.assignment_id,
                student_id=db_submission.student_id,
                received_at=db_submission.received_at,
                on_time=db_submission.on_time,
                status=db_submission.status
            )
    
    def get_submissions_by_assignment(self, assignment_id: str) -> List[Submission]:
        with self.SessionLocal() as session:
            db_submissions = session.query(SubmissionDB).filter_by(assignment_id=assignment_id).all()
            return [
                Submission(
                    id=submission.id,
                    assignment_id=submission.assignment_id,
                    student_id=submission.student_id,
                    received_at=submission.received_at,
                    on_time=submission.on_time,
                    status=submission.status
                )
                for submission in db_submissions
            ]
    
    def save_grade(self, grade: Grade) -> None:
        with self.SessionLocal() as session:
            db_grade = GradeDB(
                id=grade.id,
                assignment_id=grade.assignment_id,
                student_id=grade.student_id,
                grade_value=grade.grade_value,
                feedback_text=grade.feedback_text,
                graded_at=grade.graded_at
            )
            session.add(db_grade)
            session.commit()
    
    def save_email_message(self, email: EmailMessage) -> None:
        with self.SessionLocal() as session:
            db_email = EmailMessageDB(
                id=email.id,
                direction=email.direction,
                from_email=email.from_email,
                to_emails=json.dumps(email.to_emails),
                subject=email.subject,
                message_id=email.message_id,
                processed_at=email.processed_at,
                parse_result=email.parse_result
            )
            session.add(db_email)
            session.commit()
