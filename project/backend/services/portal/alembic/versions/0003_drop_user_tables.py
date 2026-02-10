"""drop portal user tables

Revision ID: 0003_drop_portal_users
Revises: 0002_portal_defaults
Create Date: 2026-02-10
"""

from alembic import op


revision = "0003_drop_portal_users"
down_revision = "0002_portal_defaults"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TABLE IF EXISTS employees")
    op.execute("DROP TABLE IF EXISTS users")


def downgrade():
    # No-op: users/employees were removed from portal DB
    pass
