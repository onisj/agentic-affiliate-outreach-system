"""Initial schema

Revision ID: ce6cb9564b24
Revises: a0022ed1f0f4
Create Date: 2025-06-02 22:05:31.530489
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect, text

# revision identifiers, used by Alembic.
revision: str = 'ce6cb9564b24'
down_revision: Union[str, None] = 'a0022ed1f0f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    # Drop message_log table
    op.drop_table('message_log')

    # Add created_at to ab_test_results if it doesn't exist
    if not any(col['name'] == 'created_at' for col in inspector.get_columns('ab_test_results')):
        op.add_column('ab_test_results', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    # Update ab_test_results columns
    op.alter_column('ab_test_results', 'sent_count',
                    existing_type=sa.INTEGER(),
                    nullable=False)
    op.alter_column('ab_test_results', 'open_rate',
                    existing_type=sa.DOUBLE_PRECISION(precision=53),
                    nullable=False)
    op.alter_column('ab_test_results', 'click_rate',
                    existing_type=sa.DOUBLE_PRECISION(precision=53),
                    nullable=False)
    op.alter_column('ab_test_results', 'reply_rate',
                    existing_type=sa.DOUBLE_PRECISION(precision=53),
                    nullable=False)
    op.alter_column('ab_test_results', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.create_foreign_key(None, 'ab_test_results', 'ab_tests', ['ab_test_id'], ['id'])

    # Add updated_at to ab_tests if it doesn't exist
    if not any(col['name'] == 'updated_at' for col in inspector.get_columns('ab_tests')):
        op.add_column('ab_tests', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    op.alter_column('ab_tests', 'variants',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=False)
    op.alter_column('ab_tests', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    if not any(idx['name'] == 'idx_ab_tests_variants' for idx in inspector.get_indexes('ab_tests')):
        op.create_index('idx_ab_tests_variants', 'ab_tests', ['variants'], unique=False, postgresql_using='gin')
    op.create_foreign_key(None, 'ab_tests', 'outreach_campaigns', ['campaign_id'], ['id'])

    op.alter_column('affiliate_prospects', 'social_profiles',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True)
    op.alter_column('affiliate_prospects', 'consent_given',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    op.alter_column('affiliate_prospects', 'consent_timestamp',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    
    # Check if prospect_status ENUM type exists
    result = bind.execute(text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prospect_status')")).scalar()
    if not result:
        op.execute("CREATE TYPE prospect_status AS ENUM ('NEW', 'QUALIFIED', 'CONTACTED', 'INTERESTED', 'DECLINED', 'ENROLLED')")
    op.execute("ALTER TABLE affiliate_prospects ALTER COLUMN status TYPE prospect_status USING status::text::prospect_status")
    op.execute("DROP TYPE IF EXISTS prospectstatus CASCADE")
    
    op.alter_column('affiliate_prospects', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.alter_column('affiliate_prospects', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    if not any(idx['name'] == 'idx_affiliate_prospects_social_profiles' for idx in inspector.get_indexes('affiliate_prospects')):
        op.create_index('idx_affiliate_prospects_social_profiles', 'affiliate_prospects', ['social_profiles'], unique=False, postgresql_using='gin')

    op.alter_column('content', 'data',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=False)
    op.alter_column('content', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.alter_column('content', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    if not any(idx['name'] == 'idx_content_data' for idx in inspector.get_indexes('content')):
        op.create_index('idx_content_data', 'content', ['data'], unique=False, postgresql_using='gin')

    op.alter_column('message_logs', 'message_type',
                    existing_type=postgresql.ENUM('EMAIL', 'LINKEDIN', 'TWITTER', name='message_type'),
                    nullable=False)
    op.alter_column('message_logs', 'status',
                    existing_type=postgresql.ENUM('SENT', 'DELIVERED', 'OPENED', 'CLICKED', 'REPLIED', 'BOUNCED', name='message_status'),
                    nullable=False)
    op.create_foreign_key(None, 'message_logs', 'affiliate_prospects', ['prospect_id'], ['id'])
    op.create_foreign_key(None, 'message_logs', 'outreach_campaigns', ['campaign_id'], ['id'])
    op.create_foreign_key(None, 'message_logs', 'message_templates', ['template_id'], ['id'])

    if not any(col['name'] == 'updated_at' for col in inspector.get_columns('message_templates')):
        op.add_column('message_templates', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    op.alter_column('message_templates', 'message_type',
                    existing_type=postgresql.ENUM('EMAIL', 'LINKEDIN', 'TWITTER', name='messagetype'),
                    type_=postgresql.ENUM('EMAIL', 'LINKEDIN', 'TWITTER', name='message_type'),
                    nullable=False)
    op.alter_column('message_templates', 'is_active',
                    existing_type=sa.BOOLEAN(),
                    nullable=False)
    op.alter_column('message_templates', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)

    op.alter_column('outreach_campaigns', 'target_criteria',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True)
    op.alter_column('outreach_campaigns', 'status',
                    existing_type=postgresql.ENUM('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='campaignstatus'),
                    type_=postgresql.ENUM('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='campaign_status'),
                    nullable=False)
    op.alter_column('outreach_campaigns', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    op.alter_column('outreach_campaigns', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    if not any(idx['name'] == 'idx_outreach_campaigns_target_criteria' for idx in inspector.get_indexes('outreach_campaigns')):
        op.create_index('idx_outreach_campaigns_target_criteria', 'outreach_campaigns', ['target_criteria'], unique=False, postgresql_using='gin')
    op.create_foreign_key(None, 'outreach_campaigns', 'message_templates', ['template_id'], ['id'])

    if not any(col['name'] == 'updated_at' for col in inspector.get_columns('sequences')):
        op.add_column('sequences', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

    op.alter_column('sequences', 'condition',
                    existing_type=postgresql.JSON(astext_type=sa.Text()),
                    type_=postgresql.JSONB(astext_type=sa.Text()),
                    existing_nullable=True)
    op.alter_column('sequences', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=True)
    if not any(idx['name'] == 'idx_sequences_condition' for idx in inspector.get_indexes('sequences')):
        op.create_index('idx_sequences_condition', 'sequences', ['condition'], unique=False, postgresql_using='gin')
    op.create_foreign_key(None, 'sequences', 'outreach_campaigns', ['campaign_id'], ['id'])
    op.create_foreign_key(None, 'sequences', 'message_templates', ['template_id'], ['id'])

def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)

    op.drop_constraint(None, 'sequences', type_='foreignkey')
    op.drop_constraint(None, 'sequences', type_='foreignkey')
    if any(idx['name'] == 'idx_sequences_condition' for idx in inspector.get_indexes('sequences')):
        op.drop_index('idx_sequences_condition', table_name='sequences', postgresql_using='gin')
    op.alter_column('sequences', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('sequences', 'condition',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=postgresql.JSON(astext_type=sa.Text()),
                    existing_nullable=True)
    if any(col['name'] == 'updated_at' for col in inspector.get_columns('sequences')):
        op.drop_column('sequences', 'updated_at')

    op.drop_constraint(None, 'outreach_campaigns', type_='foreignkey')
    if any(idx['name'] == 'idx_outreach_campaigns_target_criteria' for idx in inspector.get_indexes('outreach_campaigns')):
        op.drop_index('idx_outreach_campaigns_target_criteria', table_name='outreach_campaigns', postgresql_using='gin')
    op.alter_column('outreach_campaigns', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('outreach_campaigns', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('outreach_campaigns', 'status',
                    existing_type=postgresql.ENUM('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='campaign_status'),
                    type_=postgresql.ENUM('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='campaignstatus'),
                    nullable=True)
    op.alter_column('outreach_campaigns', 'target_criteria',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=postgresql.JSON(astext_type=sa.Text()),
                    existing_nullable=True)

    op.alter_column('message_templates', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('message_templates', 'is_active',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.alter_column('message_templates', 'message_type',
                    existing_type=postgresql.ENUM('EMAIL', 'LINKEDIN', 'TWITTER', name='message_type'),
                    type_=postgresql.ENUM('EMAIL', 'LINKEDIN', 'TWITTER', name='messagetype'),
                    nullable=True)
    if any(col['name'] == 'updated_at' for col in inspector.get_columns('message_templates')):
        op.drop_column('message_templates', 'updated_at')

    op.drop_constraint(None, 'message_logs', type_='foreignkey')
    op.drop_constraint(None, 'message_logs', type_='foreignkey')
    op.drop_constraint(None, 'message_logs', type_='foreignkey')
    op.alter_column('message_logs', 'status',
                    existing_type=postgresql.ENUM('SENT', 'DELIVERED', 'OPENED', 'CLICKED', 'REPLIED', 'BOUNCED', name='message_status'),
                    nullable=True)
    op.alter_column('message_logs', 'message_type',
                    existing_type=postgresql.ENUM('EMAIL', 'LINKEDIN', 'TWITTER', name='message_type'),
                    nullable=True)

    if any(idx['name'] == 'idx_content_data' for idx in inspector.get_indexes('content')):
        op.drop_index('idx_content_data', table_name='content', postgresql_using='gin')
    op.alter_column('content', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('content', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('content', 'data',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=postgresql.JSON(astext_type=sa.Text()),
                    existing_nullable=False)

    if any(idx['name'] == 'idx_affiliate_prospects_social_profiles' for idx in inspector.get_indexes('affiliate_prospects')):
        op.drop_index('idx_affiliate_prospects_social_profiles', table_name='affiliate_prospects', postgresql_using='gin')
    op.alter_column('affiliate_prospects', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('affiliate_prospects', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    
    op.execute("CREATE TYPE prospectstatus AS ENUM ('NEW', 'QUALIFIED', 'CONTACTED', 'INTERESTED', 'DECLINED', 'ENROLLED')")
    op.execute("ALTER TABLE affiliate_prospects ALTER COLUMN status TYPE prospectstatus USING status::text::prospectstatus")
    result = bind.execute(text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prospect_status')")).scalar()
    if result:
        op.execute("DROP TYPE prospect_status")
    
    op.alter_column('affiliate_prospects', 'consent_timestamp',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('affiliate_prospects', 'consent_given',
                    existing_type=sa.BOOLEAN(),
                    nullable=True)
    op.alter_column('affiliate_prospects', 'social_profiles',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=postgresql.JSON(astext_type=sa.Text()),
                    existing_nullable=True)

    op.drop_constraint(None, 'ab_tests', type_='foreignkey')
    if any(idx['name'] == 'idx_ab_tests_variants' for idx in inspector.get_indexes('ab_tests')):
        op.drop_index('idx_ab_tests_variants', table_name='ab_tests', postgresql_using='gin')
    op.alter_column('ab_tests', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('ab_tests', 'variants',
                    existing_type=postgresql.JSONB(astext_type=sa.Text()),
                    type_=postgresql.JSON(astext_type=sa.Text()),
                    existing_nullable=False)
    if any(col['name'] == 'updated_at' for col in inspector.get_columns('ab_tests')):
        op.drop_column('ab_tests', 'updated_at')

    op.drop_constraint(None, 'ab_test_results', type_='foreignkey')
    op.alter_column('ab_test_results', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=True)
    op.alter_column('ab_test_results', 'reply_rate',
                    existing_type=sa.DOUBLE_PRECISION(precision=53),
                    nullable=True)
    op.alter_column('ab_test_results', 'click_rate',
                    existing_type=sa.DOUBLE_PRECISION(precision=53),
                    nullable=True)
    op.alter_column('ab_test_results', 'open_rate',
                    existing_type=sa.DOUBLE_PRECISION(precision=53),
                    nullable=True)
    op.alter_column('ab_test_results', 'sent_count',
                    existing_type=sa.INTEGER(),
                    nullable=True)
    if any(col['name'] == 'created_at' for col in inspector.get_columns('ab_test_results')):
        op.drop_column('ab_test_results', 'created_at')

    op.create_table('message_log',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('prospect_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('campaign_id', sa.UUID(), autoincrement=False, nullable=True),
        sa.Column('template_id', sa.UUID(), autoincrement=False, nullable=True),
        sa.Column('message_type', postgresql.ENUM('EMAIL', 'LINKEDIN', 'TWITTER', name='messagetype'), autoincrement=False, nullable=True),
        sa.Column('subject', sa.VARCHAR(length=500), autoincrement=False, nullable=True),
        sa.Column('content', sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column('sent_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('opened_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('clicked_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('replied_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column('status', postgresql.ENUM('SENT', 'DELIVERED', 'OPENED', 'CLICKED', 'REPLIED', 'BOUNCED', name='messagestatus'), autoincrement=False, nullable=True),
        sa.Column('ab_test_variant', sa.VARCHAR(length=50), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('message_log_pkey'))
    )