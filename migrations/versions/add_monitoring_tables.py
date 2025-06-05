"""Add monitoring tables

Revision ID: add_monitoring_tables
Revises: add_metadata_to_message_logs
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_monitoring_tables'
down_revision = 'add_metadata_to_message_logs'
branch_labels = None
depends_on = None

def upgrade():
    # Create AlertType enum
    op.execute("""
        CREATE TYPE alert_type AS ENUM (
            'high_failure_rate',
            'consecutive_failures',
            'message_processing_error',
            'system_error',
            'performance_degradation',
            'rate_limit_exceeded',
            'invalid_payload',
            'authentication_error',
            'connection_error',
            'timeout_error'
        )
    """)
    
    # Create AlertSeverity enum
    op.execute("""
        CREATE TYPE alert_severity AS ENUM (
            'info',
            'warning',
            'error',
            'critical'
        )
    """)
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', postgresql.ENUM('alert_type', name='alert_type'), nullable=False),
        sa.Column('severity', postgresql.ENUM('alert_severity', name='alert_severity'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('alert_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(255), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create system_metrics table
    op.create_table(
        'system_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_labels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'idx_system_metrics_name_timestamp',
        'system_metrics',
        ['metric_name', 'timestamp']
    )
    
    # Create webhook_metrics table
    op.create_table(
        'webhook_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(255), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_labels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'idx_webhook_metrics_webhook_timestamp',
        'webhook_metrics',
        ['webhook_id', 'timestamp']
    )

def downgrade():
    # Drop webhook_metrics table
    op.drop_index('idx_webhook_metrics_webhook_timestamp', table_name='webhook_metrics')
    op.drop_table('webhook_metrics')
    
    # Drop system_metrics table
    op.drop_index('idx_system_metrics_name_timestamp', table_name='system_metrics')
    op.drop_table('system_metrics')
    
    # Drop alerts table
    op.drop_table('alerts')
    
    # Drop enums
    op.execute('DROP TYPE alert_severity')
    op.execute('DROP TYPE alert_type')

    # Drop 'alert_metadata' column from alerts table
    op.drop_column('alerts', 'alert_metadata') 