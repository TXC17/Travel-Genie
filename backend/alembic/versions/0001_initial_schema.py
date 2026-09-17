"""Initial database schema with 14 core tables

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-29 01:54:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. Destinations table
    op.create_table(
        'destinations',
        sa.Column('id', sa.String(length=50), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('best_season', sa.String(length=100), nullable=False),
        sa.Column('hero_image_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_destinations_name', 'destinations', ['name'], unique=True)

    # 3. Seasonal Data table
    op.create_table(
        'seasonal_data',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('destination_id', sa.String(length=50), sa.ForeignKey('destinations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('month_name', sa.String(length=20), nullable=False),
        sa.Column('suitability_score', sa.Float(), nullable=False),
        sa.Column('climate_type', sa.String(length=100), nullable=False),
        sa.Column('rainfall_level', sa.String(length=50), nullable=False),
        sa.Column('crowd_demand', sa.String(length=50), nullable=False),
        sa.Column('water_sports_available', sa.Boolean(), nullable=False, default=True),
        sa.Column('advisory_notice', sa.Text(), nullable=True),
        sa.Column('provenance', sa.JSON(), nullable=False, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('destination_id', 'month', name='uq_destination_month'),
    )
    op.create_index('ix_seasonal_data_destination_id', 'seasonal_data', ['destination_id'])

    # 4. Attraction Categories table
    op.create_table(
        'attraction_categories',
        sa.Column('id', sa.String(length=50), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_name', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 5. Attractions table
    op.create_table(
        'attractions',
        sa.Column('id', sa.String(length=100), primary_key=True),
        sa.Column('destination_id', sa.String(length=50), sa.ForeignKey('destinations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('category_id', sa.String(length=50), sa.ForeignKey('attraction_categories.id'), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('average_visit_duration', sa.Float(), nullable=False),
        sa.Column('entry_fee', sa.Float(), nullable=False, default=0.0),
        sa.Column('popularity_score', sa.Float(), nullable=False, default=0.5),
        sa.Column('rating', sa.Float(), nullable=False, default=4.0),
        sa.Column('opening_time', sa.String(length=10), nullable=True),
        sa.Column('closing_time', sa.String(length=10), nullable=True),
        sa.Column('best_time_to_visit', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False, default=list),
        sa.Column('seasonal_scores', sa.JSON(), nullable=False, default=dict),
        sa.Column('crowd_heuristics', sa.JSON(), nullable=False, default=dict),
        sa.Column('provenance', sa.JSON(), nullable=False, default=dict),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('duration_estimation_method', sa.String(length=100), nullable=False, default='curated_empirical_average'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_attractions_destination_id', 'attractions', ['destination_id'])
    op.create_index('ix_attractions_category', 'attractions', ['category'])
    op.create_index('ix_attractions_name', 'attractions', ['name'])

    # 6. Trips table
    op.create_table(
        'trips',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('creator_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('destination_id', sa.String(length=50), sa.ForeignKey('destinations.id'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('start_date', sa.String(length=10), nullable=False),
        sa.Column('end_date', sa.String(length=10), nullable=False),
        sa.Column('number_of_days', sa.Integer(), nullable=False),
        sa.Column('party_size', sa.Integer(), nullable=False, default=1),
        sa.Column('total_budget', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, default='draft'),
        sa.Column('invite_code', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_trips_creator_id', 'trips', ['creator_id'])
    op.create_index('ix_trips_destination_id', 'trips', ['destination_id'])
    op.create_index('ix_trips_invite_code', 'trips', ['invite_code'], unique=True)

    # 7. Trip Preferences table
    op.create_table(
        'trip_preferences',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('trip_id', sa.String(length=36), sa.ForeignKey('trips.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('interests', sa.JSON(), nullable=False, default=list),
        sa.Column('pace', sa.String(length=30), nullable=False, default='Moderate'),
        sa.Column('preferred_transport', sa.String(length=30), nullable=False, default='auto'),
        sa.Column('max_daily_travel_hours', sa.Float(), nullable=False, default=4.0),
        sa.Column('budget_tier', sa.String(length=30), nullable=False, default='Standard'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Itineraries table
    op.create_table(
        'itineraries',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('trip_id', sa.String(length=36), sa.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('is_current', sa.Boolean(), nullable=False, default=True),
        sa.Column('total_estimated_cost', sa.Float(), nullable=False, default=0.0),
        sa.Column('total_travel_distance_km', sa.Float(), nullable=False, default=0.0),
        sa.Column('total_travel_duration_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('total_sightseeing_duration_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('optimization_metrics', sa.JSON(), nullable=False, default=dict),
        sa.Column('explanation_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_itineraries_trip_id', 'itineraries', ['trip_id'])

    # 9. Itinerary Days table
    op.create_table(
        'itinerary_days',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('itinerary_id', sa.String(length=36), sa.ForeignKey('itineraries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('date', sa.String(length=10), nullable=False),
        sa.Column('cluster_id', sa.Integer(), nullable=False, default=0),
        sa.Column('day_travel_distance_km', sa.Float(), nullable=False, default=0.0),
        sa.Column('day_travel_duration_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('day_sightseeing_duration_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('day_estimated_cost', sa.Float(), nullable=False, default=0.0),
        sa.Column('recommended_transport', sa.String(length=50), nullable=False),
        sa.Column('transport_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_itinerary_days_itinerary_id', 'itinerary_days', ['itinerary_id'])

    # 10. Itinerary Items table
    op.create_table(
        'itinerary_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('itinerary_day_id', sa.String(length=36), sa.ForeignKey('itinerary_days.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attraction_id', sa.String(length=100), sa.ForeignKey('attractions.id'), nullable=False),
        sa.Column('visit_order', sa.Integer(), nullable=False),
        sa.Column('arrival_time', sa.String(length=10), nullable=False),
        sa.Column('departure_time', sa.String(length=10), nullable=False),
        sa.Column('visit_duration_hours', sa.Float(), nullable=False),
        sa.Column('travel_time_from_prev_hours', sa.Float(), nullable=False, default=0.0),
        sa.Column('distance_from_prev_km', sa.Float(), nullable=False, default=0.0),
        sa.Column('item_cost', sa.Float(), nullable=False, default=0.0),
        sa.Column('crowd_estimate_score', sa.Float(), nullable=False, default=0.5),
        sa.Column('crowd_level', sa.String(length=20), nullable=False, default='Moderate'),
        sa.Column('visit_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_itinerary_items_itinerary_day_id', 'itinerary_items', ['itinerary_day_id'])
    op.create_index('ix_itinerary_items_attraction_id', 'itinerary_items', ['attraction_id'])

    # 11. Trip Members table
    op.create_table(
        'trip_members',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('trip_id', sa.String(length=36), sa.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, default='member'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('trip_id', 'user_id', name='uq_trip_member'),
    )
    op.create_index('ix_trip_members_trip_id', 'trip_members', ['trip_id'])
    op.create_index('ix_trip_members_user_id', 'trip_members', ['user_id'])

    # 12. User Votes table
    op.create_table(
        'user_votes',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('trip_id', sa.String(length=36), sa.ForeignKey('trips.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attraction_id', sa.String(length=100), sa.ForeignKey('attractions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('vote_value', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('trip_id', 'user_id', 'attraction_id', name='uq_user_attraction_vote'),
    )
    op.create_index('ix_user_votes_trip_id', 'user_votes', ['trip_id'])
    op.create_index('ix_user_votes_user_id', 'user_votes', ['user_id'])
    op.create_index('ix_user_votes_attraction_id', 'user_votes', ['attraction_id'])

    # 13. Chat Sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trip_id', sa.String(length=36), sa.ForeignKey('trips.id', ondelete='CASCADE'), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False, default='Trip Planning Chat'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('ix_chat_sessions_trip_id', 'chat_sessions', ['trip_id'])

    # 14. Chat Messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('session_id', sa.String(length=36), sa.ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('extracted_constraints', sa.JSON(), nullable=False, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])


def downgrade() -> None:
    # Drop tables in reverse topological dependency order
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('user_votes')
    op.drop_table('trip_members')
    op.drop_table('itinerary_items')
    op.drop_table('itinerary_days')
    op.drop_table('itineraries')
    op.drop_table('trip_preferences')
    op.drop_table('trips')
    op.drop_table('attractions')
    op.drop_table('attraction_categories')
    op.drop_table('seasonal_data')
    op.drop_table('destinations')
    op.drop_table('users')
