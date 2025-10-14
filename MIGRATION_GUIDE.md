# Migration Guide: Week 1-2 MVP Implementation

This guide documents the changes made to implement the Week 1-2 MVP requirements for the RIV Assignment System.

## Overview

The system has been migrated from a basic SQLite implementation to a production-ready PostgreSQL setup with proper data models, validation, and admin interface.

## Key Changes

### 1. Database Migration
- **From**: SQLite with basic tables
- **To**: PostgreSQL with full relational schema
- **Migration Tool**: Alembic for versioned schema management
- **Connection**: Configurable via `DATABASE_URL` environment variable

### 2. Core Models Implementation
Added complete data models as specified in the project plan:

- **Student**: Student records with ID, name, email, status
- **Teacher**: Teacher records with email whitelist validation
- **Parent**: Parent/guardian records
- **Term**: Academic terms (SPRING/SUMMER/FALL/WINTER)
- **Class**: Classes linked to terms and teachers
- **Enrollment**: Student-class relationships with parent links

### 3. Enhanced Email Processing
- **ASSIGN**: Create assignments with teacher whitelist validation
- **SUBMIT**: Submit work with student enrollment validation
- **GRADE**: Grade submissions with teacher authorization
- **Validation**: Proper error handling and user feedback

### 4. Admin Interface
- Assignment list view with filtering
- Assignment details with submission tracking
- Real-time status updates
- Responsive design for admin use

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup

#### Option A: Local PostgreSQL
```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb riv_assignments

# Set environment variable
export DATABASE_URL="postgresql://username:password@localhost:5432/riv_assignments"
```

#### Option B: Cloud SQL (Production)
```bash
# Set Cloud SQL connection string
export DATABASE_URL="postgresql://user:pass@/riv_assignments?host=/cloudsql/project:region:instance"
```

### 3. Run Migrations
```bash
# Apply database schema
alembic upgrade head
```

### 4. Seed Data (Development)
```python
# Create sample data for testing
python scripts/seed_data.py
```

### 5. Start Application
```bash
# Development server
uvicorn src.api:app --reload

# Production server
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://localhost/riv_assignments

# Gmail API (optional for MVP)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GMAIL_USER_EMAIL=assignments@yourdomain.com

# Application
APP_ENVIRONMENT=development
APP_CORS_ORIGINS=*
```

## Testing

### Run Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_processor.py -v

# With coverage
pytest --cov=src tests/
```

### Test Database
Tests use temporary SQLite databases for speed and isolation.

## API Endpoints

### Email Processing
- `POST /api/process-email` - Process ASSIGN/SUBMIT/GRADE emails

### Assignment Management
- `GET /api/assignments` - List all assignments
- `GET /api/assignments/{code}` - Get assignment details
- `GET /api/assignments/{code}/status` - Get assignment with submissions

### Gmail Integration
- `POST /api/gmail-webhook` - Pub/Sub webhook for Gmail notifications

## Email Format Examples

### Create Assignment
```
Subject: ASSIGN
Body:
Title: Essay on Climate Change
Class: English 7
Deadline: 2025-01-15 23:59 CT
Instructions: Write a 500-word essay on climate change impacts.
```

### Submit Work
```
Subject: SUBMIT ENG7-0115
Body:
StudentID: STU001
[Attach essay file]
```

### Grade Work
```
Subject: GRADE ENG7-0115 STU001
Body:
Grade: A-
Feedback: Excellent analysis of climate impacts. Well-structured arguments.
```

## Validation Rules

### Teacher Whitelist
- Only emails from the `teachers` table can create assignments or grades
- Unauthorized emails receive error messages

### Student Enrollment
- Students must be enrolled in the class to submit work
- Enrollment status is checked against the `enrollments` table

### Assignment Validation
- Assignment codes are auto-generated (CLASS-YYMMDD format)
- Deadlines must be in the future
- Class must exist and be active

## Admin Interface Usage

1. **View Assignments**: Navigate to "All Assignments" tab
2. **Check Status**: Use "Check Status" tab with assignment code
3. **Test Email Processing**: Use the test forms to simulate email commands

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
brew services list | grep postgresql

# Test connection
psql $DATABASE_URL -c "SELECT 1;"
```

### Migration Issues
```bash
# Check migration status
alembic current

# Reset migrations (development only)
alembic downgrade base
alembic upgrade head
```

### Test Failures
```bash
# Run with verbose output
pytest -v -s

# Check specific test
pytest tests/test_processor.py::test_email_processing -v
```

## Next Steps

This implementation completes the Week 1-2 MVP requirements:

✅ **Essential Loop**: Teachers can assign → Students can submit → Teachers can grade  
✅ **Database**: PostgreSQL with proper schema  
✅ **Validation**: Teacher whitelist and student enrollment checks  
✅ **Admin Interface**: Assignment list and status views  

### Ready for Week 3: Production Hardening
- Cloud SQL setup
- Security hardening
- Google Drive integration
- Structured logging
- Health checks

### Ready for Week 4: Automation
- Email templates
- Reminder system
- Escalation system
- SLA tracking
