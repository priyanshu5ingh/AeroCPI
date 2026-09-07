"""hardening_schema

Revision ID: 003_hardening_schema
Revises: 002_milestone2_schema
Create Date: 2026-09-07

"""
from alembic import op
import sqlalchemy as sa

revision = '003_hardening_schema'
down_revision = '002_milestone2_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new columns to index_runs table
    op.add_column('index_runs', sa.Column('frequency', sa.String(length=20), nullable=False, server_default='MONTHLY'))
    op.add_column('index_runs', sa.Column('expected_route_horizon_pairs', sa.Integer(), nullable=False, server_default='40'))
    op.add_column('index_runs', sa.Column('calculated_route_horizon_pairs', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('index_runs', sa.Column('unavailable_route_horizon_pairs', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('index_runs', sa.Column('valid_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('index_runs', sa.Column('outlier_flagged_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('index_runs', sa.Column('retained_with_warning_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('index_runs', sa.Column('excluded_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('index_runs', sa.Column('calculation_manifest', sa.JSON(), nullable=True))

def downgrade() -> None:
    op.drop_column('index_runs', 'calculation_manifest')
    op.drop_column('index_runs', 'excluded_count')
    op.drop_column('index_runs', 'retained_with_warning_count')
    op.drop_column('index_runs', 'outlier_flagged_count')
    op.drop_column('index_runs', 'valid_count')
    op.drop_column('index_runs', 'unavailable_route_horizon_pairs')
    op.drop_column('index_runs', 'calculated_route_horizon_pairs')
    op.drop_column('index_runs', 'expected_route_horizon_pairs')
    op.drop_column('index_runs', 'frequency')
