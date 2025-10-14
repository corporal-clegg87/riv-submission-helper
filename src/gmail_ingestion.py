"""
Gmail ingestion service for processing incoming emails.
Handles Pub/Sub push notifications and email processing.
"""

import base64
import json
import logging
import hashlib
from typing import Dict, Optional
from datetime import datetime
from .gmail_client import GmailClient
from .processor import EmailProcessor
from .storage import Database

logger = logging.getLogger(__name__)


class GmailIngestionService:
    """Service for ingesting emails from Gmail via Pub/Sub notifications."""
    
    def __init__(self, gmail_client: GmailClient, db: Database, processor: EmailProcessor):
        """
        Initialize ingestion service.
        
        Args:
            gmail_client: Gmail API client
            db: Database instance
            processor: Email processor
        """
        self.gmail = gmail_client
        self.db = db
        self.processor = processor
        self.processed_messages = set()  # Simple in-memory dedup (use Redis/DB in prod)
    
    def handle_pubsub_notification(self, pubsub_message: Dict) -> Dict:
        """
        Handle incoming Pub/Sub push notification from Gmail.
        
        Args:
            pubsub_message: Pub/Sub message payload
        
        Returns:
            Processing result
        """
        try:
            # Extract notification data
            message_data = pubsub_message.get('message', {})
            data = message_data.get('data', '')
            
            # Decode base64 data
            if data:
                notification_data = json.loads(base64.b64decode(data).decode('utf-8'))
            else:
                logger.warning("Empty Pub/Sub message received")
                return {'status': 'ignored', 'reason': 'empty_message'}
            
            logger.info(f"Received Gmail notification: {notification_data}")
            
            # Extract email address and history ID
            email_address = notification_data.get('emailAddress')
            history_id = notification_data.get('historyId')
            
            if not history_id:
                logger.warning("No historyId in notification")
                return {'status': 'ignored', 'reason': 'no_history_id'}
            
            # Fetch new messages from history
            return self.process_history(history_id)
            
        except Exception as e:
            logger.error(f"Error handling Pub/Sub notification: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
    
    def process_history(self, start_history_id: str) -> Dict:
        """
        Process Gmail history changes to find new messages.
        
        Args:
            start_history_id: History ID to start from
        
        Returns:
            Processing result with count of processed messages
        """
        try:
            # Fetch history
            history = self.gmail.list_history(start_history_id)
            
            processed_count = 0
            errors = []
            
            # Process each history item
            for record in history:
                messages_added = record.get('messagesAdded', [])
                
                for msg_entry in messages_added:
                    message = msg_entry.get('message', {})
                    message_id = message.get('id')
                    
                    if message_id:
                        try:
                            result = self.process_message(message_id)
                            if result['status'] == 'processed':
                                processed_count += 1
                        except Exception as e:
                            error_msg = f"Failed to process message {message_id}: {e}"
                            logger.error(error_msg)
                            errors.append(error_msg)
            
            return {
                'status': 'success',
                'processed_count': processed_count,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error processing history: {e}", exc_info=True)
            return {'status': 'error', 'error': str(e)}
    
    def process_message(self, message_id: str) -> Dict:
        """
        Fetch and process a single Gmail message.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Processing result
        """
        # Check if already processed (idempotency)
        if message_id in self.processed_messages:
            logger.info(f"Message {message_id} already processed, skipping")
            return {'status': 'duplicate', 'message_id': message_id}
        
        try:
            # Fetch message details
            message_data = self.gmail.get_message(message_id, format='full')
            parsed_message = self.gmail.parse_message(message_data)
            
            # Fetch raw MIME for audit
            raw_mime = self.gmail.get_raw_message(message_id)
            raw_checksum = hashlib.sha256(raw_mime).hexdigest()
            
            logger.info(f"Processing message {message_id}")
            logger.info(f"From: {parsed_message.get('from')}")
            logger.info(f"Subject: {parsed_message.get('subject')}")
            
            # TODO: Store raw MIME in Google Drive
            # For now, just log the checksum
            logger.info(f"Raw MIME checksum: {raw_checksum}")
            
            # Process the email through existing processor
            response = self.processor.process_email(
                email_content=parsed_message.get('body', ''),
                from_email=parsed_message.get('from', ''),
                to_emails=[parsed_message.get('to', '')],
                subject=parsed_message.get('subject', ''),
                message_id=parsed_message.get('email_message_id', message_id)
            )
            
            # Mark as processed
            self.processed_messages.add(message_id)
            
            logger.info(f"Successfully processed message {message_id}: {response}")
            
            return {
                'status': 'processed',
                'message_id': message_id,
                'response': response,
                'checksum': raw_checksum
            }
            
        except Exception as e:
            logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'message_id': message_id,
                'error': str(e)
            }

