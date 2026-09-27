"""015_longitudinal_panel

Revision ID: 499a337e91e2
Revises: '014_multisource_orchestration'
Create Date: 2026-09-27 20:48:32.866468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '499a337e91e2'
down_revision = '014_multisource_orchestration'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('airline_registry',
    sa.Column('airline_id', sa.String(length=20), nullable=False),
    sa.Column('iata_code', sa.String(length=5), nullable=False),
    sa.Column('icao_code', sa.String(length=5), nullable=True),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('domestic_scheduled', sa.Boolean(), nullable=False),
    sa.Column('direct_booking_url', sa.String(length=255), nullable=True),
    sa.Column('official_api_available', sa.Boolean(), nullable=False),
    sa.Column('ndc_available', sa.Boolean(), nullable=False),
    sa.Column('ndc_portal_url', sa.String(length=255), nullable=True),
    sa.Column('api_access_type', sa.String(length=50), nullable=False),
    sa.Column('requires_authentication', sa.Boolean(), nullable=False),
    sa.Column('partner_restriction', sa.Boolean(), nullable=False),
    sa.Column('fare_data_available', sa.Boolean(), nullable=False),
    sa.Column('seat_availability_available', sa.Boolean(), nullable=False),
    sa.Column('ancillary_data_available', sa.Boolean(), nullable=False),
    sa.Column('is_documented', sa.Boolean(), nullable=False),
    sa.Column('is_accessible', sa.Boolean(), nullable=False),
    sa.Column('is_actually_collected', sa.Boolean(), nullable=False),
    sa.Column('is_currently_observed', sa.Boolean(), nullable=False),
    sa.Column('last_verified_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('verification_source', sa.String(length=255), nullable=False),
    sa.Column('verification_status', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('airline_id')
    )
    op.create_index(op.f('ix_airline_registry_airline_id'), 'airline_registry', ['airline_id'], unique=False)
    op.create_index(op.f('ix_airline_registry_iata_code'), 'airline_registry', ['iata_code'], unique=True)
    
    op.create_table('longitudinal_panel_manifest',
    sa.Column('manifest_id', sa.String(length=50), nullable=False),
    sa.Column('route_id', sa.String(length=20), nullable=False),
    sa.Column('travel_date', sa.Date(), nullable=False),
    sa.Column('first_observed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_observed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('search_count', sa.Integer(), nullable=False),
    sa.Column('search_dates', sa.JSON(), nullable=False),
    sa.Column('observation_count', sa.Integer(), nullable=False),
    sa.Column('history_span_days', sa.Integer(), nullable=False),
    sa.Column('has_3_searches', sa.Boolean(), nullable=False),
    sa.Column('has_7_day_pair', sa.Boolean(), nullable=False),
    sa.Column('has_14_day_pair', sa.Boolean(), nullable=False),
    sa.Column('eligible_for_forecasting', sa.Boolean(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('manifest_id')
    )
    op.create_index(op.f('ix_longitudinal_panel_manifest_eligible_for_forecasting'), 'longitudinal_panel_manifest', ['eligible_for_forecasting'], unique=False)
    op.create_index(op.f('ix_longitudinal_panel_manifest_manifest_id'), 'longitudinal_panel_manifest', ['manifest_id'], unique=False)
    op.create_index(op.f('ix_longitudinal_panel_manifest_route_id'), 'longitudinal_panel_manifest', ['route_id'], unique=False)
    op.create_index(op.f('ix_longitudinal_panel_manifest_travel_date'), 'longitudinal_panel_manifest', ['travel_date'], unique=False)
    op.create_index('ix_longitudinal_panel_manifest_route_date_uniq', 'longitudinal_panel_manifest', ['route_id', 'travel_date'], unique=True)
    
    op.create_table('route_universe',
    sa.Column('route_id', sa.String(length=20), nullable=False),
    sa.Column('canonical_origin_airport', sa.String(length=10), nullable=False),
    sa.Column('canonical_destination_airport', sa.String(length=10), nullable=False),
    sa.Column('city_pair', sa.String(length=50), nullable=False),
    sa.Column('directionality', sa.String(length=20), nullable=False),
    sa.Column('tier', sa.String(length=30), nullable=False),
    sa.Column('is_cpi_basket_member', sa.Boolean(), nullable=False),
    sa.Column('active_status', sa.String(length=20), nullable=False),
    sa.Column('dgca_annual_passenger_share', sa.String(length=20), nullable=True),
    sa.Column('source_of_route', sa.String(length=100), nullable=False),
    sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('route_id')
    )
    op.create_index(op.f('ix_route_universe_canonical_destination_airport'), 'route_universe', ['canonical_destination_airport'], unique=False)
    op.create_index(op.f('ix_route_universe_canonical_origin_airport'), 'route_universe', ['canonical_origin_airport'], unique=False)
    op.create_index(op.f('ix_route_universe_city_pair'), 'route_universe', ['city_pair'], unique=False)
    op.create_index(op.f('ix_route_universe_is_cpi_basket_member'), 'route_universe', ['is_cpi_basket_member'], unique=False)
    op.create_index(op.f('ix_route_universe_route_id'), 'route_universe', ['route_id'], unique=False)
    op.create_index(op.f('ix_route_universe_tier'), 'route_universe', ['tier'], unique=False)
    
    op.create_table('source_capabilities',
    sa.Column('source_id', sa.String(length=40), nullable=False),
    sa.Column('source_name', sa.String(length=100), nullable=False),
    sa.Column('source_type', sa.String(length=30), nullable=False),
    sa.Column('access_status', sa.String(length=40), nullable=False),
    sa.Column('is_public_unrestricted', sa.Boolean(), nullable=False),
    sa.Column('requires_partner_credentials', sa.Boolean(), nullable=False),
    sa.Column('credentials_available', sa.Boolean(), nullable=False),
    sa.Column('rate_limit_per_minute', sa.Integer(), nullable=False),
    sa.Column('fare_search_supported', sa.Boolean(), nullable=False),
    sa.Column('domestic_supported', sa.Boolean(), nullable=False),
    sa.Column('seat_availability_supported', sa.Boolean(), nullable=False),
    sa.Column('ancillary_fare_supported', sa.Boolean(), nullable=False),
    sa.Column('fare_breakdown_supported', sa.Boolean(), nullable=False),
    sa.Column('health_status', sa.String(length=20), nullable=False),
    sa.Column('availability_rate', sa.Float(), nullable=False),
    sa.Column('successful_requests', sa.Integer(), nullable=False),
    sa.Column('failed_requests', sa.Integer(), nullable=False),
    sa.Column('median_response_time_ms', sa.Float(), nullable=False),
    sa.Column('last_success', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_failure', sa.DateTime(timezone=True), nullable=True),
    sa.Column('provenance_doc_url', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('source_id')
    )
    op.create_index(op.f('ix_source_capabilities_source_id'), 'source_capabilities', ['source_id'], unique=False)
    
    op.create_table('source_price_comparisons',
    sa.Column('comparison_id', sa.String(length=64), nullable=False),
    sa.Column('route_id', sa.String(length=20), nullable=False),
    sa.Column('travel_date', sa.Date(), nullable=False),
    sa.Column('carrier', sa.String(length=20), nullable=False),
    sa.Column('source_a', sa.String(length=40), nullable=False),
    sa.Column('source_b', sa.String(length=40), nullable=False),
    sa.Column('fare_a', sa.Float(), nullable=False),
    sa.Column('fare_b', sa.Float(), nullable=False),
    sa.Column('absolute_difference', sa.Float(), nullable=False),
    sa.Column('percentage_difference', sa.Float(), nullable=False),
    sa.Column('search_timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_anomalous', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('comparison_id')
    )
    op.create_index(op.f('ix_source_price_comparisons_comparison_id'), 'source_price_comparisons', ['comparison_id'], unique=False)
    op.create_index(op.f('ix_source_price_comparisons_route_id'), 'source_price_comparisons', ['route_id'], unique=False)
    op.create_index(op.f('ix_source_price_comparisons_travel_date'), 'source_price_comparisons', ['travel_date'], unique=False)
    op.create_index(op.f('ix_source_price_comparisons_carrier'), 'source_price_comparisons', ['carrier'], unique=False)

def downgrade() -> None:
    op.drop_table('source_price_comparisons')
    op.drop_table('source_capabilities')
    op.drop_table('route_universe')
    op.drop_table('longitudinal_panel_manifest')
    op.drop_table('airline_registry')
