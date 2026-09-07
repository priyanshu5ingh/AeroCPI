"""milestone2_schema

Revision ID: 002_milestone2_schema
Revises: 001_initial_schema
Create Date: 2026-09-07

"""
from alembic import op
import sqlalchemy as sa

revision = '002_milestone2_schema'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'dataset_versions',
        sa.Column('dataset_version_id', sa.String(length=50), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('source_status', sa.String(length=30), nullable=False, server_default='OBSERVED'),
        sa.Column('record_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('fingerprint', sa.String(length=64), nullable=False),
    )

    op.create_table(
        'proxy_route_weights',
        sa.Column('weight_version_id', sa.String(length=50), primary_key=True, nullable=False),
        sa.Column('route_id', sa.String(length=15), sa.ForeignKey('routes.route_id'), primary_key=True, nullable=False),
        sa.Column('weight_share', sa.Numeric(precision=8, scale=6), nullable=False),
        sa.Column('weight_type', sa.String(length=50), nullable=False, server_default='DGCA_TRAFFIC_SHARE_PROXY'),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_proxy_route_weights_route_id', 'proxy_route_weights', ['route_id'])

    op.create_table(
        'index_runs',
        sa.Column('run_id', sa.String(length=36), primary_key=True),
        sa.Column('run_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reference_period', sa.String(length=20), nullable=False),
        sa.Column('comparison_period', sa.String(length=20), nullable=False),
        sa.Column('dataset_version_id', sa.String(length=50), sa.ForeignKey('dataset_versions.dataset_version_id'), nullable=False),
        sa.Column('route_basket_version', sa.String(length=50), nullable=False, server_default='BASKET_2026_Q1'),
        sa.Column('proxy_weight_version', sa.String(length=50), nullable=False, server_default='DGCA_PROXY_2026_V1'),
        sa.Column('methodology_version', sa.String(length=50), nullable=False, server_default='JEVONS_YOUNG_LASPEYRES_V1'),
        sa.Column('normalization_version', sa.String(length=30), nullable=False, server_default='V1_SIMPLE_SUM'),
        sa.Column('quality_rule_version', sa.String(length=30), nullable=False, server_default='V1_MAD_DUPLICATE_CHECKS'),
        sa.Column('index_method', sa.String(length=50), nullable=False, server_default='JEVONS_YOUNG_LASPEYRES'),
        sa.Column('number_of_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('number_of_eligible_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('number_of_excluded_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('number_of_outlier_flagged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('number_of_retained_warning', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('number_of_duplicates', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('coverage_ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('index_value', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('software_version', sa.String(length=30), nullable=False, server_default='0.2.0-milestone2'),
        sa.Column('canonical_run_fingerprint', sa.String(length=64), nullable=False),
    )
    op.create_index('ix_index_runs_dataset_version_id', 'index_runs', ['dataset_version_id'])

    op.create_table(
        'route_index_results',
        sa.Column('result_id', sa.String(length=36), primary_key=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('index_runs.run_id'), nullable=False),
        sa.Column('route_id', sa.String(length=15), sa.ForeignKey('routes.route_id'), nullable=False),
        sa.Column('origin_code', sa.String(length=10), nullable=False),
        sa.Column('destination_code', sa.String(length=10), nullable=False),
        sa.Column('travel_date', sa.Date(), nullable=True),
        sa.Column('booking_horizon', sa.Integer(), nullable=False),
        sa.Column('cabin', sa.String(length=20), nullable=False, server_default='ECONOMY'),
        sa.Column('stop_type', sa.String(length=20), nullable=False, server_default='NON_STOP'),
        sa.Column('reference_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('price_relative', sa.Float(), nullable=False),
        sa.Column('route_index_value', sa.Float(), nullable=False),
        sa.Column('weight_share', sa.Float(), nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('eligible_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('excluded_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('flagged_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.create_index('ix_route_index_results_run_id', 'route_index_results', ['run_id'])
    op.create_index('ix_route_index_results_route_id', 'route_index_results', ['route_id'])

def downgrade() -> None:
    op.drop_table('route_index_results')
    op.drop_table('index_runs')
    op.drop_table('proxy_route_weights')
    op.drop_table('dataset_versions')
