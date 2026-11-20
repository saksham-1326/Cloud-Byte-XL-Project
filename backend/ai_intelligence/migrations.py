"""Explicit, transactional migrations; isolated additive ai_* schema."""
import hashlib
from pathlib import Path


def migrate(connect):
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(73492714)")
            cursor.execute("CREATE TABLE IF NOT EXISTS ai_schema_migrations (name text PRIMARY KEY, checksum text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())")
            for path in sorted((Path(__file__).parents[1] / "migrations").glob("*.sql")):
                sql = path.read_text(encoding="utf-8-sig")
                digest = hashlib.sha256(sql.encode()).hexdigest()
                cursor.execute("SELECT checksum FROM ai_schema_migrations WHERE name=%s", (path.name,))
                row = cursor.fetchone()
                if row:
                    if row[0] != digest:
                        raise RuntimeError("Applied migration checksum mismatch: " + path.name)
                    continue
                cursor.execute(sql)
                cursor.execute("INSERT INTO ai_schema_migrations(name,checksum) VALUES(%s,%s)", (path.name,digest))
