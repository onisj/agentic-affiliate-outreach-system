"""Initial models

Revision ID: a0022ed1f0f4
Revises: 
Create Date: 2025-06-02 09:36:22.940921
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a0022ed1f0f4'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    
    # Create ab_test_results if not exists
    if not bind.dialect.has_table(bind, 'ab_test_results'):
        op.create_table('ab_test_results',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('ab_test_id', sa.UUID(), nullable=False),
            sa.Column('variant_id', sa.String(length=50), nullable=False),
            sa.Column('sent_count', sa.Integer(), nullable=True),
            sa.Column('open_rate', sa.Float(), nullable=True),
            sa.Column('click_rate', sa.Float(), nullable=True),
            sa.Column('reply_rate', sa.Float(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Create ab_tests if not exists
    if not bind.dialect.has_table(bind, 'ab_tests'):
        op.create_table('ab_tests',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('campaign_id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('variants', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Create affiliate_prospects if not exists
    if not bind.dialect.has_table(bind, 'affiliate_prospects'):
        op.create_table('affiliate_prospects',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('first_name', sa.String(length=100), nullable=True),
            sa.Column('last_name', sa.String(length=100), nullable=True),
            sa.Column('company', sa.String(length=255), nullable=True),
            sa.Column('website', sa.String(length=255), nullable=True),
            sa.Column('social_profiles', sa.JSON(), nullable=True),
            sa.Column('lead_source', sa.String(length=100), nullable=True),
            sa.Column('qualification_score', sa.Integer(), nullable=True),
            sa.Column('consent_given', sa.Boolean(), nullable=True),
            sa.Column('consent_timestamp', sa.DateTime(), nullable=True),
            sa.Column('status', sa.Enum('NEW', 'QUALIFIED', 'CONTACTED', 'INTERESTED', 'DECLINED', 'ENROLLED', name='prospectstatus'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_affiliate_prospects_email'), 'affiliate_prospects', ['email'], unique=True)

    # Create content if not exists
    if not bind.dialect.has_table(bind, 'content'):
        op.create_table('content',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('content_type', sa.String(length=100), nullable=False),
            sa.Column('data', sa.JSON(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Create message_log if not exists
    if not bind.dialect.has_table(bind, 'message_log'):
        op.create_table('message_log',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('prospect_id', sa.UUID(), nullable=False),
            sa.Column('campaign_id', sa.UUID(), nullable=True),
            sa.Column('template_id', sa.UUID(), nullable=True),
            sa.Column('message_type', sa.Enum('EMAIL', 'LINKEDIN', 'TWITTER', name='messagetype'), nullable=True),
            sa.Column('subject', sa.String(length=500), nullable=True),
            sa.Column('content', sa.Text(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('opened_at', sa.DateTime(), nullable=True),
            sa.Column('clicked_at', sa.DateTime(), nullable=True),
            sa.Column('replied_at', sa.DateTime(), nullable=True),
            sa.Column('status', sa.Enum('SENT', 'DELIVERED', 'OPENED', 'CLICKED', 'REPLIED', 'BOUNCED', name='messagestatus'), nullable=True),
            sa.Column('ab_test_variant', sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Create message_templates if not exists
    if not bind.dialect.has_table(bind, 'message_templates'):
        op.create_table('message_templates',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('subject', sa.String(length=500), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('message_type', sa.Enum('EMAIL', 'LINKEDIN', 'TWITTER', name='messagetype'), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Create outreach_campaigns if not exists
    if not bind.dialect.has_table(bind, 'outreach_campaigns'):
        op.create_table('outreach_campaigns',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('template_id', sa.UUID(), nullable=True),
            sa.Column('target_criteria', sa.JSON(), nullable=True),
            sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='campaignstatus'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Create sequences if not exists
    if not bind.dialect.has_table(bind, 'sequences'):
        op.create_table('sequences',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('campaign_id', sa.UUID(), nullable=False),
            sa.Column('step_number', sa.Integer(), nullable=False),
            sa.Column('template_id', sa.UUID(), nullable=False),
            sa.Column('delay_days', sa.Integer(), nullable=False),
            sa.Column('condition', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('sequences')
    op.drop_table('outreach_campaigns')
    op.drop_table('message_templates')
    op.drop_table('message_log')
    op.drop_table('content')
    op.drop_index(op.f('ix_affiliate_prospects_email'), table_name='affiliate_prospects')
    op.drop_table('affiliate_prospects')
    op.drop_table('ab_tests')
    op.drop_table('ab_test_results')