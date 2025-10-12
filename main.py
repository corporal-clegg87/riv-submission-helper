#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from src.storage import Database
from src.processor import EmailProcessor
from src.models import Assignment

def main():
    parser = argparse.ArgumentParser(description='RIV Assignment Helper - MVP')
    parser.add_argument('command', choices=['process', 'list', 'status'], help='Command to run')
    parser.add_argument('--email-file', help='Path to email file to process')
    parser.add_argument('--assignment-code', help='Assignment code for status check')
    
    args = parser.parse_args()
    
    db = Database()
    processor = EmailProcessor(db)
    
    if args.command == 'process':
        if not args.email_file:
            print("Error: --email-file required for process command")
            sys.exit(1)
        process_email_file(args.email_file, processor)
    elif args.command == 'list':
        list_assignments(db)
    elif args.command == 'status':
        if not args.assignment_code:
            print("Error: --assignment-code required for status command")
            sys.exit(1)
        show_assignment_status(args.assignment_code, db)

def process_email_file(email_file: str, processor: EmailProcessor):
    """Process an email file (eml format or text)."""
    try:
        with open(email_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple email parsing (for MVP)
        lines = content.split('\n')
        subject = ""
        body = ""
        from_email = ""
        to_emails = []
        message_id = ""
        
        in_body = False
        for line in lines:
            if line.startswith('Subject:'):
                subject = line[8:].strip()
            elif line.startswith('From:'):
                from_email = line[5:].strip()
            elif line.startswith('To:'):
                to_emails = [line[3:].strip()]
            elif line.startswith('Message-ID:'):
                message_id = line[11:].strip()
            elif line == '' and not in_body:
                in_body = True
            elif in_body:
                body += line + '\n'
        
        response = processor.process_email(body, from_email, to_emails, subject, message_id)
        print(f"Response: {response}")
        
    except Exception as e:
        print(f"Error processing email: {e}")
        sys.exit(1)

def list_assignments(db: Database):
    """List all assignments."""
    assignments = db.get_all_assignments()
    if not assignments:
        print("No assignments found.")
        return
    
    print("Assignments:")
    for assignment in assignments:
        print(f"  {assignment.code}: {assignment.title} (Due: {assignment.deadline_at.strftime('%Y-%m-%d %H:%M')} CT)")

def show_assignment_status(assignment_code: str, db: Database):
    """Show status of an assignment."""
    assignment = db.get_assignment_by_code(assignment_code)
    if not assignment:
        print(f"Assignment {assignment_code} not found.")
        return
    
    submissions = db.get_submissions_by_assignment(assignment.id)
    print(f"Assignment: {assignment.title}")
    print(f"Due: {assignment.deadline_at.strftime('%Y-%m-%d %H:%M')} CT")
    print(f"Submissions: {len(submissions)}")
    for submission in submissions:
        status = "on time" if submission.on_time else "late"
        print(f"  Student {submission.student_id}: {status} ({submission.received_at.strftime('%Y-%m-%d %H:%M')} UTC)")

if __name__ == '__main__':
    main()
