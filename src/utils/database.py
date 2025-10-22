from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session, sessionmaker

class DatabaseSession:
    """Centralized database session management to eliminate DRY violations."""
    
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with proper cleanup."""
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def get_readonly_session(self) -> Generator[Session, None, None]:
        """Context manager for read-only database operations."""
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()
