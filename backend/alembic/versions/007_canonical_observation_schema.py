"""canonical_observation_schema

Revision ID: 007_canonical_observation_schema
Revises: 006_dgca_route_reference_schema
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa

revision = '007_canonical_observation_schema'
down_revision = '006_dgca_route_reference_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('observations') as batch_op:
        batch_op.add_column(sa.Column('source_name', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('source_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('collected_at', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('search_date', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('advance_purchase_days', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('origin_raw', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('destination_raw', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('origin_airport', sa.String(10), nullable=True))
        batch_op.add_column(sa.Column('destination_airport', sa.String(10), nullable=True))
        batch_op.add_column(sa.Column('airline', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('flight_number', sa.String(30), nullable=True))
        batch_op.add_column(sa.Column('stops', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('stops_status', sa.String(20), nullable=True, server_default='MISSING'))
        batch_op.add_column(sa.Column('duration_minutes', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('raw_total_fare', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('raw_base_fare', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('raw_taxes', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('raw_fees', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('fees', sa.Numeric(10, 2), nullable=True))
        batch_op.add_column(sa.Column('raw_payload_hash', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('observation_key', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('quote_fingerprint', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('breakdown_status', sa.String(30), nullable=True, server_default='TOTAL_ONLY'))
        batch_op.add_column(sa.Column('arithmetic_status', sa.String(30), nullable=True, server_default='ARITHMETIC_UNCHECKABLE'))
        batch_op.add_column(sa.Column('horizon_code', sa.String(20), nullable=True, server_default='OFF_HORIZON'))
        batch_op.add_column(sa.Column('route_mapping_status', sa.String(30), nullable=True, server_default='CANONICAL_MAPPED'))
        batch_op.add_column(sa.Column('basket_status', sa.String(40), nullable=True, server_default='ROUTE_OUTSIDE_REFERENCE_BASKET'))
        batch_op.add_column(sa.Column('validation_status', sa.String(20), nullable=True, server_default='ACCEPT'))
        batch_op.add_column(sa.Column('validation_reasons', sa.JSON(), nullable=True))

        batch_op.create_index('idx_obs_observation_key', ['observation_key'])
        batch_op.create_index('idx_obs_quote_fingerprint', ['quote_fingerprint'])
        batch_op.create_index('idx_obs_search_date', ['search_date'])

def downgrade() -> None:
    pass
