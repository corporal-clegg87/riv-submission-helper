import pytest
from src.exceptions import (
    AssignmentError, ValidationError, DatabaseError, AuthorizationError, NotFoundError, ErrorCodes
)


class TestExceptionHierarchy:
    """Test the exception hierarchy and error codes."""
    
    def test_assignment_error_base(self):
        """Test AssignmentError base exception."""
        error = AssignmentError("Test error")
        assert str(error) == "Test error"
        assert error.error_code == "ASSIGNMENT_ERROR"
        assert error.message == "Test error"
    
    def test_assignment_error_with_code(self):
        """Test AssignmentError with custom error code."""
        error = AssignmentError("Test error", "CUSTOM_ERROR")
        assert str(error) == "Test error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.message == "Test error"
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert isinstance(error, AssignmentError)
    
    def test_validation_error_with_code(self):
        """Test ValidationError with custom error code."""
        error = ValidationError("Missing field", ErrorCodes.MISSING_REQUIRED_FIELD)
        assert str(error) == "Missing field"
        assert error.error_code == ErrorCodes.MISSING_REQUIRED_FIELD
        assert isinstance(error, AssignmentError)
    
    def test_database_error(self):
        """Test DatabaseError exception."""
        error = DatabaseError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.error_code == "DATABASE_ERROR"
        assert isinstance(error, AssignmentError)
    
    def test_authorization_error(self):
        """Test AuthorizationError exception."""
        error = AuthorizationError("Not authorized")
        assert str(error) == "Not authorized"
        assert error.error_code == "AUTHORIZATION_ERROR"
        assert isinstance(error, AssignmentError)
    
    def test_not_found_error(self):
        """Test NotFoundError exception."""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"
        assert error.error_code == "NOT_FOUND_ERROR"
        assert isinstance(error, AssignmentError)
    
    def test_error_codes_constants(self):
        """Test that ErrorCodes constants are defined."""
        # Validation errors
        assert ErrorCodes.INVALID_EMAIL_FORMAT == "INVALID_EMAIL_FORMAT"
        assert ErrorCodes.MISSING_REQUIRED_FIELD == "MISSING_REQUIRED_FIELD"
        assert ErrorCodes.INVALID_DEADLINE_FORMAT == "INVALID_DEADLINE_FORMAT"
        assert ErrorCodes.INVALID_SUBJECT_FORMAT == "INVALID_SUBJECT_FORMAT"
        assert ErrorCodes.MISSING_STUDENT_ID == "MISSING_STUDENT_ID"
        assert ErrorCodes.MISSING_GRADE_VALUE == "MISSING_GRADE_VALUE"
        
        # Authorization errors
        assert ErrorCodes.TEACHER_NOT_WHITELISTED == "TEACHER_NOT_WHITELISTED"
        assert ErrorCodes.UNAUTHORIZED_OPERATION == "UNAUTHORIZED_OPERATION"
        
        # Not found errors
        assert ErrorCodes.ASSIGNMENT_NOT_FOUND == "ASSIGNMENT_NOT_FOUND"
        assert ErrorCodes.STUDENT_NOT_FOUND == "STUDENT_NOT_FOUND"
        assert ErrorCodes.TEACHER_NOT_FOUND == "TEACHER_NOT_FOUND"
        assert ErrorCodes.CLASS_NOT_FOUND == "CLASS_NOT_FOUND"
        assert ErrorCodes.SUBMISSION_NOT_FOUND == "SUBMISSION_NOT_FOUND"
        
        # Database errors
        assert ErrorCodes.CONNECTION_FAILED == "CONNECTION_FAILED"
        assert ErrorCodes.QUERY_FAILED == "QUERY_FAILED"
        assert ErrorCodes.SAVE_FAILED == "SAVE_FAILED"
        
        # Business logic errors
        assert ErrorCodes.DUPLICATE_SUBMISSION == "DUPLICATE_SUBMISSION"
        assert ErrorCodes.STUDENT_NOT_ENROLLED == "STUDENT_NOT_ENROLLED"
        assert ErrorCodes.INVALID_ASSIGNMENT_CODE == "INVALID_ASSIGNMENT_CODE"
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from AssignmentError."""
        validation_error = ValidationError("test")
        database_error = DatabaseError("test")
        authorization_error = AuthorizationError("test")
        not_found_error = NotFoundError("test")
        
        assert isinstance(validation_error, AssignmentError)
        assert isinstance(database_error, AssignmentError)
        assert isinstance(authorization_error, AssignmentError)
        assert isinstance(not_found_error, AssignmentError)
    
    def test_exception_chaining(self):
        """Test exception chaining with from clause."""
        original_error = ValueError("Original error")
        try:
            raise ValidationError("Wrapped error") from original_error
        except ValidationError as wrapped_error:
            assert str(wrapped_error) == "Wrapped error"
            assert wrapped_error.__cause__ is original_error
