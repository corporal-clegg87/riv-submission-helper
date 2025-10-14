#!/usr/bin/env python3
"""
Seed development data for RIV Assignment System.
Creates sample teachers, students, classes, and enrollments for testing.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.storage import Database
from src.models import Student, Teacher, Class, Term, Parent, Enrollment

def seed_development_data():
    """Create sample data for development and testing."""
    print("🌱 Seeding development data...")
    
    db = Database()
    
    # Create current term
    current_term = Term(
        id=str(uuid.uuid4()),
        name="FALL",
        year=2024,
        start_date=datetime(2024, 9, 1),
        end_date=datetime(2024, 12, 15)
    )
    db.save_term(current_term)
    print(f"✅ Created term: {current_term.name} {current_term.year}")
    
    # Create teachers
    teachers_data = [
        ("teacher@rivendell-academy.co.uk", "Jane", "Smith"),
        ("john.doe@rivendell-academy.co.uk", "John", "Doe"),
        ("mary.wilson@rivendell-academy.co.uk", "Mary", "Wilson")
    ]
    
    teachers = []
    for email, first_name, last_name in teachers_data:
        teacher = Teacher(
            id=str(uuid.uuid4()),
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        db.save_teacher(teacher)
        teachers.append(teacher)
        print(f"✅ Created teacher: {first_name} {last_name} ({email})")
    
    # Create parents
    parents_data = [
        ("parent1@example.com", "Alice", "Johnson"),
        ("parent2@example.com", "Bob", "Brown"),
        ("parent3@example.com", "Carol", "Davis"),
        ("parent4@example.com", "David", "Miller"),
        ("parent5@example.com", "Eve", "Wilson")
    ]
    
    parents = []
    for email, first_name, last_name in parents_data:
        parent = Parent(
            id=str(uuid.uuid4()),
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        db.save_parent(parent)
        parents.append(parent)
        print(f"✅ Created parent: {first_name} {last_name} ({email})")
    
    # Create students
    students_data = [
        ("STU001", "Emma", "Johnson"),
        ("STU002", "Liam", "Brown"),
        ("STU003", "Olivia", "Davis"),
        ("STU004", "Noah", "Miller"),
        ("STU005", "Ava", "Wilson")
    ]
    
    students = []
    for student_id, first_name, last_name in students_data:
        student = Student(
            id=str(uuid.uuid4()),
            student_id=student_id,
            first_name=first_name,
            last_name=last_name
        )
        db.save_student(student)
        students.append(student)
        print(f"✅ Created student: {first_name} {last_name} ({student_id})")
    
    # Create classes
    classes_data = [
        ("English 7", "English", teachers[0].id),
        ("Math 7", "Mathematics", teachers[1].id),
        ("Science 7", "Science", teachers[2].id)
    ]
    
    classes = []
    for name, subject, teacher_id in classes_data:
        class_obj = Class(
            id=str(uuid.uuid4()),
            term_id=current_term.id,
            name=name,
            subject=subject,
            teacher_id=teacher_id
        )
        db.save_class(class_obj)
        classes.append(class_obj)
        print(f"✅ Created class: {name} ({subject})")
    
    # Create enrollments (all students in all classes)
    enrollment_count = 0
    for class_obj in classes:
        for i, student in enumerate(students):
            enrollment = Enrollment(
                id=str(uuid.uuid4()),
                class_id=class_obj.id,
                student_id=student.student_id,
                parent_id=parents[i].id,
                joined_at=datetime.utcnow()
            )
            db.save_enrollment(enrollment)
            enrollment_count += 1
    
    print(f"✅ Created {enrollment_count} enrollments")
    print("\n🎉 Development data seeded successfully!")
    print("\n📧 Test with these emails:")
    print("Teacher: teacher@rivendell-academy.co.uk")
    print("Student: STU001, STU002, STU003, STU004, STU005")
    print("Classes: English 7, Math 7, Science 7")

if __name__ == "__main__":
    seed_development_data()
