"""Add accommodations table and link to trips

Revision ID: 0002_add_accommodations
Revises: 0001_initial_schema
Create Date: 2026-10-13 23:25:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_add_accommodations'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Idempotently create accommodations table if it does not already exist
    if 'accommodations' not in existing_tables:
        op.create_table(
            'accommodations',
            sa.Column('id', sa.String(length=60), primary_key=True),
            sa.Column(
                'destination_id',
                sa.String(length=50),
                sa.ForeignKey('destinations.id', ondelete='CASCADE'),
                nullable=False,
            ),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('accommodation_type', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('price_per_night', sa.Float(), nullable=False),
            sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
            sa.Column('rating', sa.Float(), nullable=False, server_default='4.0'),
            sa.Column('room_capacity', sa.Integer(), nullable=False, server_default='2'),
            sa.Column('amenities', sa.JSON(), nullable=False),
            sa.Column('image_url', sa.String(length=500), nullable=True),
            sa.Column('booking_url', sa.String(length=500), nullable=True),
            sa.Column('contact_phone', sa.String(length=50), nullable=True),
            sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('provenance', sa.JSON(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        )
    else:
        # Verify pre-existing table schema integrity without masking unrelated errors
        existing_cols = {col['name'] for col in inspector.get_columns('accommodations')}
        required_cols = {'id', 'destination_id', 'name', 'price_per_night', 'room_capacity'}
        missing = required_cols - existing_cols
        if missing:
            raise RuntimeError(
                f"Pre-existing 'accommodations' table is missing required schema columns: {missing}"
            )

    # 2. Idempotently create indexes on accommodations
    existing_indexes = set()
    try:
        for idx in inspector.get_indexes('accommodations'):
            if idx.get('name'):
                existing_indexes.add(idx['name'])
    except Exception:
        pass

    if 'ix_accommodations_destination_id' not in existing_indexes:
        op.create_index('ix_accommodations_destination_id', 'accommodations', ['destination_id'])
    if 'ix_accommodations_name' not in existing_indexes:
        op.create_index('ix_accommodations_name', 'accommodations', ['name'])

    # 3. Add selected_accommodation_id to trips table if not present
    trip_columns = {col['name'] for col in inspector.get_columns('trips')}
    if 'selected_accommodation_id' not in trip_columns:
        with op.batch_alter_table('trips') as batch_op:
            batch_op.add_column(
                sa.Column(
                    'selected_accommodation_id',
                    sa.String(length=60),
                    sa.ForeignKey('accommodations.id', ondelete='SET NULL', name='fk_trips_selected_accommodation_id'),
                    nullable=True,
                )
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. Remove selected_accommodation_id from trips table if present
    if 'trips' in existing_tables:
        trip_columns = {col['name'] for col in inspector.get_columns('trips')}
        if 'selected_accommodation_id' in trip_columns:
            with op.batch_alter_table('trips') as batch_op:
                batch_op.drop_column('selected_accommodation_id')

    # 2. Drop accommodations table and indexes if present
    if 'accommodations' in existing_tables:
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('accommodations') if idx.get('name')}
        if 'ix_accommodations_name' in existing_indexes:
            op.drop_index('ix_accommodations_name', table_name='accommodations')
        if 'ix_accommodations_destination_id' in existing_indexes:
            op.drop_index('ix_accommodations_destination_id', table_name='accommodations')
        op.drop_table('accommodations')
