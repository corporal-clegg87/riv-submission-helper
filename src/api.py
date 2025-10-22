import os
import logging
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
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

# Secret Manager imports
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    environment: str = Field(default="development")
    cors_origins: str = Field(default="*")
    basic_auth_user: str = Field(default="admin")
    basic_auth_pass: str = Field(default="admin")
    secret_username_name: str = Field(default="riv-basic-auth-user")
    secret_password_name: str = Field(default="riv-basic-auth-pass")
    
    class Config:
        env_prefix = "APP_"

settings = Settings()

# Secret Manager client - initialized lazily to prevent import failures
secret_client = None

# Credential caching
_credential_cache = {}
_credential_cache_ttl = 300  # 5 minutes

def get_secret_client():
    """Get Secret Manager client, initializing it if needed."""
    global secret_client
    if secret_client is None and SECRET_MANAGER_AVAILABLE:
        try:
            secret_client = secretmanager.SecretManagerServiceClient()
        except Exception as e:
            logger.warning(f"Failed to initialize Secret Manager client: {e}")
    return secret_client

def get_secret_manager_credentials():
    """Get credentials from Secret Manager or environment variables with caching."""
    # Check cache first
    current_time = time.time()
    if 'credentials' in _credential_cache:
        cached_time, cached_creds = _credential_cache['credentials']
        if current_time - cached_time < _credential_cache_ttl:
            logger.debug("Using cached credentials")
            return cached_creds
    
    # Check if we're in production (Cloud Run) with Secret Manager available
    client = get_secret_client()
    if client and os.getenv('GCP_PROJECT_ID'):
        try:
            project_id = os.getenv('GCP_PROJECT_ID')
            
            # Get username from Secret Manager
            username_secret_name = f"projects/{project_id}/secrets/{settings.secret_username_name}/versions/latest"
            username_response = client.access_secret_version(request={"name": username_secret_name})
            username = username_response.payload.data.decode("UTF-8")
            
            # Get password from Secret Manager
            password_secret_name = f"projects/{project_id}/secrets/{settings.secret_password_name}/versions/latest"
            password_response = client.access_secret_version(request={"name": password_secret_name})
            password = password_response.payload.data.decode("UTF-8")
            
            # Cache the credentials
            credentials = (username, password)
            _credential_cache['credentials'] = (current_time, credentials)
            
            logger.debug("Using Secret Manager credentials")
            return credentials
            
        except Exception as e:
            logger.warning(f"Failed to get credentials from Secret Manager: {e}")
            # Fallback to environment variables
            pass
    
    # Use environment variables (for local development or fallback)
    credentials = (settings.basic_auth_user, settings.basic_auth_pass)
    _credential_cache['credentials'] = (current_time, credentials)
    
    logger.debug("Using environment variable credentials")
    return credentials

# Basic authentication
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic authentication credentials."""
    # Get credentials from Secret Manager or environment
    correct_username, correct_password = get_secret_manager_credentials()
    
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

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
async def process_email_endpoint(request: EmailRequest, current_user: str = Depends(get_current_user)):
    """
    Process an email and return the response.
    
    This endpoint requires authentication and handles ASSIGN, SUBMIT, and RETURN email commands.
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
async def list_assignments_endpoint(current_user: str = Depends(get_current_user)):
    """List all assignments. Requires authentication."""
    assignments_with_classes = db.get_all_assignments_with_classes()
    result = []
    for assignment, class_name in assignments_with_classes:
        result.append(AssignmentResponse(
            id=assignment.id,
            code=assignment.code,
            title=assignment.title,
            class_name=class_name or "Unknown Class",
            deadline_at=assignment.deadline_at.isoformat(),
            deadline_tz=assignment.deadline_tz,
            instructions=assignment.instructions,
            status=assignment.status
        ))
    return result

@app.get("/api/assignments/{assignment_code}/status")
async def get_assignment_status_endpoint(assignment_code: str, current_user: str = Depends(get_current_user)):
    """Get status of a specific assignment. Requires authentication."""
    # Validate assignment code format
    if not re.match(r'^[A-Z0-9]+-[A-Z0-9]+$', assignment_code):
        raise HTTPException(status_code=400, detail="Invalid assignment code format. Use format like ENG7-0115")
    
    result = db.get_assignment_with_class_by_code(assignment_code)
    if not result:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    assignment, class_name = result
    submissions = db.get_submissions_by_assignment(assignment.id)
    
    return {
        "assignment": AssignmentResponse(
            id=assignment.id,
            code=assignment.code,
            title=assignment.title,
            class_name=class_name or "Unknown Class",
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

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run (public for monitoring)."""
    try:
        # Test database connection
        db.test_connection()
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/")
async def serve_index(current_user: str = Depends(get_current_user)):
    """Serve the main web interface. Requires authentication."""
    return FileResponse("static/index.html")
