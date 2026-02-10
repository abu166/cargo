"""add defaults for timestamps

Revision ID: 0002_portal_defaults
Revises: 0001_portal
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_portal_defaults"
down_revision = "0001_portal"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("users", "created_at", server_default=sa.text("now()"))
    op.alter_column("employees", "created_at", server_default=sa.text("now()"))
    op.alter_column("shipments", "created_at", server_default=sa.text("now()"))
    op.alter_column("shipments", "updated_at", server_default=sa.text("now()"))


def downgrade():
    op.alter_column("shipments", "updated_at", server_default=None)
    op.alter_column("shipments", "created_at", server_default=None)
    op.alter_column("employees", "created_at", server_default=None)
    op.alter_column("users", "created_at", server_default=None)
