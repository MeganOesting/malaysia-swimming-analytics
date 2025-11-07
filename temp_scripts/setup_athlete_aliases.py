"""Create and seed the athlete_aliases table with canonical names."""

import sqlite3
from pathlib import Path


DB_PATH = Path("malaysia_swimming.db")


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS athlete_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            athlete_id TEXT NOT NULL,
            alias_fullname TEXT NOT NULL,
            is_canonical INTEGER NOT NULL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(athlete_id) REFERENCES athletes(id)
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_athlete_aliases_alias
        ON athlete_aliases(alias_fullname COLLATE NOCASE)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_athlete_aliases_athlete
        ON athlete_aliases(athlete_id)
        """
    )


def seed_canonical_aliases(conn: sqlite3.Connection) -> tuple[int, int]:
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT id, FULLNAME
        FROM athletes
        WHERE FULLNAME IS NOT NULL AND TRIM(FULLNAME) <> ''
        """
    ).fetchall()

    inserted = 0
    updated = 0

    for athlete_id, fullname in rows:
        fullname_stripped = fullname.strip()
        if not fullname_stripped:
            continue

        existing = cursor.execute(
            """
            SELECT id, is_canonical
            FROM athlete_aliases
            WHERE LOWER(alias_fullname) = LOWER(?)
            """,
            (fullname_stripped,),
        ).fetchone()

        if existing is None:
            cursor.execute(
                """
                INSERT INTO athlete_aliases (athlete_id, alias_fullname, is_canonical)
                VALUES (?, ?, 1)
                """,
                (athlete_id, fullname_stripped),
            )
            inserted += 1
        else:
            alias_id, is_canonical = existing
            if not is_canonical:
                cursor.execute(
                    """
                    UPDATE athlete_aliases
                    SET athlete_id = ?, is_canonical = 1
                    WHERE id = ?
                    """,
                    (athlete_id, alias_id),
                )
                updated += 1

    return inserted, updated


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_table(conn)
        inserted, updated = seed_canonical_aliases(conn)
        conn.commit()
        print(
            f"Alias table ready. Inserted {inserted} canonical aliases, "
            f"updated {updated} existing entries."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    main()

