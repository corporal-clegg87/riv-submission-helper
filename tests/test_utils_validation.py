import pytest
from src.utils.validation import EmailValidator

class TestEmailValidator:
    """Test EmailValidator utility for comprehensive email validation."""
    
    def test_valid_email_formats(self):
        """Test validation of valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org",
            "123@test-domain.com",
            "a@b.co"
        ]
        
        for email in valid_emails:
            assert EmailValidator.validate_email_format(email), f"Email {email} should be valid"
            assert EmailValidator.is_valid_email(email), f"Email {email} should be valid"
    
    def test_invalid_email_formats(self):
        """Test validation of invalid email formats."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example..com",
            "",
            " ",
            "test@.com",
            "test@com."
        ]
        
        for email in invalid_emails:
            assert not EmailValidator.validate_email_format(email), f"Email {email} should be invalid"
            assert not EmailValidator.is_valid_email(email), f"Email {email} should be invalid"
    
    def test_domain_validation(self):
        """Test email domain validation against allowed list."""
        allowed_domains = ["example.com", "test.org", "domain.co.uk"]
        
        # Valid domains
        assert EmailValidator.validate_email_domain("user@example.com", allowed_domains)
        assert EmailValidator.validate_email_domain("user@TEST.ORG", allowed_domains)  # Case insensitive
        assert EmailValidator.validate_email_domain("user@domain.co.uk", allowed_domains)
        
        # Invalid domains
        assert not EmailValidator.validate_email_domain("user@invalid.com", allowed_domains)
        assert not EmailValidator.validate_email_domain("user@example.org", allowed_domains)
        
        # No domain restrictions
        assert EmailValidator.validate_email_domain("user@anydomain.com", None)
        assert EmailValidator.validate_email_domain("user@anydomain.com", [])
    
    def test_length_validation(self):
        """Test email length validation."""
        # Valid lengths
        assert EmailValidator.validate_email_length("a@b.co")  # Shortest valid
        assert EmailValidator.validate_email_length("test@example.com")
        
        # Test default max length (254)
        long_local = "a" * 60  # Shorter local part to stay under 254 total
        long_domain = "b" * 180  # Shorter domain to stay under 254 total
        long_email = f"{long_local}@{long_domain}.com"
        assert len(long_email) <= 254
        assert EmailValidator.validate_email_length(long_email)
        
        # Invalid length
        assert not EmailValidator.validate_email_length("a@b.co", max_length=5)
    
    def test_comprehensive_validation(self):
        """Test comprehensive email validation combining all checks."""
        # Valid email
        assert EmailValidator.is_valid_email("test@example.com", ["example.com"])
        
        # Invalid format
        assert not EmailValidator.is_valid_email("invalid-email", ["example.com"])
        
        # Valid format but invalid domain
        assert not EmailValidator.is_valid_email("test@invalid.com", ["example.com"])
        
        # Valid format and domain but too long
        long_email = "a" * 100 + "@" + "b" * 100 + ".com"
        assert not EmailValidator.is_valid_email(long_email, None)
        
        # Empty or whitespace
        assert not EmailValidator.is_valid_email("", ["example.com"])
        assert not EmailValidator.is_valid_email("   ", ["example.com"])
        assert not EmailValidator.is_valid_email(None, ["example.com"])
