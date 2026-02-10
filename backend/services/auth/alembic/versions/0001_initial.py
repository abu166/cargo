"""initial auth schema

Revision ID: 0001_auth
Revises:
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_auth"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=True),
        sa.Column("station", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=128), nullable=True),
        sa.Column("company", sa.String(length=128), nullable=True),
        sa.Column("deposit_balance", sa.Float(), nullable=True),
        sa.Column("contract_number", sa.String(length=64), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("roles", sa.String(length=256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("document_id", sa.String(length=64), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("details", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("audit_log")
    op.drop_table("clients")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
