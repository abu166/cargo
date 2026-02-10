"""initial finance schema

Revision ID: 0001_finance
Revises:
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_finance"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tariffs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("base_rate", sa.Float(), nullable=False),
        sa.Column("per_kg_rate", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("payments")
    op.drop_table("tariffs")
