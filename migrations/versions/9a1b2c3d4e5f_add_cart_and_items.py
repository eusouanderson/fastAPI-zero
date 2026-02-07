"""add cart and cart_items

Revision ID: 9a1b2c3d4e5f
Revises: 5634b0a78199
Create Date: 2026-02-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9a1b2c3d4e5f'
down_revision = '5634b0a78199'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'carts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_table(
        'cart_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('cart_id', sa.Integer(), sa.ForeignKey('carts.id'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade() -> None:
    op.drop_table('cart_items')
    op.drop_table('carts')
