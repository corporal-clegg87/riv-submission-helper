# GCP Setup Guide for RIV Assignment System

## Prerequisites

### 1. Install Google Cloud CLI
```bash
# macOS (using Homebrew)
brew install --cask google-cloud-sdk

# Alternative: Direct download
# curl https://sdk.cloud.google.com | bash
# exec -l $SHELL

# Verify installation
gcloud version
```

### 2. Initialize and Authenticate
```bash
# Initialize gcloud
gcloud init

# Follow the interactive prompts:
# 1. Select or create a new project (e.g., "riv-assignments-prod")
# 2. Choose default region: us-central1
# 3. Choose default zone: us-central1-a

# Set up application default credentials
gcloud auth application-default login

# Verify authentication
gcloud auth list
gcloud config list
```

### 3. Set Environment Variables
```bash
# Set your project ID (replace with your actual project ID)
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export ZONE=us-central1-a

# Verify project is set
echo "Project ID: $PROJECT_ID"
```

## GCP Infrastructure Setup

### 1. Enable Required APIs
```bash
# Enable all required APIs
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sqladmin.googleapis.com \
    pubsub.googleapis.com \
    gmail.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudresourcemanager.googleapis.com \
    iam.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled
```

### 2. Create Cloud SQL PostgreSQL Instance
```bash
# Set database variables
export DB_INSTANCE_NAME=riv-assignments-db
export DB_NAME=riv_assignments_prod
export DB_USER=riv_admin
export DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Save password securely
echo "Database password: $DB_PASSWORD" > .db_password.txt
chmod 600 .db_password.txt

# Create Cloud SQL instance (production-ready configuration)
gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-standard-1 \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=20GB \
    --storage-auto-increase \
    --storage-auto-increase-limit=100GB \
    --backup \
    --backup-start-time=02:00 \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=02 \
    --deletion-protection \
    --labels=environment=production,app=riv-assignments

# Create database
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME

# Create application user
gcloud sql users create $DB_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DB_PASSWORD

# Get connection name for Cloud Run
export CONNECTION_NAME=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME
echo "Connection name: $CONNECTION_NAME"
```

### 3. Create Service Account and IAM
```bash
# Create service account for the application
gcloud iam service-accounts create riv-assignments-sa \
    --display-name="RIV Assignments Service Account" \
    --description="Service account for RIV Assignment Management System"

# Grant necessary IAM roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# Download service account key (for local development)
gcloud iam service-accounts keys create riv-service-account-key.json \
    --iam-account=riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com

# Set permissions for service account key file
chmod 600 riv-service-account-key.json
```

### 4. Set up Pub/Sub for Gmail Notifications
```bash
# Create Pub/Sub topic for Gmail notifications
gcloud pubsub topics create gmail-notifications \
    --labels=environment=production,app=riv-assignments

# Create subscription for the application
gcloud pubsub subscriptions create gmail-notifications-sub \
    --topic=gmail-notifications \
    --ack-deadline=600 \
    --message-retention-duration=7d \
    --labels=environment=production,app=riv-assignments

# Grant Pub/Sub permissions to service account
gcloud pubsub topics add-iam-policy-binding gmail-notifications \
    --member="serviceAccount:riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"
```

### 5. Create Cloud Run Service
```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/$PROJECT_ID/riv-assignments

# Deploy to Cloud Run with production configuration
gcloud run deploy riv-assignments \
    --image gcr.io/$PROJECT_ID/riv-assignments \
    --platform managed \
    --region $REGION \
    --service-account riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --set-env-vars="DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME,APP_ENVIRONMENT=production,GCP_PROJECT_ID=$PROJECT_ID,PUBSUB_TOPIC=gmail-notifications,PUBSUB_SUBSCRIPTION=gmail-notifications-sub" \
    --add-cloudsql-instances $CONNECTION_NAME \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10 \
    --concurrency 1000 \
    --timeout 300 \
    --port 8080 \
    --labels=environment=production,app=riv-assignments

# Get the service URL
export SERVICE_URL=$(gcloud run services describe riv-assignments --region=$REGION --format='value(status.url)')
echo "Service URL: $SERVICE_URL"
```

