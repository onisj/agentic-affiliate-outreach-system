"""Add sequence endpoint support

Revision ID: 0005
Revises: 0004
Create Date: 2025-06-02 06:52:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None

def upgrade():
    # No schema changes needed; endpoint uses existing table
    pass

def downgrade():
    pass