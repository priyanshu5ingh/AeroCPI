"""reference_data_schema

Revision ID: 004_reference_data_schema
Revises: 003_hardening_schema
Create Date: 2026-09-07

"""
from alembic import op
import sqlalchemy as sa

revision = '004_reference_data_schema'
down_revision = '003_hardening_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'external_reference_data',
        sa.Column('reference_id', sa.String(length=36), primary_key=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('reference_period', sa.String(length=20), nullable=False),
        sa.Column('route_id', sa.String(length=15), nullable=False),
        sa.Column('origin', sa.String(length=3), nullable=False),
        sa.Column('destination', sa.String(length=3), nullable=False),
        sa.Column('average_fare', sa.Float(), nullable=True),
        sa.Column('passenger_traffic', sa.Integer(), nullable=True),
        sa.Column('publication_date', sa.Date(), nullable=False),
        sa.Column('data_status', sa.String(length=30), nullable=False, server_default='OFFICIAL'),
        sa.Column('provenance_reference_url', sa.String(length=500), nullable=True),
        sa.Column('metadata_info', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_external_reference_data_source', 'external_reference_data', ['source'])
    op.create_index('ix_external_reference_data_reference_period', 'external_reference_data', ['reference_period'])
    op.create_index('ix_external_reference_data_route_id', 'external_reference_data', ['route_id'])

def downgrade() -> None:
    op.drop_index('ix_external_reference_data_route_id', table_name='external_reference_data')
    op.drop_index('ix_external_reference_data_reference_period', table_name='external_reference_data')
    op.drop_index('ix_external_reference_data_source', table_name='external_reference_data')
    op.drop_table('external_reference_data')