### 3. Set up Gmail API and Pub/Sub
```bash
# Enable required APIs
gcloud services enable gmail.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com

# Create Pub/Sub topic and subscription
gcloud pubsub topics create gmail-notifications
gcloud pubsub subscriptions create gmail-notifications-sub --topic=gmail-notifications
```

### 4. Configure Gmail API
```bash
# Create service account
gcloud iam service-accounts create riv-assignments-sa \
    --display-name="RIV Assignments Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.editor"

# Download service account key
gcloud iam service-accounts keys create riv-service-account-key.json \
    --iam-account=riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com
```

## Database Migration

### 1. Run Alembic Migrations on Cloud SQL
```bash
# Set up Cloud SQL Proxy for local migration
gcloud sql instances describe $DB_INSTANCE_NAME --format="value(connectionName)"

# Install Cloud SQL Proxy
curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64
chmod +x cloud_sql_proxy

# Start Cloud SQL Proxy in background
./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 &
PROXY_PID=$!

# Wait for proxy to start
sleep 5

# Set environment variables for local migration
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

# Run Alembic migrations
alembic upgrade head

# Stop the proxy
kill $PROXY_PID

# Verify migration
gcloud sql connect $DB_INSTANCE_NAME --user=$DB_USER --database=$DB_NAME
# In the database prompt, run:
# \dt  # List tables
# \q   # Quit
```

### 2. Create Production Seed Data Script
```bash
# Create production seed data script
cat > scripts/seed_production_data.py << 'EOF'
#!/usr/bin/env python3
"""
Production seed data for RIV Assignment System.
Creates initial terms, teachers, classes, and students.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import Database
from src.models import TermName

def create_production_data():
    db = Database()
    
    # Create current term (Spring 2024)
    current_term = db.create_term(
        id="term-2024-spring",
        name=TermName.SPRING,
        year=2024,
        start_date=datetime(2024, 1, 15),
        end_date=datetime(2024, 5, 15)
    )
    print(f"Created term: {current_term.name} {current_term.year}")
    
    # Create teachers
    teachers_data = [
        {
            "id": "teacher-001",
            "email": "john.smith@rivendell-academy.co.uk",
            "first_name": "John",
            "last_name": "Smith"
        },
        {
            "id": "teacher-002", 
            "email": "mary.johnson@rivendell-academy.co.uk",
            "first_name": "Mary",
            "last_name": "Johnson"
        }
    ]
    
    for teacher_data in teachers_data:
        teacher = db.create_teacher(**teacher_data)
        print(f"Created teacher: {teacher.first_name} {teacher.last_name}")
    
    # Create students
    students_data = [
        {"id": "student-001", "student_id": "S001", "first_name": "Alice", "last_name": "Brown"},
        {"id": "student-002", "student_id": "S002", "first_name": "Bob", "last_name": "Davis"},
        {"id": "student-003", "student_id": "S003", "first_name": "Charlie", "last_name": "Wilson"},
        {"id": "student-004", "student_id": "S004", "first_name": "Diana", "last_name": "Taylor"},
        {"id": "student-005", "student_id": "S005", "first_name": "Eve", "last_name": "Anderson"}
    ]
    
    for student_data in students_data:
        student = db.create_student(**student_data)
        print(f"Created student: {student.first_name} {student.last_name} ({student.student_id})")
    
    # Create parents
    parents_data = [
        {"id": "parent-001", "email": "brown.family@example.com", "first_name": "Robert", "last_name": "Brown"},
        {"id": "parent-002", "email": "davis.family@example.com", "first_name": "Sarah", "last_name": "Davis"},
        {"id": "parent-003", "email": "wilson.family@example.com", "first_name": "Michael", "last_name": "Wilson"},
        {"id": "parent-004", "email": "taylor.family@example.com", "first_name": "Jennifer", "last_name": "Taylor"},
        {"id": "parent-005", "email": "anderson.family@example.com", "first_name": "David", "last_name": "Anderson"}
    ]
    
    for parent_data in parents_data:
        parent = db.create_parent(**parent_data)
        print(f"Created parent: {parent.first_name} {parent.last_name}")
    
    # Create classes
    classes_data = [
        {
            "id": "class-001",
            "term_id": current_term.id,
            "name": "English 7A",
            "subject": "English",
            "teacher_id": "teacher-001"
        },
        {
            "id": "class-002", 
            "term_id": current_term.id,
            "name": "Mathematics 7A",
            "subject": "Mathematics",
            "teacher_id": "teacher-002"
        }
    ]
    
    for class_data in classes_data:
        class_obj = db.create_class(**class_data)
        print(f"Created class: {class_obj.name}")
    
    # Create enrollments
    enrollments_data = [
        # English 7A enrollments
        {"class_id": "class-001", "student_id": "student-001", "parent_id": "parent-001"},
        {"class_id": "class-001", "student_id": "student-002", "parent_id": "parent-002"},
        {"class_id": "class-001", "student_id": "student-003", "parent_id": "parent-003"},
        # Math 7A enrollments  
        {"class_id": "class-002", "student_id": "student-003", "parent_id": "parent-003"},
        {"class_id": "class-002", "student_id": "student-004", "parent_id": "parent-004"},
        {"class_id": "class-002", "student_id": "student-005", "parent_id": "parent-005"}
    ]
    
    for enrollment_data in enrollments_data:
        enrollment = db.create_enrollment(
            id=f"enrollment-{len(enrollments_data)}",
            joined_at=datetime.utcnow(),
            **enrollment_data
        )
        print(f"Created enrollment: Student {enrollment.student_id} in class {enrollment.class_id}")
    
    print("\nProduction seed data created successfully!")

if __name__ == "__main__":
    create_production_data()
EOF

# Make the script executable
chmod +x scripts/seed_production_data.py
```

