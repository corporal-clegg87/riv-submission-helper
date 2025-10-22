import pytest
from unittest.mock import Mock, patch
from src.utils.database import DatabaseSession

class TestDatabaseSession:
    """Test DatabaseSession utility for proper session management."""
    
    def test_session_context_manager(self):
        """Test that session context manager works correctly."""
        mock_session_factory = Mock()
        mock_session = Mock()
        mock_session_factory.return_value = mock_session
        
        session_manager = DatabaseSession(mock_session_factory)
        
        with session_manager.get_session() as session:
            assert session == mock_session
        
        # Verify session was created, committed, and closed
        mock_session_factory.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
    
    def test_session_rollback_on_error(self):
        """Test that session rolls back on exception."""
        mock_session_factory = Mock()
        mock_session = Mock()
        mock_session_factory.return_value = mock_session
        
        session_manager = DatabaseSession(mock_session_factory)
        
        with pytest.raises(ValueError):
            with session_manager.get_session() as session:
                raise ValueError("Test error")
        
        # Verify session was rolled back and closed
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        # Commit should not have been called
        mock_session.commit.assert_not_called()
    
    def test_readonly_session(self):
        """Test readonly session context manager."""
        mock_session_factory = Mock()
        mock_session = Mock()
        mock_session_factory.return_value = mock_session
        
        session_manager = DatabaseSession(mock_session_factory)
        
        with session_manager.get_readonly_session() as session:
            assert session == mock_session
        
        # Verify session was created and closed, but not committed
        mock_session_factory.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()
        mock_session.rollback.assert_not_called()
