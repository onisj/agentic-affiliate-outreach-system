"""add message_metadata to message_logs

Revision ID: add_metadata_to_message_logs
Revises: e47db7712763
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_metadata_to_message_logs'
down_revision = 'e47db7712763'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('message_logs', sa.Column('message_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, server_default='{}'))

def downgrade():
    op.drop_column('message_logs', 'message_metadata') 