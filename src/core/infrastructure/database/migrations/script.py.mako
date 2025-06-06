"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | None}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = '${revision}'
down_revision = '${down_revision | None}'
branch_labels = ${branch_labels}
depends_on = ${depends_on}

def upgrade():
    ${upgrades if upgrades else "pass"}

def downgrade():
    ${downgrades if downgrades else "pass"}