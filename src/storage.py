import json
import uuid
import os
from typing import Optional, List
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .models import (
    Assignment, Submission, Grade, EmailMessage, Student, Teacher, Class, Term, Enrollment, Parent,
    AssignmentDB, SubmissionDB, GradeDB, EmailMessageDB, StudentDB, TeacherDB, ClassDB, TermDB, EnrollmentDB, ParentDB
)
from datetime import datetime

class Database:
    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            db_url = os.getenv('DATABASE_URL', 'postgresql://localhost/riv_assignments')
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        from .models import Base
        Base.metadata.create_all(self.engine)
    
    def save_assignment(self, assignment: Assignment) -> None:
        with self.SessionLocal() as session:
            db_assignment = AssignmentDB(
                id=assignment.id,
                code=assignment.code,
                class_id=assignment.class_id,
                title=assignment.title,
                instructions=assignment.instructions,
                deadline_at=assignment.deadline_at,
                deadline_tz=assignment.deadline_tz,
                created_by_teacher_id=assignment.created_by_teacher_id,
                status=assignment.status,
                grace_days=assignment.grace_days,
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
                class_id=db_assignment.class_id,
                title=db_assignment.title,
                instructions=db_assignment.instructions,
                deadline_at=db_assignment.deadline_at,
                deadline_tz=db_assignment.deadline_tz,
                created_by_teacher_id=db_assignment.created_by_teacher_id,
                status=db_assignment.status,
                grace_days=db_assignment.grace_days,
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

    # Core model methods
    def save_student(self, student: Student) -> None:
        with self.SessionLocal() as session:
            db_student = StudentDB(
                id=student.id,
                student_id=student.student_id,
                first_name=student.first_name,
                last_name=student.last_name,
                email=student.email,
                status=student.status
            )
            session.add(db_student)
            session.commit()

    def get_student_by_id(self, student_id: str) -> Optional[Student]:
        with self.SessionLocal() as session:
            db_student = session.query(StudentDB).filter_by(student_id=student_id).first()
            if not db_student:
                return None
            return Student(
                id=db_student.id,
                student_id=db_student.student_id,
                first_name=db_student.first_name,
                last_name=db_student.last_name,
                email=db_student.email,
                status=db_student.status
            )

    def save_teacher(self, teacher: Teacher) -> None:
        with self.SessionLocal() as session:
            db_teacher = TeacherDB(
                id=teacher.id,
                email=teacher.email,
                first_name=teacher.first_name,
                last_name=teacher.last_name,
                status=teacher.status
            )
            session.add(db_teacher)
            session.commit()

    def get_teacher_by_email(self, email: str) -> Optional[Teacher]:
        with self.SessionLocal() as session:
            db_teacher = session.query(TeacherDB).filter_by(email=email).first()
            if not db_teacher:
                return None
            return Teacher(
                id=db_teacher.id,
                email=db_teacher.email,
                first_name=db_teacher.first_name,
                last_name=db_teacher.last_name,
                status=db_teacher.status
            )

    def save_class(self, class_obj: Class) -> None:
        with self.SessionLocal() as session:
            db_class = ClassDB(
                id=class_obj.id,
                term_id=class_obj.term_id,
                name=class_obj.name,
                subject=class_obj.subject,
                teacher_id=class_obj.teacher_id,
                roster_version=class_obj.roster_version,
                status=class_obj.status
            )
            session.add(db_class)
            session.commit()

    def get_class_by_name(self, name: str) -> Optional[Class]:
        with self.SessionLocal() as session:
            db_class = session.query(ClassDB).filter_by(name=name).first()
            if not db_class:
                return None
            return Class(
                id=db_class.id,
                term_id=db_class.term_id,
                name=db_class.name,
                subject=db_class.subject,
                teacher_id=db_class.teacher_id,
                roster_version=db_class.roster_version,
                status=db_class.status
            )

    def save_term(self, term: Term) -> None:
        with self.SessionLocal() as session:
            db_term = TermDB(
                id=term.id,
                name=term.name.value,
                year=term.year,
                start_date=term.start_date,
                end_date=term.end_date
            )
            session.add(db_term)
            session.commit()

    def save_parent(self, parent: Parent) -> None:
        with self.SessionLocal() as session:
            db_parent = ParentDB(
                id=parent.id,
                email=parent.email,
                first_name=parent.first_name,
                last_name=parent.last_name,
                status=parent.status
            )
            session.add(db_parent)
            session.commit()

    def save_enrollment(self, enrollment: Enrollment) -> None:
        with self.SessionLocal() as session:
            db_enrollment = EnrollmentDB(
                id=enrollment.id,
                class_id=enrollment.class_id,
                student_id=enrollment.student_id,
                parent_id=enrollment.parent_id,
                active=enrollment.active,
                joined_at=enrollment.joined_at,
                left_at=enrollment.left_at
            )
            session.add(db_enrollment)
            session.commit()

    def get_enrollments_by_class(self, class_id: str) -> List[Enrollment]:
        with self.SessionLocal() as session:
            db_enrollments = session.query(EnrollmentDB).filter_by(class_id=class_id, active=True).all()
            return [
                Enrollment(
                    id=enrollment.id,
                    class_id=enrollment.class_id,
                    student_id=enrollment.student_id,
                    parent_id=enrollment.parent_id,
                    active=enrollment.active,
                    joined_at=enrollment.joined_at,
                    left_at=enrollment.left_at
                )
                for enrollment in db_enrollments
            ]

    def is_student_enrolled_in_class(self, student_id: str, class_id: str) -> bool:
        with self.SessionLocal() as session:
            enrollment = session.query(EnrollmentDB).filter_by(
                student_id=student_id, 
                class_id=class_id, 
                active=True
            ).first()
            return enrollment is not None