### 3. Run Production Seed Data
```bash
# Set up Cloud SQL Proxy again for seeding
./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 &
PROXY_PID=$!
sleep 5

# Run the seed script
python scripts/seed_production_data.py

# Stop the proxy
kill $PROXY_PID

# Verify data was created
gcloud sql connect $DB_INSTANCE_NAME --user=$DB_USER --database=$DB_NAME
# In the database prompt, run:
# SELECT COUNT(*) FROM teachers;
# SELECT COUNT(*) FROM students;
# SELECT COUNT(*) FROM classes;
# \q
```

## Environment Configuration

### 1. Create Production Environment File
```bash
cat > .env.production << EOF
# Application Settings
APP_ENVIRONMENT=production
APP_CORS_ORIGINS=https://yourdomain.com

# Google Cloud Settings
GOOGLE_APPLICATION_CREDENTIALS=/app/riv-service-account-key.json
GCP_PROJECT_ID=$PROJECT_ID

# Pub/Sub Settings
PUBSUB_TOPIC=gmail-notifications
PUBSUB_SUBSCRIPTION=gmail-notifications-sub

# Database
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME
EOF
```

### 2. Update Dockerfile for Production
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for Cloud SQL socket
RUN mkdir -p /cloudsql

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Monitoring and Logging Setup

### 1. Configure Cloud Logging
```bash
# Create log sink for application logs
gcloud logging sinks create riv-assignments-logs \
    bigquery.googleapis.com/projects/$PROJECT_ID/datasets/riv_logs \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="riv-assignments"'

# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=riv-assignments" \
    --limit=50 --format="table(timestamp,severity,textPayload)"
```

### 2. Set up Cloud Monitoring
```bash
# Create monitoring workspace
gcloud alpha monitoring workspaces create \
    --display-name="RIV Assignments Monitoring"

# Create uptime check
gcloud alpha monitoring uptime-checks create \
    --display-name="RIV Assignments Uptime" \
    --http-check-path="/health" \
    --http-check-port="443" \
    --http-check-use-ssl \
    --selected-regions="us-central1" \
    --resource-group-type="INSTANCE_ID" \
    --resource-group-filter="resource.label.instance_id=riv-assignments"

# Create alerting policy for high error rate
cat > monitoring-policy.yaml << 'EOF'
displayName: "RIV Assignments High Error Rate"
conditions:
  - displayName: "Error rate > 5%"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="riv-assignments" AND metric.type="run.googleapis.com/request_count"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.05
      duration: 300s
alertStrategy:
  autoClose: 604800s
notificationChannels:
  - projects/$PROJECT_ID/notificationChannels/[CHANNEL_ID]
EOF

gcloud alpha monitoring policies create --policy-from-file=monitoring-policy.yaml
```

