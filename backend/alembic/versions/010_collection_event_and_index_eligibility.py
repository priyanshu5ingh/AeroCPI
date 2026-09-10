"""collection_event_and_index_eligibility

Revision ID: 010_collection_event_and_index_eligibility
Revises: 009_separate_provenance_hashes
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa

revision = '010_collection_event_and_index_eligibility'
down_revision = '009_separate_provenance_hashes'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'collection_events',
        sa.Column('event_id', sa.String(length=36), primary_key=True),
        sa.Column('source_id', sa.String(length=30), nullable=False, server_default='SRC_GOOGLE_FLIGHTS'),
        sa.Column('origin', sa.String(length=10), nullable=False),
        sa.Column('destination', sa.String(length=10), nullable=False),
        sa.Column('apw', sa.Integer(), nullable=False),
        sa.Column('collection_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SUCCESS'),
        sa.Column('quotes_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('raw_file_path', sa.String(length=500), nullable=True),
        sa.Column('raw_payload_sha256', sa.String(length=64), nullable=True),
        sa.Column('stored_file_sha256', sa.String(length=64), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('error_message', sa.String(length=500), nullable=True),
    )
    op.create_index('idx_coll_evt_route_apw_date', 'collection_events', ['source_id', 'origin', 'destination', 'apw', 'collection_date'], unique=True)
    op.create_index('ix_collection_events_source_id', 'collection_events', ['source_id'])
    op.create_index('ix_collection_events_origin', 'collection_events', ['origin'])
    op.create_index('ix_collection_events_destination', 'collection_events', ['destination'])
    op.create_index('ix_collection_events_apw', 'collection_events', ['apw'])
    op.create_index('ix_collection_events_collection_date', 'collection_events', ['collection_date'])
    op.create_index('ix_collection_events_status', 'collection_events', ['status'])

    with op.batch_alter_table('observations') as batch_op:
        batch_op.add_column(sa.Column('index_eligibility', sa.String(length=20), nullable=False, server_default='INELIGIBLE'))
        batch_op.add_column(sa.Column('index_eligibility_reasons', sa.JSON(), nullable=True))
        batch_op.create_index('ix_observations_index_eligibility', ['index_eligibility'])

def downgrade() -> None:
    with op.batch_alter_table('observations') as batch_op:
        batch_op.drop_index('ix_observations_index_eligibility')
        batch_op.drop_column('index_eligibility_reasons')
        batch_op.drop_column('index_eligibility')

    op.drop_table('collection_events')
