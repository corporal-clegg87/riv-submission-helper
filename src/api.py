import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator, Field
from pydantic_settings import BaseSettings
from typing import List, Optional
import re
from email_validator import validate_email, EmailNotValidError
from .storage import Database
from .processor import EmailProcessor
from .models import Assignment, Submission
from .gmail_client import GmailClient
from .gmail_ingestion import GmailIngestionService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    environment: str = Field(default="development")
    cors_origins: str = Field(default="*")
    
    class Config:
        env_prefix = "APP_"

settings = Settings()

app = FastAPI(title="RIV Assignment Helper API", version="1.0.0")

# Configure CORS
origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and processor
db = Database()
processor = EmailProcessor(db)

# Initialize Gmail client and ingestion service (if credentials are available)
gmail_client = None
ingestion_service = None

try:
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and os.getenv('GMAIL_USER_EMAIL'):
        gmail_client = GmailClient()
        ingestion_service = GmailIngestionService(gmail_client, db, processor)
        logger.info("Gmail ingestion service initialized")
    else:
        logger.info("Gmail ingestion not configured (missing credentials)")
except Exception as e:
    logger.warning(f"Could not initialize Gmail client: {e}")

class EmailRequest(BaseModel):
    subject: str
    body: str
    from_email: str
    to_email: str
    message_id: str
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Subject cannot be empty')
        if len(v) > 200:
            raise ValueError('Subject must be less than 200 characters')
        return v.strip()
    
    @field_validator('body')
    @classmethod
    def validate_body(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Body cannot be empty')
        if len(v) > 5000:
            raise ValueError('Body must be less than 5000 characters')
        return v.strip()
    
    @field_validator('from_email')
    @classmethod
    def validate_from_email(cls, v):
        try:
            validation = validate_email(v, check_deliverability=False)
            return validation.normalized
        except EmailNotValidError as e:
            raise ValueError(f'Invalid from_email: {str(e)}')
    
    @field_validator('to_email')
    @classmethod
    def validate_to_email(cls, v):
        try:
            validation = validate_email(v, check_deliverability=False)
            return validation.normalized
        except EmailNotValidError as e:
            raise ValueError(f'Invalid to_email: {str(e)}')
    
    @field_validator('message_id')
    @classmethod
    def validate_message_id(cls, v):
        if not v or '@' not in v:
            raise ValueError('Invalid message_id format')
        return v.strip()

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
    """
    Process an email and return the response.
    
    This endpoint handles ASSIGN, SUBMIT, and RETURN email commands.
    All inputs are validated both client-side and server-side.
    """
    try:
        response = processor.process_email(
            email_content=request.body,
            from_email=request.from_email,
            to_emails=[request.to_email],
            subject=request.subject,
            message_id=request.message_id
        )
        return {"success": True, "response": response}
    except ValueError as e:
        # Validation errors from the processor
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors - log details but return generic message in production
        logger.error(f"Internal error processing email: {str(e)}", exc_info=True)
        
        if settings.environment == "development":
            detail = f"Internal server error: {str(e)}"
        else:
            detail = "An internal error occurred while processing your request"
        
        raise HTTPException(status_code=500, detail=detail)

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
    # Validate assignment code format
    if not re.match(r'^[A-Z0-9]+-[A-Z0-9]+$', assignment_code):
        raise HTTPException(status_code=400, detail="Invalid assignment code format. Use format like ENG7-0115")
    
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

@app.post("/api/gmail-webhook")
async def gmail_webhook(request: Request):
    """
    Webhook endpoint for Gmail Pub/Sub push notifications.
    
    This endpoint is called by Google Cloud Pub/Sub when new emails arrive.
    It processes the notification and ingests the email.
    """
    if not ingestion_service:
        raise HTTPException(
            status_code=503,
            detail="Gmail ingestion service not configured"
        )
    
    try:
        # Parse Pub/Sub message
        body = await request.json()
        
        logger.info(f"Received Gmail webhook: {body}")
        
        # Process the notification
        result = ingestion_service.handle_pubsub_notification(body)
        
        return {
            "status": "ok",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing Gmail webhook: {e}", exc_info=True)
        
        if settings.environment == "development":
            detail = f"Webhook error: {str(e)}"
        else:
            detail = "Error processing notification"
        
        raise HTTPException(status_code=500, detail=detail)

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")
