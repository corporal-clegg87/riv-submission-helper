"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create terms table
    op.create_table('terms',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create teachers table
    op.create_table('teachers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='ACTIVE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create students table
    op.create_table('students',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='ACTIVE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id')
    )
    
    # Create parents table
    op.create_table('parents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='ACTIVE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create classes table
    op.create_table('classes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('term_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('teacher_id', sa.String(), nullable=False),
        sa.Column('roster_version', sa.Integer(), nullable=False, default=1),
        sa.Column('status', sa.String(), nullable=False, default='ACTIVE'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['term_id'], ['terms.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'])
    )
    
    # Create enrollments table
    op.create_table('enrollments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('class_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('parent_id', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id'])
    )
    
    # Create assignments table
    op.create_table('assignments',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('class_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('deadline_at', sa.DateTime(), nullable=False),
        sa.Column('deadline_tz', sa.String(), nullable=False, default='CT'),
        sa.Column('created_by_teacher_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='SCHEDULED'),
        sa.Column('grace_days', sa.Integer(), nullable=False, default=7),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id']),
        sa.ForeignKeyConstraint(['created_by_teacher_id'], ['teachers.id'])
    )
    
    # Create submissions table
    op.create_table('submissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assignment_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('on_time', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='RECEIVED'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'])
    )
    
    # Create grades table
    op.create_table('grades',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('assignment_id', sa.String(), nullable=False),
        sa.Column('student_id', sa.String(), nullable=False),
        sa.Column('grade_value', sa.String(), nullable=False),
        sa.Column('feedback_text', sa.Text(), nullable=True),
        sa.Column('graded_by_teacher_id', sa.String(), nullable=False),
        sa.Column('graded_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['assignment_id'], ['assignments.id']),
        sa.ForeignKeyConstraint(['student_id'], ['students.id']),
        sa.ForeignKeyConstraint(['graded_by_teacher_id'], ['teachers.id'])
    )
    
    # Create email_messages table
    op.create_table('email_messages',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('from_email', sa.String(), nullable=False),
        sa.Column('to_emails', sa.Text(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('message_id', sa.String(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.Column('parse_result', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )


def downgrade() -> None:
    op.drop_table('email_messages')
    op.drop_table('grades')
    op.drop_table('submissions')
    op.drop_table('assignments')
    op.drop_table('enrollments')
    op.drop_table('classes')
    op.drop_table('parents')
    op.drop_table('students')
    op.drop_table('teachers')
    op.drop_table('terms')
