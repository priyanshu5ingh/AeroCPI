"""mospi_cpi2024_schema

Revision ID: 005_mospi_cpi2024_schema
Revises: 004_reference_data_schema
Create Date: 2026-09-08

"""
from alembic import op
import sqlalchemy as sa

revision = '005_mospi_cpi2024_schema'
down_revision = '004_reference_data_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add new columns to external_reference_data
    op.add_column('external_reference_data', sa.Column('reference_dataset_id', sa.String(length=50), nullable=True))
    op.add_column('external_reference_data', sa.Column('publisher', sa.String(length=100), nullable=False, server_default='MoSPI / NSO'))
    op.add_column('external_reference_data', sa.Column('dataset_name', sa.String(length=150), nullable=False, server_default='CPI-2024 Airfare Official Reference Series'))
    op.add_column('external_reference_data', sa.Column('month', sa.String(length=10), nullable=True))
    op.add_column('external_reference_data', sa.Column('base_year', sa.Integer(), nullable=False, server_default='2024'))
    op.add_column('external_reference_data', sa.Column('series_type', sa.String(length=20), nullable=False, server_default='CURRENT'))
    op.add_column('external_reference_data', sa.Column('geography', sa.String(length=50), nullable=False, server_default='All India'))
    op.add_column('external_reference_data', sa.Column('sector', sa.String(length=50), nullable=False, server_default='Combined'))
    op.add_column('external_reference_data', sa.Column('division_code', sa.String(length=10), nullable=True, server_default='07'))
    op.add_column('external_reference_data', sa.Column('group_code', sa.String(length=10), nullable=True, server_default='07.3'))
    op.add_column('external_reference_data', sa.Column('class_code', sa.String(length=15), nullable=True, server_default='07.3.3'))
    op.add_column('external_reference_data', sa.Column('subclass_code', sa.String(length=20), nullable=True, server_default='07.3.3.1'))
    op.add_column('external_reference_data', sa.Column('item_code', sa.String(length=20), nullable=False, server_default='07.3.3.1.2.01'))
    op.add_column('external_reference_data', sa.Column('item_label', sa.String(length=100), nullable=False, server_default='Airfare'))
    op.add_column('external_reference_data', sa.Column('index_value', sa.Float(), nullable=True))
    op.add_column('external_reference_data', sa.Column('inflation_value', sa.Float(), nullable=True))
    op.add_column('external_reference_data', sa.Column('inflation_type', sa.String(length=10), nullable=False, server_default='YOY'))
    op.add_column('external_reference_data', sa.Column('revision_status', sa.String(length=20), nullable=False, server_default='FINAL'))
    
    # CPI Weight fields
    op.add_column('external_reference_data', sa.Column('cpi_weight_value', sa.Float(), nullable=True))
    op.add_column('external_reference_data', sa.Column('cpi_weight_unit', sa.String(length=30), nullable=False, server_default='percent_of_CPI'))
    op.add_column('external_reference_data', sa.Column('cpi_weight_scope', sa.String(length=50), nullable=False, server_default='All India Combined'))
    op.add_column('external_reference_data', sa.Column('cpi_weight_source', sa.String(length=150), nullable=False, server_default='MoSPI Expert Group Report — Annexure 5.3d'))
    op.add_column('external_reference_data', sa.Column('cpi_weight_source_document', sa.String(length=200), nullable=False, server_default='Expert Group Report on Comprehensive Updation of Consumer Price Index, January 2026'))
    
    # Provenance fields
    op.add_column('external_reference_data', sa.Column('provenance_status', sa.String(length=30), nullable=False, server_default='PARTIAL'))
    op.add_column('external_reference_data', sa.Column('source_url', sa.String(length=500), nullable=True))
    op.add_column('external_reference_data', sa.Column('source_document', sa.String(length=200), nullable=True))
    op.add_column('external_reference_data', sa.Column('source_sheet', sa.String(length=50), nullable=True))
    op.add_column('external_reference_data', sa.Column('download_timestamp', sa.DateTime(timezone=True), nullable=True))
    op.add_column('external_reference_data', sa.Column('source_file_sha256', sa.String(length=64), nullable=True))
    op.add_column('external_reference_data', sa.Column('canonical_dataset_sha256', sa.String(length=64), nullable=True))
    op.add_column('external_reference_data', sa.Column('notes', sa.String(length=500), nullable=True))

    # Allow route fields to be nullable for item-level MoSPI records
    with op.batch_alter_table('external_reference_data') as batch_op:
        batch_op.alter_column('route_id', existing_type=sa.String(length=15), nullable=True)
        batch_op.alter_column('origin', existing_type=sa.String(length=3), nullable=True)
        batch_op.alter_column('destination', existing_type=sa.String(length=3), nullable=True)
        batch_op.create_index('ix_external_reference_data_series_type', ['series_type'])
        batch_op.create_index('ix_external_reference_data_item_code', ['item_code'])

def downgrade() -> None:
    pass
