"""
Gmail API client for ingesting and sending emails.
Handles Gmail watch, fetching messages, and storing raw MIME.
"""

import base64
import logging
import os
from typing import Optional, Dict, List
from email import message_from_bytes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailClient:
    """Client for interacting with Gmail API."""
    
    def __init__(self, credentials_path: Optional[str] = None, user_email: Optional[str] = None):
        """
        Initialize Gmail client.
        
        Args:
            credentials_path: Path to service account JSON key file
            user_email: Email address to impersonate (for domain-wide delegation)
        """
        self.user_email = user_email or os.getenv('GMAIL_USER_EMAIL')
        
        # Load credentials
        creds_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not creds_path:
            raise ValueError("No credentials path provided. Set GOOGLE_APPLICATION_CREDENTIALS env var.")
        
        # Gmail API scopes
        scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.settings.basic'
        ]
        
        try:
            credentials = service_account.Credentials.from_service_account_file(
                creds_path, 
                scopes=scopes
            )
            
            # For domain-wide delegation, impersonate the user
            if self.user_email:
                credentials = credentials.with_subject(self.user_email)
            
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info(f"Gmail client initialized for user: {self.user_email}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail client: {e}")
            raise
    
    def setup_watch(self, topic_name: str, label_ids: List[str] = None) -> Dict:
        """
        Set up Gmail push notifications via Pub/Sub.
        
        Args:
            topic_name: Full Pub/Sub topic name (projects/{project}/topics/{topic})
            label_ids: Gmail labels to watch (default: INBOX)
        
        Returns:
            Watch response with historyId and expiration
        """
        try:
            request_body = {
                'topicName': topic_name,
                'labelIds': label_ids or ['INBOX']
            }
            
            response = self.service.users().watch(
                userId='me',
                body=request_body
            ).execute()
            
            logger.info(f"Gmail watch established: {response}")
            return response
            
        except HttpError as e:
            logger.error(f"Failed to setup Gmail watch: {e}")
            raise
    
    def get_message(self, message_id: str, format: str = 'full') -> Dict:
        """
        Fetch a Gmail message by ID.
        
        Args:
            message_id: Gmail message ID
            format: Response format (minimal, full, raw, metadata)
        
        Returns:
            Message data including headers, body, attachments
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format=format
            ).execute()
            
            logger.info(f"Fetched message {message_id}")
            return message
            
        except HttpError as e:
            logger.error(f"Failed to fetch message {message_id}: {e}")
            raise
    
    def get_raw_message(self, message_id: str) -> bytes:
        """
        Fetch raw MIME content of a message.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Raw MIME bytes
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='raw'
            ).execute()
            
            # Decode base64url encoded raw message
            raw_bytes = base64.urlsafe_b64decode(message['raw'])
            logger.info(f"Fetched raw MIME for message {message_id}")
            return raw_bytes
            
        except HttpError as e:
            logger.error(f"Failed to fetch raw message {message_id}: {e}")
            raise
    
    def parse_message(self, message_data: Dict) -> Dict:
        """
        Parse Gmail message data into structured format.
        
        Args:
            message_data: Gmail API message response
        
        Returns:
            Parsed message with from, to, subject, body
        """
        headers = message_data.get('payload', {}).get('headers', [])
        
        # Extract common headers
        parsed = {
            'message_id': message_data.get('id'),
            'thread_id': message_data.get('threadId'),
            'from': None,
            'to': None,
            'subject': None,
            'date': None,
            'body': None
        }
        
        for header in headers:
            name = header['name'].lower()
            value = header['value']
            
            if name == 'from':
                parsed['from'] = value
            elif name == 'to':
                parsed['to'] = value
            elif name == 'subject':
                parsed['subject'] = value
            elif name == 'date':
                parsed['date'] = value
            elif name == 'message-id':
                parsed['email_message_id'] = value
        
        # Extract body
        parsed['body'] = self._extract_body(message_data.get('payload', {}))
        
        return parsed
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract text body from message payload."""
        body = ""
        
        # Check if body is in payload directly
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        
        # Check parts for multipart messages
        elif 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    if 'data' in part.get('body', {}):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
                elif part.get('mimeType') == 'text/html' and not body:
                    if 'data' in part.get('body', {}):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        
        return body.strip()
    
    def list_history(self, start_history_id: str, max_results: int = 100) -> List[Dict]:
        """
        List message history changes since a given history ID.
        
        Args:
            start_history_id: History ID to start from
            max_results: Maximum number of results
        
        Returns:
            List of history records
        """
        try:
            response = self.service.users().history().list(
                userId='me',
                startHistoryId=start_history_id,
                maxResults=max_results,
                historyTypes=['messageAdded']
            ).execute()
            
            return response.get('history', [])
            
        except HttpError as e:
            if e.resp.status == 404:
                # History ID not found (too old), need full sync
                logger.warning(f"History ID {start_history_id} not found")
                return []
            logger.error(f"Failed to list history: {e}")
            raise
    
    def send_message(self, to: str, subject: str, body: str, from_email: Optional[str] = None) -> Dict:
        """
        Send an email message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Optional from address
        
        Returns:
            Sent message data
        """
        try:
            # Create MIME message
            from email.mime.text import MIMEText
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            response = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            logger.info(f"Sent message to {to}: {response.get('id')}")
            return response
            
        except HttpError as e:
            logger.error(f"Failed to send message: {e}")
            raise

