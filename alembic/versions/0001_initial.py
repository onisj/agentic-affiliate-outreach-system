"""Initial database schema

Revision ID: 0001
Revises: 
Create Date: 2025-06-02 02:20:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('affiliate_prospects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('company', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=255), nullable=True),
        sa.Column('social_profiles', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('lead_source', sa.String(length=100), nullable=True),
        sa.Column('qualification_score', sa.Integer(), nullable=True),
        sa.Column('consent_given', sa.Boolean(), nullable=True),
        sa.Column('consent_timestamp', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'QUALIFIED', 'CONTACTED', 'INTERESTED', 'DECLINED', 'ENROLLED', name='prospectstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_affiliate_prospects_email'), 'affiliate_prospects', ['email'], unique=True)
    
    op.create_table('message_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.Enum('EMAIL', 'LINKEDIN', 'TWITTER', name='messagetype'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('outreach_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_criteria', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='campaignstatus'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('message_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prospect_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_type', sa.Enum('EMAIL', 'LINKEDIN', 'TWITTER', name='messagetype'), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=True),
        sa.Column('replied_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('SENT', 'DELIVERED', 'OPENED', 'CLICKED', 'REPLIED', 'BOUNCED', name='messagestatus'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('message_log')
    op.drop_table('outreach_campaigns')
    op.drop_table('message_templates')
    op.drop_table('affiliate_prospects')
    op.execute('DROP TYPE prospectstatus')
    op.execute('DROP TYPE campaignstatus')
    op.execute('DROP TYPE messagetype')
    op.execute('DROP TYPE messagestatus')