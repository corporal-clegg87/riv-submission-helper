from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from .storage import Database
from .processor import EmailProcessor
from .models import Assignment, Submission

app = FastAPI(title="RIV Assignment Helper API", version="1.0.0")

# Initialize database and processor
db = Database()
processor = EmailProcessor(db)

class EmailRequest(BaseModel):
    subject: str
    body: str
    from_email: str
    to_email: str
    message_id: str

class AssignmentResponse(BaseModel):
    id: str
    code: str
    title: str
    class_name: str
    deadline_at: str
    deadline_tz: str
    instructions: Optional[str] = None
    status: str

@app.post("/api/process-email")
async def process_email_endpoint(request: EmailRequest):
    """Process an email and return the response."""
    try:
        response = processor.process_email(
            email_content=request.body,
            from_email=request.from_email,
            to_emails=[request.to_email],
            subject=request.subject,
            message_id=request.message_id
        )
        return {"success": True, "response": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/assignments")
async def list_assignments_endpoint():
    """List all assignments."""
    assignments = db.get_all_assignments()
    return [
        AssignmentResponse(
            id=assignment.id,
            code=assignment.code,
            title=assignment.title,
            class_name=assignment.class_name,
            deadline_at=assignment.deadline_at.isoformat(),
            deadline_tz=assignment.deadline_tz,
            instructions=assignment.instructions,
            status=assignment.status
        )
        for assignment in assignments
    ]

@app.get("/api/assignments/{assignment_code}/status")
async def get_assignment_status_endpoint(assignment_code: str):
    """Get status of a specific assignment."""
    assignment = db.get_assignment_by_code(assignment_code)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    submissions = db.get_submissions_by_assignment(assignment.id)
    
    return {
        "assignment": AssignmentResponse(
            id=assignment.id,
            code=assignment.code,
            title=assignment.title,
            class_name=assignment.class_name,
            deadline_at=assignment.deadline_at.isoformat(),
            deadline_tz=assignment.deadline_tz,
            instructions=assignment.instructions,
            status=assignment.status
        ),
        "submissions": [
            {
                "student_id": sub.student_id,
                "received_at": sub.received_at.isoformat(),
                "on_time": sub.on_time,
                "status": sub.status
            }
            for sub in submissions
        ]
    }

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")
