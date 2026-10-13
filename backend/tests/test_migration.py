"""
Regression Test Suite for Alembic Schema Migrations.
Validates:
1. Idempotent recovery when accommodations table pre-exists from Base.metadata.create_all.
2. Missing selected_accommodation_id column is safely added via batch_alter_table.
3. Named foreign key to accommodations.id with ON DELETE SET NULL is created.
4. Existing trips, destinations, and user records are 100% preserved.
5. Downgrade and re-upgrade cycles operate cleanly on SQLite.
"""

import os
import sqlite3
from pathlib import Path
from alembic import command
from alembic.config import Config


def get_alembic_config(db_path: Path) -> Config:
    """Create Alembic Config pointing to a specific SQLite test database."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.as_posix()}")
    return cfg


def test_idempotent_migration_with_pre_existing_accommodations(tmp_path):
    """
    Test scenario:
    Database is at revision 0001_initial_schema.
    A pre-existing 'accommodations' table exists (e.g. from create_all),
    trips has existing data, but trips.selected_accommodation_id is missing.
    Running alembic upgrade head must succeed and preserve all trip records.
    """
    test_db = tmp_path / "test_migration_conflict.db"
    cfg = get_alembic_config(test_db)

    # 1. Upgrade to 0001_initial_schema
    command.upgrade(cfg, "0001_initial_schema")

    # 2. Insert test user, destination, and trips
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (id, email, hashed_password, full_name, is_active, created_at, updated_at) "
        "VALUES ('u1', 'test@travelgenie.ai', 'hashedpw', 'Test User', 1, '2026-10-01', '2026-10-01')"
    )
    cursor.execute(
        "INSERT INTO destinations (id, name, state, description, latitude, longitude, best_season, is_active, created_at, updated_at) "
        "VALUES ('coorg', 'Coorg', 'Karnataka', 'Misty hills', 12.4, 75.7, 'Oct-Mar', 1, '2026-10-01', '2026-10-01')"
    )

    sample_trips = [
        ('t1', 'u1', 'coorg', 'Coorg Weekend Trip', '2026-11-01', '2026-11-03', 3, 2, 15000.0, 'draft', 'INVITE1', '2026-10-01', '2026-10-01'),
        ('t2', 'u1', 'coorg', 'Coorg Family Stay', '2026-11-10', '2026-11-14', 5, 4, 35000.0, 'draft', 'INVITE2', '2026-10-01', '2026-10-01'),
    ]
    cursor.executemany(
        "INSERT INTO trips (id, creator_id, destination_id, title, start_date, end_date, number_of_days, party_size, total_budget, status, invite_code, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        sample_trips
    )
    conn.commit()

    # Verify initial state: 2 trips, no selected_accommodation_id
    cursor.execute("SELECT count(*) FROM trips")
    assert cursor.fetchone()[0] == 2
    cursor.execute("PRAGMA table_info(trips)")
    cols_before = [col[1] for col in cursor.fetchall()]
    assert "selected_accommodation_id" not in cols_before

    # 3. Simulate conflict: create accommodations table out-of-band (like create_all did)
    cursor.execute(
        """
        CREATE TABLE accommodations (
            id VARCHAR(60) NOT NULL PRIMARY KEY,
            destination_id VARCHAR(50) NOT NULL,
            name VARCHAR(150) NOT NULL,
            accommodation_type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            latitude FLOAT NOT NULL,
            longitude FLOAT NOT NULL,
            price_per_night FLOAT NOT NULL,
            currency VARCHAR(10) DEFAULT 'INR' NOT NULL,
            rating FLOAT DEFAULT '4.0' NOT NULL,
            room_capacity INTEGER DEFAULT '2' NOT NULL,
            amenities JSON NOT NULL,
            image_url VARCHAR(500),
            booking_url VARCHAR(500),
            contact_phone VARCHAR(50),
            is_verified BOOLEAN DEFAULT 1 NOT NULL,
            provenance JSON NOT NULL,
            is_active BOOLEAN DEFAULT 1 NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(destination_id) REFERENCES destinations (id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute("CREATE INDEX ix_accommodations_destination_id ON accommodations (destination_id)")
    cursor.execute("CREATE INDEX ix_accommodations_name ON accommodations (name)")
    conn.commit()
    conn.close()

    # 4. Run migration 0002_add_accommodations via alembic upgrade head
    command.upgrade(cfg, "head")

    # 5. Verify successful migration and data preservation
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Check Alembic revision
    cursor.execute("SELECT version_num FROM alembic_version")
    assert cursor.fetchone()[0] == "0002_add_accommodations"

    # Check trips table has selected_accommodation_id
    cursor.execute("PRAGMA table_info(trips)")
    cols_after = [col[1] for col in cursor.fetchall()]
    assert "selected_accommodation_id" in cols_after

    # Check Foreign Keys on trips includes accommodations
    cursor.execute("PRAGMA foreign_key_list(trips)")
    fks = cursor.fetchall()
    assert any(fk[2] == "accommodations" and fk[3] == "selected_accommodation_id" and fk[6] == "SET NULL" for fk in fks)

    # Check trip records are 100% preserved
    cursor.execute("SELECT id, title, total_budget FROM trips ORDER BY id")
    rows = cursor.fetchall()
    assert len(rows) == 2
    assert rows[0] == ('t1', 'Coorg Weekend Trip', 15000.0)
    assert rows[1] == ('t2', 'Coorg Family Stay', 35000.0)

    # Check foreign key check clean
    cursor.execute("PRAGMA foreign_key_check")
    assert cursor.fetchall() == []

    conn.close()


def test_migration_downgrade_and_reupgrade_cycle(tmp_path):
    """Verify clean downgrade to 0001 and re-upgrade to head."""
    test_db = tmp_path / "test_migration_cycle.db"
    cfg = get_alembic_config(test_db)

    # Upgrade to head from scratch
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT version_num FROM alembic_version")
    assert cursor.fetchone()[0] == "0002_add_accommodations"
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accommodations'")
    assert cursor.fetchone() is not None
    conn.close()

    # Downgrade to 0001
    command.downgrade(cfg, "0001_initial_schema")

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT version_num FROM alembic_version")
    assert cursor.fetchone()[0] == "0001_initial_schema"
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accommodations'")
    assert cursor.fetchone() is None
    conn.close()

    # Re-upgrade to head
    command.upgrade(cfg, "head")

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("SELECT version_num FROM alembic_version")
    assert cursor.fetchone()[0] == "0002_add_accommodations"
    cursor.execute("PRAGMA table_info(trips)")
    cols = [col[1] for col in cursor.fetchall()]
    assert "selected_accommodation_id" in cols
    conn.close()
