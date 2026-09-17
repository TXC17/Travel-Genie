# Travel Genie: Relational Database Schema & Alembic Migration Specification

## 1. Schema Overview

The Travel Genie relational database is designed with **14 normalized tables** in PostgreSQL 16 (with full compatibility for SQLite during local rapid development).

```
                                      +--------------------+
                                      |       USERS        |
                                      +---------+----------+
                                                |
                 +------------------------------+------------------------------+
                 | 1:N                          | 1:N                          | 1:N
                 v                              v                              v
       +---------+----------+         +---------+----------+         +---------+----------+
       |       TRIPS        |         |    TRIP_MEMBERS    |         |   CHAT_SESSIONS    |
       +---------+----------+         +--------------------+         +---------+----------+
                 |                                                             |
                 | 1:1                                                         | 1:N
                 +---------------------> TRIP_PREFERENCES                      v
                 |                                                   +---------+----------+
                 | 1:N                                               |   CHAT_MESSAGES    |
                 +---------------------> USER_VOTES                  +--------------------+
                 |
                 | 1:N
                 v
       +---------+----------+
       |    ITINERARIES     |
       +---------+----------+
                 |
                 | 1:N
                 v
       +---------+----------+
       |   ITINERARY_DAYS   |
       +---------+----------+
                 |
                 | 1:N
                 v
       +---------+----------+         +--------------------+
       |  ITINERARY_ITEMS   +-------->|    ATTRACTIONS     |
       +--------------------+ N:1     +---------+----------+
                                                |
                                                | N:1
                                                v
                                      +---------+----------+
                                      |    DESTINATIONS    |<----+ SEASONAL_DATA (12 per dest)
                                      +--------------------+
```

---

## 2. Table Catalog (14 Core Tables)

| # | Table Name | Description | Key Foreign Keys & Constraints |
| :--- | :--- | :--- | :--- |
| 1 | **`users`** | Registered users & authentication profiles | Unique email index, bcrypt hash |
| 2 | **`destinations`** | Supported travel destinations (Dandeli, Coorg, Hampi, Goa) | Unique name index, central coordinates |
| 3 | **`seasonal_data`** | Monthly climate, suitability, & weather alerts (48 records) | FK `destinations.id`, Unique (`destination_id`, `month`) |
| 4 | **`attraction_categories`**| 5 normalized tourist attraction categories | Unique name index |
| 5 | **`attractions`** | Curated points of interest with verified provenance (40 records) | FK `destinations.id`, FK `attraction_categories.id` |
| 6 | **`trips`** | User planning sessions and trip parameters | FK `users.id`, FK `destinations.id`, Unique `invite_code` |
| 7 | **`trip_preferences`** | Detailed constraints (interests, pace, budget tier, max travel) | FK `trips.id` (Unique 1:1) |
| 8 | **`itineraries`** | Multi-day optimized itinerary header & overall metrics | FK `trips.id` |
| 9 | **`itinerary_days`** | Day-level groupings (Day 1..K) corresponding to spatial clusters | FK `itineraries.id` |
| 10 | **`itinerary_items`** | Sequenced visit timeline, waypoint arrival/departure, fees | FK `itinerary_days.id`, FK `attractions.id` |
| 11 | **`trip_members`** | Multi-user trip collaboration roles (owner, editor, member) | FK `trips.id`, FK `users.id`, Unique (`trip_id`, `user_id`) |
| 12 | **`user_votes`** | Member voting record for attraction consensus | FK `trips.id`, FK `users.id`, FK `attractions.id`, Unique (`trip_id`, `user_id`, `attraction_id`) |
| 13 | **`chat_sessions`** | Conversational planning sessions | FK `users.id`, FK `trips.id` |
| 14 | **`chat_messages`** | Individual chat turns with extracted Pydantic constraints | FK `chat_sessions.id` |

---

## 3. Alembic Database Migration Management

Alembic is the authoritative schema migration tool for Travel Genie.

### Migration Commands
```bash
# Navigate to backend directory
cd backend

# Apply all pending migrations (Upgrade to latest schema)
alembic upgrade head

# Rollback last migration (Downgrade 1 revision)
alembic downgrade -1

# Rollback to clean empty database
alembic downgrade base

# Create a new migration revision automatically from updated models
alembic revision --autogenerate -m "describe_schema_change"

# Check current migration revision
alembic current
```