### 3. Create Monitoring Dashboard
```bash
# Create dashboard configuration
cat > dashboard-config.json << 'EOF'
{
  "displayName": "RIV Assignments Dashboard",
  "mosaicLayout": {
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Rate",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"riv-assignments\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_RATE",
                      "crossSeriesReducer": "REDUCE_SUM",
                      "groupByFields": ["resource.label.revision_name"]
                    }
                  }
                }
              }
            ]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Response Time",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"riv-assignments\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_MEAN",
                      "crossSeriesReducer": "REDUCE_MEAN"
                    }
                  }
                }
              }
            ]
          }
        }
      }
    ]
  }
}
EOF

gcloud alpha monitoring dashboards create --config-from-file=dashboard-config.json
```

## Security Considerations

### 1. Network Security
```bash
# Restrict Cloud SQL to Cloud Run only
gcloud sql instances patch $DB_INSTANCE_NAME \
    --authorized-networks=""
```

### 2. IAM Permissions
```bash
# Grant minimal required permissions
gcloud run services add-iam-policy-binding riv-assignments \
    --member="serviceAccount:riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

## Cost Optimization

### 1. Database Settings
```bash
# Use smaller instance for development
gcloud sql instances patch $DB_INSTANCE_NAME \
    --tier=db-f1-micro \
    --storage-auto-increase=false
```

### 2. Cloud Run Settings
```bash
# Set minimum instances to 0 for cost savings
gcloud run services update riv-assignments \
    --min-instances=0 \
    --max-instances=5
```

## Gmail API Integration Setup

### 1. Configure Gmail Watch
```bash
# Set up Gmail watch for email processing
# Note: This requires manual setup in Gmail API console
# 1. Go to: https://console.cloud.google.com/apis/credentials
# 2. Create OAuth 2.0 client ID for web application
# 3. Configure authorized redirect URIs
# 4. Set up Gmail watch programmatically

