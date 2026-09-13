"""trust_evaluation_schema

Revision ID: 011_trust_evaluation_schema
Revises: 010_collection_event_and_index_eligibility
Create Date: 2026-09-11

"""
from alembic import op
import sqlalchemy as sa

revision = '011_trust_evaluation_schema'
down_revision = '010_collection_event_and_index_eligibility'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'trust_evaluations',
        sa.Column('trust_evaluation_id', sa.String(length=36), primary_key=True),
        sa.Column('index_run_id', sa.String(length=36), nullable=True),
        sa.Column('route_id', sa.String(length=15), nullable=True),
        sa.Column('travel_date', sa.Date(), nullable=True),
        sa.Column('horizon_code', sa.String(length=20), nullable=True),
        sa.Column('cabin', sa.String(length=20), nullable=True),
        sa.Column('collection_date', sa.Date(), nullable=True),
        sa.Column('trust_engine_version', sa.String(length=20), nullable=False, server_default='v1'),
        sa.Column('trust_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('trust_status', sa.String(length=30), nullable=False),
        sa.Column('coverage_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('agreement_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('sample_sufficiency_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('validity_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('outlier_health_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('source_availability_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('basket_horizon_stability_score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('total_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('eligible_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('flagged_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rejected_observations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('source_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('health_status_from_4c2', sa.String(length=30), nullable=False, server_default='INSUFFICIENT'),
        sa.Column('reason_codes', sa.JSON(), nullable=False),
        sa.Column('dimension_breakdown', sa.JSON(), nullable=True),
        sa.Column('evidence_summary', sa.JSON(), nullable=True),
        sa.Column('calculation_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_trust_eval_route_date_horizon', 'trust_evaluations', ['route_id', 'travel_date', 'horizon_code'])
    op.create_index('idx_trust_eval_fingerprint', 'trust_evaluations', ['calculation_fingerprint'])
    op.create_index('ix_trust_evaluations_index_run_id', 'trust_evaluations', ['index_run_id'])
    op.create_index('ix_trust_evaluations_route_id', 'trust_evaluations', ['route_id'])
    op.create_index('ix_trust_evaluations_travel_date', 'trust_evaluations', ['travel_date'])
    op.create_index('ix_trust_evaluations_horizon_code', 'trust_evaluations', ['horizon_code'])
    op.create_index('ix_trust_evaluations_cabin', 'trust_evaluations', ['cabin'])
    op.create_index('ix_trust_evaluations_collection_date', 'trust_evaluations', ['collection_date'])
    op.create_index('ix_trust_evaluations_trust_status', 'trust_evaluations', ['trust_status'])
    op.create_index('ix_trust_evaluations_calculation_fingerprint', 'trust_evaluations', ['calculation_fingerprint'])

def downgrade() -> None:
    op.drop_table('trust_evaluations')
