#!/usr/bin/env python3
"""
Add test teacher to production database for frontend automation testing.
This script adds teacher@example.com to the production database so it can create assignments.
"""

import sys
import os
import uuid
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.storage import Database
from src.models import Teacher, Class, Term

def add_test_teacher():
    """Add test teacher to production database."""
    print("👨‍🏫 Adding test teacher to production database...")
    
    # Set production environment
    os.environ['GCP_PROJECT_ID'] = 'riv-assignments-1079423826925'
    os.environ['APP_ENVIRONMENT'] = 'production'
    
    try:
        db = Database()
        
        # Check if teacher already exists
        existing_teacher = db.get_teacher_by_email("teacher@example.com")
        if existing_teacher:
            print("✅ Teacher teacher@example.com already exists in database")
            return
        
        # Create test teacher
        teacher = Teacher(
            id=str(uuid.uuid4()),
            email="teacher@example.com",
            first_name="Test",
            last_name="Teacher"
        )
        db.save_teacher(teacher)
        print(f"✅ Created teacher: {teacher.first_name} {teacher.last_name} ({teacher.email})")
        
        # Check if we need to create a class for this teacher
        # Look for existing classes
        existing_classes = db.get_all_classes()
        if not existing_classes:
            print("📚 No classes found, creating test class...")
            
            # Create a test term first
            term = Term(
                id=str(uuid.uuid4()),
                name="FALL",
                year=2024,
                start_date=datetime(2024, 9, 1),
                end_date=datetime(2024, 12, 15)
            )
            db.save_term(term)
            print(f"✅ Created term: {term.name} {term.year}")
            
            # Create test class
            class_obj = Class(
                id=str(uuid.uuid4()),
                term_id=term.id,
                name="Math 7",
                subject="Mathematics",
                teacher_id=teacher.id
            )
            db.save_class(class_obj)
            print(f"✅ Created class: {class_obj.name} ({class_obj.subject})")
        else:
            print(f"📚 Found {len(existing_classes)} existing classes")
        
        print("\n🎉 Test teacher added successfully!")
        print("📧 teacher@example.com can now create assignments in production")
        
    except Exception as e:
        print(f"❌ Error adding test teacher: {e}")
        raise

if __name__ == "__main__":
    add_test_teacher()
