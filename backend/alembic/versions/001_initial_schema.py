"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-07

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'sources',
        sa.Column('source_id', sa.String(length=30), primary_key=True),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=30), nullable=False),
        sa.Column('base_url', sa.String(length=255), nullable=True),
        sa.Column('collection_policy', sa.String(length=255), nullable=False, server_default='ETHICAL_PUBLIC_PERMITTED'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
    )

    op.create_table(
        'carriers',
        sa.Column('carrier_id', sa.String(length=10), primary_key=True),
        sa.Column('iata_code', sa.String(length=10), nullable=True),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
    )

    op.create_table(
        'routes',
        sa.Column('route_id', sa.String(length=15), primary_key=True),
        sa.Column('origin_code', sa.String(length=10), nullable=False),
        sa.Column('destination_code', sa.String(length=10), nullable=False),
        sa.Column('directionality', sa.String(length=20), nullable=False, server_default='OUTBOUND'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index('ix_routes_origin_code', 'routes', ['origin_code'])
    op.create_index('ix_routes_destination_code', 'routes', ['destination_code'])

    op.create_table(
        'booking_horizons',
        sa.Column('horizon_days', sa.Integer(), primary_key=True),
        sa.Column('horizon_code', sa.String(length=10), nullable=False),
        sa.Column('description', sa.String(length=100), nullable=True),
    )

    op.create_table(
        'observations',
        sa.Column('observation_id', sa.String(length=36), primary_key=True),
        sa.Column('source_id', sa.String(length=30), sa.ForeignKey('sources.source_id'), nullable=False),
        sa.Column('route_id', sa.String(length=15), sa.ForeignKey('routes.route_id'), nullable=False),
        sa.Column('carrier_id', sa.String(length=10), sa.ForeignKey('carriers.carrier_id'), nullable=False),
        sa.Column('travel_date', sa.Date(), nullable=False),
        sa.Column('observed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('booking_horizon_days', sa.Integer(), sa.ForeignKey('booking_horizons.horizon_days'), nullable=False),
        sa.Column('cabin', sa.String(length=20), nullable=False, server_default='ECONOMY'),
        sa.Column('fare_class', sa.String(length=20), nullable=True, server_default='STANDARD'),
        sa.Column('trip_type', sa.String(length=20), nullable=False, server_default='ONE_WAY'),
        sa.Column('base_fare', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('taxes', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('mandatory_fees', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('total_fare', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('baggage_information', sa.JSON(), nullable=True),
        sa.Column('stop_type', sa.String(length=20), nullable=False, server_default='NON_STOP'),
        sa.Column('data_status', sa.String(length=20), nullable=False, server_default='OBSERVED'),
        sa.Column('raw_reference', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_obs_source_id', 'observations', ['source_id'])
    op.create_index('ix_obs_route_id', 'observations', ['route_id'])
    op.create_index('ix_obs_carrier_id', 'observations', ['carrier_id'])
    op.create_index('ix_obs_travel_date', 'observations', ['travel_date'])
    op.create_index('ix_obs_observed_at', 'observations', ['observed_at'])
    op.create_index('ix_obs_booking_horizon_days', 'observations', ['booking_horizon_days'])
    op.create_index('ix_obs_data_status', 'observations', ['data_status'])
    op.create_index('idx_obs_route_travel_date', 'observations', ['route_id', 'travel_date'])

    op.create_table(
        'virtual_trip_specifications',
        sa.Column('spec_id', sa.String(length=36), primary_key=True),
        sa.Column('origin', sa.String(length=10), nullable=False),
        sa.Column('destination', sa.String(length=10), nullable=False),
        sa.Column('travel_date', sa.Date(), nullable=False),
        sa.Column('passengers', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('cabin', sa.String(length=20), nullable=False, server_default='ECONOMY'),
        sa.Column('trip_type', sa.String(length=20), nullable=False, server_default='ONE_WAY'),
        sa.Column('booking_horizon', sa.Integer(), sa.ForeignKey('booking_horizons.horizon_days'), nullable=False),
        sa.Column('baggage_requirement', sa.String(length=100), nullable=False, server_default='15KG_CHECKIN_7KG_CARRYON'),
        sa.Column('eligible_stop_type', sa.String(length=20), nullable=False, server_default='NON_STOP'),
        sa.Column('fare_inclusion_rules', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'fare_components',
        sa.Column('component_id', sa.String(length=36), primary_key=True),
        sa.Column('observation_id', sa.String(length=36), sa.ForeignKey('observations.observation_id'), nullable=False),
        sa.Column('component_name', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
    )

    op.create_table(
        'normalization_results',
        sa.Column('normalization_id', sa.String(length=36), primary_key=True),
        sa.Column('observation_id', sa.String(length=36), sa.ForeignKey('observations.observation_id'), nullable=False, unique=True),
        sa.Column('base_fare', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('taxes', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('mandatory_fees', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('included_fare_components', sa.JSON(), nullable=True),
        sa.Column('normalized_total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('exclusions', sa.JSON(), nullable=True),
        sa.Column('normalization_version', sa.String(length=30), nullable=False, server_default='V1_SIMPLE_SUM'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'quality_results',
        sa.Column('quality_id', sa.String(length=36), primary_key=True),
        sa.Column('observation_id', sa.String(length=36), sa.ForeignKey('observations.observation_id'), nullable=False, unique=True),
        sa.Column('eligible', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('duplicate_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('missing_data_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('outlier_status', sa.String(length=30), nullable=False, server_default='VALID'),
        sa.Column('exclusion_reason', sa.String(length=255), nullable=True),
        sa.Column('quality_rule_version', sa.String(length=30), nullable=False, server_default='V1_BASIC_CHECKS'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('quality_results')
    op.drop_table('normalization_results')
    op.drop_table('fare_components')
    op.drop_table('virtual_trip_specifications')
    op.drop_table('observations')
    op.drop_table('booking_horizons')
    op.drop_table('routes')
    op.drop_table('carriers')
    op.drop_table('sources')
