class AssignmentError(Exception):
    """Base exception for all assignment-related errors."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code or "ASSIGNMENT_ERROR"
        self.message = message

class ValidationError(AssignmentError):
    """Raised when input validation fails."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "VALIDATION_ERROR")

class DatabaseError(AssignmentError):
    """Raised when database operations fail."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "DATABASE_ERROR")

class AuthorizationError(AssignmentError):
    """Raised when user is not authorized for an operation."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "AUTHORIZATION_ERROR")

class NotFoundError(AssignmentError):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "NOT_FOUND_ERROR")

# Specific error codes for common scenarios
class ErrorCodes:
    # Validation errors
    INVALID_EMAIL_FORMAT = "INVALID_EMAIL_FORMAT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_DEADLINE_FORMAT = "INVALID_DEADLINE_FORMAT"
    INVALID_SUBJECT_FORMAT = "INVALID_SUBJECT_FORMAT"
    MISSING_STUDENT_ID = "MISSING_STUDENT_ID"
    MISSING_GRADE_VALUE = "MISSING_GRADE_VALUE"
    
    # Authorization errors
    TEACHER_NOT_WHITELISTED = "TEACHER_NOT_WHITELISTED"
    UNAUTHORIZED_OPERATION = "UNAUTHORIZED_OPERATION"
    
    # Not found errors
    ASSIGNMENT_NOT_FOUND = "ASSIGNMENT_NOT_FOUND"
    STUDENT_NOT_FOUND = "STUDENT_NOT_FOUND"
    TEACHER_NOT_FOUND = "TEACHER_NOT_FOUND"
    CLASS_NOT_FOUND = "CLASS_NOT_FOUND"
    SUBMISSION_NOT_FOUND = "SUBMISSION_NOT_FOUND"
    
    # Database errors
    CONNECTION_FAILED = "CONNECTION_FAILED"
    QUERY_FAILED = "QUERY_FAILED"
    SAVE_FAILED = "SAVE_FAILED"
    
    # Business logic errors
    DUPLICATE_SUBMISSION = "DUPLICATE_SUBMISSION"
    STUDENT_NOT_ENROLLED = "STUDENT_NOT_ENROLLED"
    INVALID_ASSIGNMENT_CODE = "INVALID_ASSIGNMENT_CODE"
