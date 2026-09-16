"""014_multisource_orchestration_schema

Revision ID: 014_multisource_orchestration_schema
Revises: 013_milestone7a_capabilities_schema
Create Date: 2026-09-16

"""
from alembic import op
import sqlalchemy as sa

revision = '014_multisource_orchestration_schema'
down_revision = '013_milestone7a_capabilities_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Add multi-source columns to observations if not present
    conn = op.get_bind()
    insp = sa.inspect(conn)
    columns = [c['name'] for c in insp.get_columns('observations')]
    
    with op.batch_alter_table('observations') as batch_op:
        if 'collection_run_id' not in columns:
            batch_op.add_column(sa.Column('collection_run_id', sa.String(50), nullable=True))
        if 'collection_attempt_id' not in columns:
            batch_op.add_column(sa.Column('collection_attempt_id', sa.String(50), nullable=True))
        if 'comparability_id' not in columns:
            batch_op.add_column(sa.Column('comparability_id', sa.String(64), nullable=True))
        if 'source_quote_id' not in columns:
            batch_op.add_column(sa.Column('source_quote_id', sa.String(100), nullable=True))
        if 'adapter_version' not in columns:
            batch_op.add_column(sa.Column('adapter_version', sa.String(20), nullable=True, server_default='1.0.0'))
        if 'capture_method' not in columns:
            batch_op.add_column(sa.Column('capture_method', sa.String(40), nullable=True, server_default='SEARCH_QUERY'))
        if 'source_status_at_capture' not in columns:
            batch_op.add_column(sa.Column('source_status_at_capture', sa.String(40), nullable=True, server_default='LIVE_OBSERVED'))
        if 'provenance_metadata' not in columns:
            batch_op.add_column(sa.Column('provenance_metadata', sa.JSON(), nullable=True))

    # 2. Create collection_runs table if not exists
    tables = insp.get_table_names()
    if 'collection_runs' not in tables:
        op.create_table(
            'collection_runs',
            sa.Column('run_id', sa.String(50), primary_key=True),
            sa.Column('run_type', sa.String(30), nullable=False, server_default='LONGITUDINAL_PANEL'),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('routes_attempted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('sources_attempted', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('queries_total', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('queries_success', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('queries_failed', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('observations_saved', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('errors_by_source', sa.JSON(), nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='RUNNING'),
            sa.Column('cadence', sa.String(30), nullable=False, server_default='DAILY_SCHEDULED'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        )

    # 3. Create collection_attempts table if not exists
    if 'collection_attempts' not in tables:
        op.create_table(
            'collection_attempts',
            sa.Column('attempt_id', sa.String(50), primary_key=True),
            sa.Column('run_id', sa.String(50), nullable=False),
            sa.Column('source_id', sa.String(40), nullable=False),
            sa.Column('origin', sa.String(10), nullable=False),
            sa.Column('destination', sa.String(10), nullable=False),
            sa.Column('route_id', sa.String(20), nullable=False),
            sa.Column('travel_date', sa.Date(), nullable=False),
            sa.Column('apw', sa.Integer(), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('latency_ms', sa.Float(), nullable=True),
            sa.Column('status', sa.String(30), nullable=False, server_default='SUCCESS'),
            sa.Column('error_class', sa.String(50), nullable=True),
            sa.Column('error_detail', sa.String(500), nullable=True),
            sa.Column('observations_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('raw_payload_sha256', sa.String(64), nullable=True),
        )


def downgrade() -> None:
    pass