# Create Gmail watch configuration script
cat > setup_gmail_watch.py << 'EOF'
#!/usr/bin/env python3
"""
Setup Gmail watch for RIV Assignment System.
Run this script after initial deployment.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def setup_gmail_watch():
    """Set up Gmail watch for email notifications."""
    
    creds = None
    # Load credentials from token.json if exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    try:
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Set up watch
        watch_request = {
            'labelIds': ['INBOX'],
            'topicName': f'projects/{os.getenv("PROJECT_ID")}/topics/gmail-notifications'
        }
        
        result = service.users().watch(
            userId='me',
            body=watch_request
        ).execute()
        
        print(f"Gmail watch set up successfully!")
        print(f"History ID: {result.get('historyId')}")
        
    except HttpError as error:
        print(f"Error setting up Gmail watch: {error}")

if __name__ == '__main__':
    setup_gmail_watch()
EOF

chmod +x setup_gmail_watch.py
```

### 2. Test Gmail Integration
```bash
# Test Gmail webhook endpoint
curl -X POST "$SERVICE_URL/api/gmail-webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "data": "eyJtZXNzYWdlSWQiOiIxMjM0NTY3ODkwIn0=",
      "messageId": "test-message-123",
      "publishTime": "2024-01-15T10:00:00.000Z"
    }
  }'
```

## Final Verification

### 1. Complete System Test
```bash
# Test all endpoints
echo "Testing health endpoint..."
curl -f "$SERVICE_URL/health" || echo "Health check failed"

echo "Testing assignments endpoint..."
curl -f "$SERVICE_URL/api/assignments" || echo "Assignments endpoint failed"

echo "Testing web interface..."
curl -f "$SERVICE_URL/" || echo "Web interface failed"

# Test email processing
echo "Testing email processing..."
curl -X POST "$SERVICE_URL/api/process-email" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "ASSIGN",
    "body": "Title: Test Assignment\nClass: English 7A\nDeadline: 2024-02-20 23:59 CT",
    "from_email": "john.smith@rivendell-academy.co.uk",
    "to_email": "assignments@rivendell-academy.co.uk",
    "message_id": "test-001@example.com"
  }'
```

### 2. Performance Check
```bash
# Check Cloud Run service status
gcloud run services describe riv-assignments --region=$REGION

# Check Cloud SQL instance status
gcloud sql instances describe $DB_INSTANCE_NAME

# Check Pub/Sub subscription
gcloud pubsub subscriptions describe gmail-notifications-sub

# View recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=riv-assignments" \
  --limit=10 --format="table(timestamp,severity,textPayload)"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Cloud Run Deployment Issues
```bash
# Check build logs
gcloud builds log --stream

# Check service logs
gcloud run services logs read riv-assignments --region=$REGION --limit=50

# Restart service
gcloud run services update riv-assignments --region=$REGION
```

#### 2. Database Connection Issues
```bash
# Test database connectivity
gcloud sql connect $DB_INSTANCE_NAME --user=$DB_USER --database=$DB_NAME

# Check Cloud SQL proxy
./cloud_sql_proxy -instances=$CONNECTION_NAME=tcp:5432 &
# Test connection: psql -h localhost -U $DB_USER -d $DB_NAME
```

#### 3. Gmail API Issues
```bash
# Check Gmail API quotas
gcloud logging read "resource.type=gmail_api" --limit=10

# Verify service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:riv-assignments-sa@$PROJECT_ID.iam.gserviceaccount.com"
```

#### 4. Pub/Sub Issues
```bash
# Check Pub/Sub messages
gcloud pubsub subscriptions pull gmail-notifications-sub --limit=10

# Check topic permissions
gcloud pubsub topics get-iam-policy gmail-notifications
```

### Useful Debugging Commands
```bash
# View all logs for the service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=riv-assignments" \
  --limit=100 --format="table(timestamp,severity,textPayload)"

# Check service metrics
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"

# Test database connection from Cloud Run
gcloud run services proxy riv-assignments --port=8080 --region=$REGION

# Check environment variables
gcloud run services describe riv-assignments --region=$REGION --format="export" | grep env

# View service configuration
gcloud run services describe riv-assignments --region=$REGION --format="yaml"
```

## Cost Optimization Tips

### 1. Cloud Run Optimization
```bash
# Set minimum instances to 0 for cost savings
gcloud run services update riv-assignments \
  --min-instances=0 \
  --max-instances=5 \
  --region=$REGION

# Adjust CPU and memory allocation
gcloud run services update riv-assignments \
  --cpu=1 \
  --memory=1Gi \
  --region=$REGION
```

### 2. Cloud SQL Optimization
```bash
# Use smaller instance for development
gcloud sql instances patch $DB_INSTANCE_NAME \
  --tier=db-f1-micro

# Disable auto-increase if not needed
gcloud sql instances patch $DB_INSTANCE_NAME \
  --storage-auto-increase=false
```

### 3. Monitoring Costs
```bash
# Set up billing alerts
gcloud alpha billing budgets create \
  --billing-account=[BILLING_ACCOUNT_ID] \
  --display-name="RIV Assignments Budget" \
  --budget-amount=100 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100
```

## Next Steps

1. **Complete UAT**: Follow the UAT_PROCEDURES.md document
2. **Production Checklist**: Use PRODUCTION_CHECKLIST.md for final verification
3. **User Training**: Train teachers and admin users on the system
4. **Go-Live**: Deploy to production following the checklist
5. **Monitor**: Set up ongoing monitoring and maintenance procedures

## Support and Maintenance

### Regular Maintenance Tasks
- [ ] Weekly log review
- [ ] Monthly performance review
- [ ] Quarterly security review
- [ ] Annual disaster recovery testing

### Contact Information
- **GCP Project**: $PROJECT_ID
- **Service URL**: $SERVICE_URL
- **Cloud Console**: https://console.cloud.google.com/
- **Documentation**: See UAT_PROCEDURES.md and PRODUCTION_CHECKLIST.md

---

*This setup guide provides everything needed to deploy the RIV Assignment Management System to Google Cloud Platform. Follow all sections in order for a successful deployment.*
