"""initial shipments schema

Revision ID: 0001_shipments
Revises:
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_shipments"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.String(length=32), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("origin_station", sa.String(length=64), nullable=False),
        sa.Column("destination_station", sa.String(length=64), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("length_cm", sa.Float(), nullable=True),
        sa.Column("width_cm", sa.Float(), nullable=True),
        sa.Column("height_cm", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_shipments_shipment_id", "shipments", ["shipment_id"], unique=True)

    op.create_table(
        "qrcodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.Integer(), nullable=False),
        sa.Column("qr_base64", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.Integer(), nullable=False),
        sa.Column("doc_type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "scan_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shipment_id", sa.Integer(), nullable=False),
        sa.Column("scanned_by", sa.String(length=64), nullable=False),
        sa.Column("location", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("scan_events")
    op.drop_table("documents")
    op.drop_table("qrcodes")
    op.drop_index("ix_shipments_shipment_id", table_name="shipments")
    op.drop_table("shipments")
