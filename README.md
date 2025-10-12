# riv-submission-helper

Email-first assignment system MVP.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Process an assignment email:
   ```bash
   python main.py process --email-file sample_assign.eml
   ```

3. List assignments:
   ```bash
   python main.py list
   ```

## Email Formats

### Create Assignment
Subject: ASSIGN
Body:
Title: Essay on Climate Change
Class: English 7
Deadline: 2025-01-15 23:59 CT

### Submit Assignment
Subject: SUBMIT ENG7-0115
Body: StudentID: STU001

### Return Assignment (Grade)
Subject: RETURN ENG7-0115 STU001
Body:
Grade: A-
Feedback: Good work!

## Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Test with sample emails:
```bash
# Create an assignment
python main.py process --email-file sample_assign.eml

# Submit to the assignment
python main.py process --email-file sample_submit.eml

# Return graded assignment
python main.py process --email-file sample_return.eml

# Check assignment status
python main.py status --assignment-code ENG7-0115
```

## Next Steps
This MVP validates the email-first approach. Next iterations will add Gmail API integration, scheduling, and admin UI.
