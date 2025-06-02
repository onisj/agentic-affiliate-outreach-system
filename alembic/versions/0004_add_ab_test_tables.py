"""Add A/B test tables

Revision ID: 0004
Revises: 0003
Create Date: 2025-06-02 04:56:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('message_log', sa.Column('ab_test_variant', sa.String(length=50), nullable=True))
    
    op.create_table('ab_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('variants', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('ab_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ab_test_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variant_id', sa.String(length=50), nullable=False),
        sa.Column('sent_count', sa.Integer(), nullable=True),
        sa.Column('open_rate', sa.Float(), nullable=True),
        sa.Column('click_rate', sa.Float(), nullable=True),
        sa.Column('reply_rate', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('ab_test_results')
    op.drop_table('ab_tests')
    op.drop_column('message_log', 'ab_test_variant')