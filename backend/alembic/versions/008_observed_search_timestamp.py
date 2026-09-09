"""observed_search_timestamp

Revision ID: 008_observed_search_timestamp
Revises: 007_canonical_observation_schema
Create Date: 2026-09-09

"""
from alembic import op
import sqlalchemy as sa

revision = '008_observed_search_timestamp'
down_revision = '007_canonical_observation_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    with op.batch_alter_table('observations') as batch_op:
        batch_op.add_column(sa.Column('search_timestamp', sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index('idx_obs_search_timestamp', ['search_timestamp'])

def downgrade() -> None:
    with op.batch_alter_table('observations') as batch_op:
        batch_op.drop_index('idx_obs_search_timestamp')
        batch_op.drop_column('search_timestamp')
