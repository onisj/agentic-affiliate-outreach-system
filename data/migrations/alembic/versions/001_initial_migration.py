"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-03-19 10:00:00.000000

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
    # Create enum types
    op.execute("CREATE TYPE prospect_status AS ENUM ('new', 'qualified', 'contacted', 'interested', 'declined', 'enrolled')")
    op.execute("CREATE TYPE campaign_status AS ENUM ('draft', 'active', 'paused', 'completed', 'failed')")
    op.execute("CREATE TYPE message_status AS ENUM ('pending', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed')")
    op.execute("CREATE TYPE message_type AS ENUM ('email', 'linkedin', 'twitter', 'sms')")
    op.execute("CREATE TYPE webhook_event_type AS ENUM ('message.opened', 'message.clicked', 'message.replied', 'message.bounced', 'message.failed', 'prospect.status_changed', 'campaign.status_changed', 'prospect.engagement')")
    op.execute("CREATE TYPE alert_type AS ENUM ('high_failure_rate', 'consecutive_failures', 'message_processing_error', 'system_error', 'performance_degradation', 'rate_limit_exceeded', 'invalid_payload', 'authentication_error', 'connection_error', 'timeout_error', 'high_latency')")
    op.execute("CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'error', 'critical')")

    # Create content table
    op.create_table(
        'content',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('data', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_content_content_type', 'content', ['content_type'])

    # Create affiliate_prospects table
    op.create_table(
        'affiliate_prospects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100)),
        sa.Column('last_name', sa.String(100)),
        sa.Column('company', sa.String(255)),
        sa.Column('website', sa.String(255)),
        sa.Column('lead_source', sa.String(100)),
        sa.Column('consent_given', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('consent_timestamp', sa.DateTime(timezone=True)),
        sa.Column('qualification_score', sa.Integer, server_default='50'),
        sa.Column('status', sa.Enum('new', 'qualified', 'contacted', 'interested', 'declined', 'enrolled', name='prospect_status'), nullable=False, server_default='new'),
        sa.Column('social_profiles', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_affiliate_prospects_email', 'affiliate_prospects', ['email'], unique=True)
    op.create_index('ix_affiliate_prospects_status', 'affiliate_prospects', ['status'])
    op.create_index('ix_affiliate_prospects_qualification_score', 'affiliate_prospects', ['qualification_score'])
    op.create_index('ix_affiliate_prospects_email_status', 'affiliate_prospects', ['email', 'status'])

    # Create message_templates table
    op.create_table(
        'message_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('message_type', sa.Enum('email', 'linkedin', 'twitter', 'sms', name='message_type'), nullable=False),
        sa.Column('subject', sa.String(255)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_message_templates_message_type', 'message_templates', ['message_type'])

    # Create outreach_campaigns table
    op.create_table(
        'outreach_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('message_templates.id', ondelete='SET NULL')),
        sa.Column('target_criteria', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('status', sa.Enum('draft', 'active', 'paused', 'completed', 'failed', name='campaign_status'), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_outreach_campaigns_status', 'outreach_campaigns', ['status'])

    # Create message_logs table
    op.create_table(
        'message_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('prospect_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('affiliate_prospects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_campaigns.id', ondelete='SET NULL')),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('message_templates.id', ondelete='SET NULL')),
        sa.Column('message_type', sa.Enum('email', 'linkedin', 'twitter', 'sms', name='message_type'), nullable=False),
        sa.Column('subject', sa.String(255)),
        sa.Column('content', sa.Text),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('opened_at', sa.DateTime(timezone=True)),
        sa.Column('clicked_at', sa.DateTime(timezone=True)),
        sa.Column('replied_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'failed', name='message_status'), nullable=False, server_default='pending'),
        sa.Column('external_message_id', sa.String(255)),
        sa.Column('ab_test_variant', sa.String(50)),
        sa.Column('message_metadata', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_message_logs_status', 'message_logs', ['status'])
    op.create_index('ix_message_logs_message_type', 'message_logs', ['message_type'])
    op.create_index('ix_message_logs_sent_at', 'message_logs', ['sent_at'])
    op.create_index('ix_message_logs_prospect_campaign', 'message_logs', ['prospect_id', 'campaign_id'])

    # Create sequences table
    op.create_table(
        'sequences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('step_number', sa.Integer, nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('message_templates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('delay_days', sa.Integer, nullable=False, server_default='0'),
        sa.Column('condition', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_sequences_campaign_id_step', 'sequences', ['campaign_id', 'step_number'], unique=True)

    # Create ab_tests table
    op.create_table(
        'ab_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outreach_campaigns.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('variants', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index('ix_ab_tests_campaign_id', 'ab_tests', ['campaign_id'])

    # Create ab_test_results table
    op.create_table(
        'ab_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('ab_test_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ab_tests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sent_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('open_rate', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('click_rate', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('reply_rate', sa.Float, nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('url', sa.String(512), nullable=False),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('events', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('description', sa.String(255)),
        sa.Column('failure_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True)),
        sa.Column('validate_payloads', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('payload_schema', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.Enum('message.opened', 'message.clicked', 'message.replied', 'message.bounced', 'message.failed', 'prospect.status_changed', 'campaign.status_changed', 'prospect.engagement', name='webhook_event_type'), nullable=False),
        sa.Column('payload', postgresql.JSONB, nullable=False),
        sa.Column('response_code', sa.Integer),
        sa.Column('response_body', sa.Text),
        sa.Column('success', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('alert_type', sa.Enum('high_failure_rate', 'consecutive_failures', 'message_processing_error', 'system_error', 'performance_degradation', 'rate_limit_exceeded', 'invalid_payload', 'authentication_error', 'connection_error', 'timeout_error', 'high_latency', name='alert_type'), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'error', 'critical', name='alert_severity'), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('alert_metadata', sa.JSON),
        sa.Column('is_resolved', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', sa.String(255)),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('metric_labels', sa.JSON),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # Create webhook_metrics table
    op.create_table(
        'webhook_metrics',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('webhooks.id'), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('metric_labels', sa.JSON),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('webhook_metrics')
    op.drop_table('system_metrics')
    op.drop_table('alerts')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
    op.drop_table('ab_test_results')
    op.drop_table('ab_tests')
    op.drop_table('sequences')
    op.drop_table('message_logs')
    op.drop_table('outreach_campaigns')
    op.drop_table('message_templates')
    op.drop_table('affiliate_prospects')
    op.drop_table('content')

    # Drop enum types
    op.execute('DROP TYPE alert_severity')
    op.execute('DROP TYPE alert_type')
    op.execute('DROP TYPE webhook_event_type')
    op.execute('DROP TYPE message_type')
    op.execute('DROP TYPE message_status')
    op.execute('DROP TYPE campaign_status')
    op.execute('DROP TYPE prospect_status')
