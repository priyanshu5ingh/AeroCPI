"""separate_provenance_hashes

Revision ID: 009_separate_provenance_hashes
Revises: 008_observed_search_timestamp
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa

revision = '009_separate_provenance_hashes'
down_revision = '008_observed_search_timestamp'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('observations') as batch_op:
        batch_op.add_column(sa.Column('raw_payload_sha256', sa.String(64), nullable=True))
        batch_op.add_column(sa.Column('stored_file_sha256', sa.String(64), nullable=True))
        batch_op.create_index('idx_obs_raw_payload_sha256', ['raw_payload_sha256'])
        batch_op.create_index('idx_obs_stored_file_sha256', ['stored_file_sha256'])

def downgrade() -> None:
    with op.batch_alter_table('observations') as batch_op:
        batch_op.drop_index('idx_obs_stored_file_sha256')
        batch_op.drop_index('idx_obs_raw_payload_sha256')
        batch_op.drop_column('stored_file_sha256')
        batch_op.drop_column('raw_payload_sha256')
