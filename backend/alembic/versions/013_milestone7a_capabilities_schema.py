"""milestone7a_capabilities_schema

Revision ID: 013_milestone7a_capabilities_schema
Revises: 012_milestone4d_statistical_index_schema
Create Date: 2026-09-12

"""
from alembic import op
import sqlalchemy as sa

revision = '013_milestone7a_capabilities_schema'
down_revision = '012_milestone4d_statistical_index_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create measurement_configurations table
    op.create_table(
        'measurement_configurations',
        sa.Column('configuration_id', sa.String(length=36), primary_key=True),
        sa.Column('configuration_version', sa.String(length=50), nullable=False, unique=True),
        sa.Column('basket_version', sa.String(length=50), nullable=False, server_default='DGCA-10-2026.1'),
        sa.Column('horizon_set', sa.JSON(), nullable=False),
        sa.Column('validation_rule_version', sa.String(length=50), nullable=False, server_default='VAL-2026.1'),
        sa.Column('outlier_rule_version', sa.String(length=50), nullable=False, server_default='IQR-1.5-v1'),
        sa.Column('source_policy_version', sa.String(length=50), nullable=False, server_default='MULTI-SOURCE-V1'),
        sa.Column('aggregation_version', sa.String(length=50), nullable=False, server_default='JEVONS-GEOMETRIC-V1'),
        sa.Column('publication_threshold_version', sa.String(length=50), nullable=False, server_default='PUB-THRESH-V1'),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('configuration_fingerprint', sa.String(length=64), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_measurement_configurations_config_ver', 'measurement_configurations', ['configuration_version'])

    # 2. Create observation_qualities table
    op.create_table(
        'observation_qualities',
        sa.Column('quality_id', sa.String(length=36), primary_key=True),
        sa.Column('observation_id', sa.String(length=36), nullable=False),
        sa.Column('completeness_status', sa.String(length=30), nullable=False, server_default='COMPLETE'),
        sa.Column('timestamp_status', sa.String(length=30), nullable=False, server_default='VALID'),
        sa.Column('fare_integrity_status', sa.String(length=30), nullable=False, server_default='VALID'),
        sa.Column('route_mapping_status', sa.String(length=30), nullable=False, server_default='MAPPED'),
        sa.Column('duplicate_risk', sa.String(length=30), nullable=False, server_default='LOW'),
        sa.Column('anomaly_flags', sa.JSON(), nullable=False),
        sa.Column('source_health_status', sa.String(length=30), nullable=False, server_default='HEALTHY'),
        sa.Column('quality_rule_version', sa.String(length=50), nullable=False, server_default='QR-2026.1'),
        sa.Column('quality_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_observation_qualities_obs_id', 'observation_qualities', ['observation_id'])

    # 3. Create validation_benchmarks table
    op.create_table(
        'validation_benchmarks',
        sa.Column('benchmark_id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('reference_period', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_validation_benchmarks_name', 'validation_benchmarks', ['name'])

    # 4. Create validation_runs table
    op.create_table(
        'validation_runs',
        sa.Column('validation_run_id', sa.String(length=36), primary_key=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('index_runs.run_id'), nullable=False),
        sa.Column('benchmark_id', sa.String(length=36), sa.ForeignKey('validation_benchmarks.benchmark_id'), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DISABLED_NO_BENCHMARK_DATA'),
        sa.Column('validation_timestamp', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_validation_runs_run_id', 'validation_runs', ['run_id'])
    op.create_index('ix_validation_runs_benchmark_id', 'validation_runs', ['benchmark_id'])

    # 5. Create validation_metrics table
    op.create_table(
        'validation_metrics',
        sa.Column('metric_id', sa.String(length=36), primary_key=True),
        sa.Column('validation_run_id', sa.String(length=36), sa.ForeignKey('validation_runs.validation_run_id'), nullable=False),
        sa.Column('coverage', sa.Float(), nullable=True),
        sa.Column('directional_agreement', sa.Float(), nullable=True),
        sa.Column('correlation', sa.Float(), nullable=True),
        sa.Column('absolute_deviation', sa.Float(), nullable=True),
        sa.Column('relative_deviation', sa.Float(), nullable=True),
        sa.Column('route_level_deviation', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_validation_metrics_val_run_id', 'validation_metrics', ['validation_run_id'])

def downgrade() -> None:
    op.drop_table('validation_metrics')
    op.drop_table('validation_runs')
    op.drop_table('validation_benchmarks')
    op.drop_table('observation_qualities')
    op.drop_table('measurement_configurations')
