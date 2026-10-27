"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-26 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('canonical_url', sa.String(length=2048), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(length=2048), nullable=True),
        sa.Column('sku', sa.String(length=100), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_products_canonical_url', 'products', ['canonical_url'], unique=True)
    op.create_index('ix_products_domain', 'products', ['domain'], unique=False)

    # 2. tracked_products table
    op.create_table(
        'tracked_products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('target_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('notify_on_drop', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('notify_on_target', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_tracked_products_product_id', 'tracked_products', ['product_id'], unique=False)

    # 3. price_snapshots table
    op.create_table(
        'price_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('original_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=10), server_default='USD', nullable=False),
        sa.Column('in_stock', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('seller', sa.String(length=255), nullable=True),
        sa.Column('scraped_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_price_snapshots_product_id', 'price_snapshots', ['product_id'], unique=False)
    op.create_index('ix_price_snapshots_scraped_at', 'price_snapshots', ['scraped_at'], unique=False)

    # 4. scrape_jobs table
    op.create_table(
        'scrape_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=True),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='PENDING', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_scrape_jobs_product_id', 'scrape_jobs', ['product_id'], unique=False)
    op.create_index('ix_scrape_jobs_status', 'scrape_jobs', ['status'], unique=False)

    # 5. alerts table
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('tracked_product_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tracked_products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('threshold_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('triggered_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_alerts_tracked_product_id', 'alerts', ['tracked_product_id'], unique=False)
    op.create_index('ix_alerts_is_read', 'alerts', ['is_read'], unique=False)
    op.create_index('ix_alerts_triggered_at', 'alerts', ['triggered_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_alerts_triggered_at', table_name='alerts')
    op.drop_index('ix_alerts_is_read', table_name='alerts')
    op.drop_index('ix_alerts_tracked_product_id', table_name='alerts')
    op.drop_table('alerts')

    op.drop_index('ix_scrape_jobs_status', table_name='scrape_jobs')
    op.drop_index('ix_scrape_jobs_product_id', table_name='scrape_jobs')
    op.drop_table('scrape_jobs')

    op.drop_index('ix_price_snapshots_scraped_at', table_name='price_snapshots')
    op.drop_index('ix_price_snapshots_product_id', table_name='price_snapshots')
    op.drop_table('price_snapshots')

    op.drop_index('ix_tracked_products_product_id', table_name='tracked_products')
    op.drop_table('tracked_products')

    op.drop_index('ix_products_domain', table_name='products')
    op.drop_index('ix_products_canonical_url', table_name='products')
    op.drop_table('products')
