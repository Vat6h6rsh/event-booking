import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Defaults to SQLite for zero-infra local dev; set DATABASE_URL for PostgreSQL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./booking.db",
)

# Managed hosts (Render, Heroku, Railway) hand out `postgres://` URLs, but
# SQLAlchemy 2.x + psycopg2 require the `postgresql://` scheme. Normalise it so a
# copy-pasted database URL just works.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; PostgreSQL does not accept that kwarg.
# `timeout` lets a request and its background-task session (separate connections)
# wait for each other instead of failing with "database is locked".
connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

pool_options = {} if DATABASE_URL.startswith("sqlite") else {
    "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    "pool_timeout": 10,
    "pool_pre_ping": True,
}
engine = create_engine(DATABASE_URL, connect_args=connect_args, **pool_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
Base = declarative_base()


def ensure_schema():
    """create_all + a tiny additive upgrade for databases created by an older version.

    `create_all` creates missing tables but never alters existing ones, so a DB first
    created by v2 would lack v3's new nullable columns and indexes. Only additive,
    idempotent DDL here — nothing is ever dropped or rewritten.
    """
    from sqlalchemy import inspect, text
    import app.models  # noqa: F401 — register every model on Base.metadata

    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    added = {  # (table, column) -> DDL type, for columns added after v2
        ("bookings", "cancelled_at"): "TIMESTAMP",
        ("notifications", "job_id"): "INTEGER",
    }
    with engine.begin() as conn:
        for (table, column), ddl_type in added.items():
            if column not in {c["name"] for c in insp.get_columns(table)}:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))
        conn.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_job_id ON notifications (job_id)"))
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            index.create(bind=engine, checkfirst=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
