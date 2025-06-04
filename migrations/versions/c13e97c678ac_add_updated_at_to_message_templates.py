from alembic import op
import sqlalchemy as sa

revision = 'c13e97c678ac'
down_revision = '0e9ca861c07f'
branch_labels = None
depends_on = None

def upgrade():
    # Drop GIN index if it exists
    op.drop_index('ix_affiliate_prospects_social_profiles', table_name='affiliate_prospects', postgresql_using='gin', if_exists=True)
    
    # Add updated_at to message_templates if not exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='message_templates' AND column_name='updated_at'
        """)
    ).fetchone()
    
    if result is None:
        op.add_column(
            'message_templates',
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
        )

def downgrade():
    # Remove updated_at from message_templates
    op.drop_column('message_templates', 'updated_at')
    
    # Recreate GIN index
    op.create_index('ix_affiliate_prospects_social_profiles', 'affiliate_prospects', ['social_profiles'], postgresql_using='gin')



# # migrations/versions/c13e97c678ac_add_updated_at_to_message_templates.py
# """Add updated_at to message_templates

# Revision ID: c13e97c678ac
# Revises: 0e9ca861c07f
# Create Date: 2025-06-03

# """
# from alembic import op
# import sqlalchemy as sa

# revision = 'c13e97c678ac'
# down_revision = '0e9ca861c07f'
# branch_labels = None
# depends_on = None

# def upgrade():
#     # Drop GIN index on social_profiles if exists
#     op.drop_index('ix_affiliate_prospects_social_profiles', table_name='affiliate_prospects', postgresql_using='gin', if_exists=True)
    
#     # Add updated_at to message_templates if not exists
#     op.add_column(
#         'message_templates',
#         sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
#     )

# def downgrade():
#     # Remove updated_at from message_templates
#     op.drop_column('message_templates', 'updated_at')