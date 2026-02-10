"""initial portal schema

Revision ID: 0001_portal
Revises:
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_portal"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("client_id", sa.String(), nullable=False),
        sa.Column("client_name", sa.String(), nullable=True),
        sa.Column("client_email", sa.String(), nullable=True),
        sa.Column("from_station", sa.String(), nullable=False),
        sa.Column("to_station", sa.String(), nullable=False),
        sa.Column("current_station", sa.String(), nullable=True),
        sa.Column("next_station", sa.String(), nullable=True),
        sa.Column("route", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("departure_date", sa.String(), nullable=True),
        sa.Column("weight", sa.String(), nullable=True),
        sa.Column("dimensions", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("shipments")
