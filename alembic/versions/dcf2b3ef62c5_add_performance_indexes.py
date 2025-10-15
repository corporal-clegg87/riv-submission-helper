"""add_performance_indexes

Revision ID: dcf2b3ef62c5
Revises: 001
Create Date: 2025-10-15 07:48:52.988720

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcf2b3ef62c5'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add performance indexes
    op.create_index('idx_teacher_email', 'teachers', ['email'], unique=False)
    op.create_index('idx_student_id', 'students', ['student_id'], unique=False)
    op.create_index('idx_class_name', 'classes', ['name'], unique=False)
    op.create_index('idx_enrollment_lookup', 'enrollments', ['student_id', 'class_id', 'active'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove performance indexes
    op.drop_index('idx_enrollment_lookup', table_name='enrollments')
    op.drop_index('idx_class_name', table_name='classes')
    op.drop_index('idx_student_id', table_name='students')
    op.drop_index('idx_teacher_email', table_name='teachers')
