"""dgca_route_reference_schema

Revision ID: 006_dgca_route_reference_schema
Revises: 005_mospi_cpi2024_schema
Create Date: 2026-09-08

"""
from alembic import op
import sqlalchemy as sa

revision = '006_dgca_route_reference_schema'
down_revision = '005_mospi_cpi2024_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. city_airport_mappings
    op.create_table(
        'city_airport_mappings',
        sa.Column('raw_city_name', sa.String(), primary_key=True),
        sa.Column('canonical_city_name', sa.String(), nullable=False),
        sa.Column('primary_airport_code', sa.String(), nullable=False),
        sa.Column('metro_area_code', sa.String(), nullable=False),
        sa.Column('is_multi_airport', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('state_or_ut', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_city_airport_mappings_raw_city_name', 'city_airport_mappings', ['raw_city_name'])

    # 2. dgca_reference_datasets
    op.create_table(
        'dgca_reference_datasets',
        sa.Column('dataset_id', sa.String(), primary_key=True),
        sa.Column('publisher', sa.String(), nullable=False, server_default='DGCA'),
        sa.Column('dataset_name', sa.String(), nullable=False),
        sa.Column('reference_period_start', sa.String(), nullable=False),
        sa.Column('reference_period_end', sa.String(), nullable=False),
        sa.Column('months_expected', sa.Integer(), nullable=False, server_default='12'),
        sa.Column('months_available', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('months_missing', sa.Text(), nullable=True),
        sa.Column('completeness_status', sa.String(), nullable=False, server_default='INCOMPLETE'),
        sa.Column('source_status', sa.String(), nullable=False, server_default='PROVENANCE_PARTIAL'),
        sa.Column('canonical_dataset_sha256', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    # 3. dgca_raw_observations
    op.create_table(
        'dgca_raw_observations',
        sa.Column('raw_id', sa.String(), primary_key=True),
        sa.Column('dataset_id', sa.String(), sa.ForeignKey('dgca_reference_datasets.dataset_id'), nullable=False),
        sa.Column('source_filename', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('source_row_index', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('raw_city1', sa.String(), nullable=False),
        sa.Column('raw_city2', sa.String(), nullable=False),
        sa.Column('raw_pax_to', sa.String(), nullable=True),
        sa.Column('raw_pax_from', sa.String(), nullable=True),
        sa.Column('raw_freight_to', sa.String(), nullable=True),
        sa.Column('raw_freight_from', sa.String(), nullable=True),
        sa.Column('raw_mail_to', sa.String(), nullable=True),
        sa.Column('raw_mail_from', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_dgca_raw_obs_dataset_id', 'dgca_raw_observations', ['dataset_id'])

    # 4. dgca_route_month_observations
    op.create_table(
        'dgca_route_month_observations',
        sa.Column('obs_id', sa.String(), primary_key=True),
        sa.Column('dataset_id', sa.String(), sa.ForeignKey('dgca_reference_datasets.dataset_id'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('reference_period', sa.String(), nullable=False),
        sa.Column('canonical_route_key', sa.String(), nullable=False),
        sa.Column('city1_code', sa.String(), nullable=False),
        sa.Column('city2_code', sa.String(), nullable=False),
        sa.Column('origin_airport', sa.String(), nullable=False),
        sa.Column('destination_airport', sa.String(), nullable=False),
        sa.Column('passengers_city1_to_city2', sa.Integer(), nullable=True),
        sa.Column('passengers_city2_to_city1', sa.Integer(), nullable=True),
        sa.Column('combined_passengers', sa.Integer(), nullable=True),
        sa.Column('freight_tons', sa.Float(), nullable=True),
        sa.Column('mail_tons', sa.Float(), nullable=True),
        sa.Column('aggregation_mode', sa.String(), nullable=False, server_default='BIDIRECTIONAL_MERGED'),
        sa.Column('deduplication_status', sa.String(), nullable=False, server_default='DEDUPLICATED'),
        sa.Column('raw_passenger_value', sa.String(), nullable=True),
        sa.Column('normalization_reason', sa.String(), nullable=True),
        sa.Column('source_status', sa.String(), nullable=False, server_default='PROVENANCE_PARTIAL'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_dgca_route_month_obs_route_key', 'dgca_route_month_observations', ['canonical_route_key'])

    # 5. dgca_ingestion_runs
    op.create_table(
        'dgca_ingestion_runs',
        sa.Column('ingestion_id', sa.String(), primary_key=True),
        sa.Column('dataset_id', sa.String(), nullable=False),
        sa.Column('run_timestamp', sa.DateTime(), nullable=False),
        sa.Column('source_files_count', sa.Integer(), nullable=False),
        sa.Column('raw_records_count', sa.Integer(), nullable=False),
        sa.Column('normalized_records_count', sa.Integer(), nullable=False),
        sa.Column('unique_routes_count', sa.Integer(), nullable=False),
        sa.Column('parser_version', sa.String(), nullable=False, server_default='DGCA_PARSER_V1_2026'),
        sa.Column('status', sa.String(), nullable=False, server_default='SUCCESS'),
        sa.Column('ingestion_notes', sa.Text(), nullable=True)
    )

    # 6. dgca_provenance_records
    op.create_table(
        'dgca_provenance_records',
        sa.Column('provenance_id', sa.String(), primary_key=True),
        sa.Column('dataset_id', sa.String(), nullable=False),
        sa.Column('publisher', sa.String(), nullable=False, server_default='DGCA'),
        sa.Column('source_type', sa.String(), nullable=False, server_default='OFFICIAL_DGCA_S3'),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('secondary_discovery_repo', sa.String(), nullable=True, server_default='Vonter/india-aviation-traffic'),
        sa.Column('download_timestamp', sa.DateTime(), nullable=False),
        sa.Column('source_file_sha256', sa.String(), nullable=False),
        sa.Column('canonical_dataset_sha256', sa.String(), nullable=False),
        sa.Column('parser_version', sa.String(), nullable=False, server_default='DGCA_PARSER_V1_2026'),
        sa.Column('schema_version', sa.String(), nullable=False, server_default='DGCA_SCHEMA_V1'),
        sa.Column('source_status', sa.String(), nullable=False, server_default='PROVENANCE_PARTIAL'),
        sa.Column('verification_notes', sa.Text(), nullable=True)
    )

    # 7. route_baskets
    op.create_table(
        'route_baskets',
        sa.Column('basket_id', sa.String(), primary_key=True),
        sa.Column('basket_name', sa.String(), nullable=False),
        sa.Column('reference_period_type', sa.String(), nullable=False, server_default='CALENDAR_YEAR'),
        sa.Column('reference_period_start', sa.String(), nullable=False),
        sa.Column('reference_period_end', sa.String(), nullable=False),
        sa.Column('selection_method', sa.String(), nullable=False, server_default='TOP_N_TRAFFIC'),
        sa.Column('basket_size', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('total_period_passengers', sa.Integer(), nullable=False),
        sa.Column('source_dataset_id', sa.String(), nullable=False),
        sa.Column('methodology_version', sa.String(), nullable=False, server_default='AEROCPI_BASKET_V1_2026'),
        sa.Column('relationship_to_mospi', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    # 8. route_basket_members
    op.create_table(
        'route_basket_members',
        sa.Column('member_id', sa.String(), primary_key=True),
        sa.Column('basket_id', sa.String(), sa.ForeignKey('route_baskets.basket_id'), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('route_id', sa.String(), nullable=False),
        sa.Column('canonical_route_key', sa.String(), nullable=False),
        sa.Column('city_1', sa.String(), nullable=False),
        sa.Column('city_2', sa.String(), nullable=False),
        sa.Column('origin_airport', sa.String(), nullable=False),
        sa.Column('destination_airport', sa.String(), nullable=False),
        sa.Column('period_passengers', sa.Integer(), nullable=False),
        sa.Column('traffic_share', sa.Float(), nullable=False),
        sa.Column('traffic_share_unit', sa.String(), nullable=False, server_default='share_of_basket_traffic'),
        sa.Column('selection_reason', sa.String(), nullable=False),
        sa.Column('source_status', sa.String(), nullable=False, server_default='PROVENANCE_PARTIAL'),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_route_basket_members_basket_id', 'route_basket_members', ['basket_id'])

def downgrade() -> None:
    pass
