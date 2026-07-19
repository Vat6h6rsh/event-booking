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

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
