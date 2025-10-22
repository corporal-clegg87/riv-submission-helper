import re
from typing import Optional
from email_validator import validate_email, EmailNotValidError

class EmailValidator:
    """Centralized email validation to eliminate DRY violations."""
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate email format using email-validator library."""
        try:
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def validate_email_domain(email: str, allowed_domains: Optional[list] = None) -> bool:
        """Validate email domain against allowed list."""
        if not allowed_domains:
            return True
        
        domain = email.split('@')[-1].lower()
        return domain in [d.lower() for d in allowed_domains]
    
    @staticmethod
    def validate_email_length(email: str, max_length: int = 254) -> bool:
        """Validate email length according to RFC standards."""
        return len(email) <= max_length
    
    @staticmethod
    def is_valid_email(email: str, allowed_domains: Optional[list] = None) -> bool:
        """Comprehensive email validation combining format, domain, and length checks."""
        if not email or not email.strip():
            return False
        
        email = email.strip()
        return (
            EmailValidator.validate_email_format(email) and
            EmailValidator.validate_email_domain(email, allowed_domains) and
            EmailValidator.validate_email_length(email)
        )
