#!/bin/bash

# Setup script for deploying RIV Assignment Helper to Google Cloud Platform
# This script automates the GCP configuration and deployment

set -e  # Exit on error

echo "🚀 RIV Assignment Helper - GCP Setup"
echo "======================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed."
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✅ gcloud CLI found"

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ No GCP project configured."
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Using GCP Project: $PROJECT_ID"
echo ""

# Prompt for required information
read -p "Enter your assignments email address (e.g., assignments@yourdomain.com): " GMAIL_USER_EMAIL

if [ -z "$GMAIL_USER_EMAIL" ]; then
    echo "❌ Email address is required"
    exit 1
fi

echo ""
echo "Step 1: Enabling required APIs..."
echo "-----------------------------------"

gcloud services enable gmail.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable drive.googleapis.com
gcloud services enable sheets.googleapis.com

echo "✅ APIs enabled"
echo ""

echo "Step 2: Creating service account..."
echo "------------------------------------"

SERVICE_ACCOUNT_NAME="riv-assignment-helper"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Check if service account already exists
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL &>/dev/null; then
    echo "⚠️  Service account already exists: $SERVICE_ACCOUNT_EMAIL"
else
    gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
        --display-name="RIV Assignment Helper Service Account" \
        --description="Service account for email assignment system"
    
    echo "✅ Service account created: $SERVICE_ACCOUNT_EMAIL"
fi

echo ""
echo "Step 3: Granting IAM roles..."
echo "------------------------------"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/pubsub.editor" \
    --condition=None

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/logging.logWriter" \
    --condition=None

echo "✅ IAM roles granted"
echo ""

echo "Step 4: Downloading service account key..."
echo "-------------------------------------------"

KEY_FILE="service-account-key.json"

if [ -f "$KEY_FILE" ]; then
    read -p "⚠️  $KEY_FILE already exists. Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping key download"
        KEY_FILE_EXISTS=true
    fi
fi

if [ -z "$KEY_FILE_EXISTS" ]; then
    gcloud iam service-accounts keys create ${KEY_FILE} \
        --iam-account=${SERVICE_ACCOUNT_EMAIL}
    
    echo "✅ Service account key saved to: $KEY_FILE"
    echo "⚠️  IMPORTANT: Keep this file secure and never commit it to git!"
fi

echo ""
echo "Step 5: Creating Pub/Sub topic..."
echo "----------------------------------"

TOPIC_NAME="gmail-notifications"

if gcloud pubsub topics describe ${TOPIC_NAME} &>/dev/null; then
    echo "⚠️  Pub/Sub topic already exists: $TOPIC_NAME"
else
    gcloud pubsub topics create ${TOPIC_NAME}
    echo "✅ Pub/Sub topic created: $TOPIC_NAME"
fi

# Grant Gmail permission to publish to the topic
GMAIL_SERVICE_ACCOUNT="serviceAccount:gmail-api-push@system.gserviceaccount.com"

gcloud pubsub topics add-iam-policy-binding ${TOPIC_NAME} \
    --member=${GMAIL_SERVICE_ACCOUNT} \
    --role=roles/pubsub.publisher

echo "✅ Gmail granted publish permissions"
echo ""

echo "Step 6: Building and deploying to Cloud Run..."
echo "-----------------------------------------------"

SERVICE_NAME="riv-assignment-helper"
REGION="us-central1"

echo "Building container..."

gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}

echo ""
echo "Deploying to Cloud Run..."

gcloud run deploy ${SERVICE_NAME} \
    --image gcr.io/${PROJECT_ID}/${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --set-env-vars "APP_ENVIRONMENT=production,GMAIL_USER_EMAIL=${GMAIL_USER_EMAIL},GCP_PROJECT_ID=${PROJECT_ID}" \
    --service-account ${SERVICE_ACCOUNT_EMAIL}

# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format='value(status.url)')

echo "✅ Deployed to Cloud Run: $SERVICE_URL"
echo ""

echo "Step 7: Creating Pub/Sub push subscription..."
echo "----------------------------------------------"

SUBSCRIPTION_NAME="gmail-notifications-sub"
WEBHOOK_URL="${SERVICE_URL}/api/gmail-webhook"

if gcloud pubsub subscriptions describe ${SUBSCRIPTION_NAME} &>/dev/null; then
    echo "⚠️  Subscription already exists, updating..."
    gcloud pubsub subscriptions delete ${SUBSCRIPTION_NAME} --quiet
fi

gcloud pubsub subscriptions create ${SUBSCRIPTION_NAME} \
    --topic=${TOPIC_NAME} \
    --push-endpoint=${WEBHOOK_URL} \
    --ack-deadline=60

echo "✅ Push subscription created: $SUBSCRIPTION_NAME"
echo "   Webhook URL: $WEBHOOK_URL"
echo ""

echo "=========================================="
echo "✅ GCP Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Set up Gmail API access:"
echo "   - Go to https://console.cloud.google.com/iam-admin/serviceaccounts"
echo "   - Click on: $SERVICE_ACCOUNT_EMAIL"
echo "   - Enable 'Google Workspace Domain-wide Delegation'"
echo "   - Note the Client ID"
echo ""
echo "2. Configure Domain-Wide Delegation:"
echo "   - Go to https://admin.google.com/ac/owl/domainwidedelegation"
echo "   - Add the Client ID with these scopes:"
echo "     https://www.googleapis.com/auth/gmail.readonly"
echo "     https://www.googleapis.com/auth/gmail.send"
echo "     https://www.googleapis.com/auth/gmail.settings.basic"
echo ""
echo "3. Set up Gmail watch (run this Python script):"
echo "   python -c \""
echo "   from src.gmail_client import GmailClient"
echo "   gmail = GmailClient()"
echo "   topic = 'projects/${PROJECT_ID}/topics/${TOPIC_NAME}'"
echo "   result = gmail.setup_watch(topic)"
echo "   print('Watch established:', result)"
echo "   \""
echo ""
echo "4. Test the system:"
echo "   Send an email to: $GMAIL_USER_EMAIL"
echo "   with subject: ASSIGN"
echo "   and body with Title, Class, and Deadline fields"
echo ""
echo "Service URL: $SERVICE_URL"
echo "Logs: gcloud run logs read ${SERVICE_NAME} --region ${REGION}"
echo ""

