"""milestone4d_statistical_index_schema

Revision ID: 012_milestone4d_statistical_index_schema
Revises: 011_trust_evaluation_schema
Create Date: 2026-09-12

"""
from alembic import op
import sqlalchemy as sa

revision = '012_milestone4d_statistical_index_schema'
down_revision = '011_trust_evaluation_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create horizon_index_results table
    op.create_table(
        'horizon_index_results',
        sa.Column('result_id', sa.String(length=36), primary_key=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('index_runs.run_id'), nullable=False),
        sa.Column('horizon_code', sa.String(length=10), nullable=False),
        sa.Column('horizon_days', sa.Integer(), nullable=False),
        sa.Column('index_name', sa.String(length=50), nullable=False),
        sa.Column('index_value', sa.Float(), nullable=False),
        sa.Column('matched_sample_index_value', sa.Float(), nullable=True),
        sa.Column('base_coverage_ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('current_coverage_ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('matched_coverage_ratio', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('active_weight_sum', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('active_routes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('base_routes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_basket_routes_count', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('is_headline', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_horizon_index_results_run_id', 'horizon_index_results', ['run_id'])
    op.create_index('ix_horizon_index_results_horizon_code', 'horizon_index_results', ['horizon_code'])
    op.create_index('ix_horizon_index_results_index_name', 'horizon_index_results', ['index_name'])

    # 2. Add trust_evaluation_id to index_runs
    with op.batch_alter_table('index_runs') as batch_op:
        batch_op.add_column(sa.Column('trust_evaluation_id', sa.String(length=36), nullable=True))
        batch_op.alter_column('dataset_version_id', existing_type=sa.String(length=50), nullable=True)
        batch_op.create_index('ix_index_runs_trust_evaluation_id', ['trust_evaluation_id'])

def downgrade() -> None:
    with op.batch_alter_table('index_runs') as batch_op:
        batch_op.drop_index('ix_index_runs_trust_evaluation_id')
        batch_op.drop_column('trust_evaluation_id')
        batch_op.alter_column('dataset_version_id', existing_type=sa.String(length=50), nullable=False)
    
    op.drop_table('horizon_index_results')
