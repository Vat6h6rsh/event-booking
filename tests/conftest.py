"""
Shared pytest fixtures.

Key design point: we point the *whole app* at an isolated database **before**
importing it, so request-scoped sessions and the separate sessions opened by the
background tasks all share one DB. An externally supplied `DATABASE_URL` is
respected only for a separate test database; otherwise a throwaway SQLite file
is used. The same conditional inventory algorithms run on both backends.
"""
import os
import tempfile
from pathlib import Path
from sqlalchemy.engine import make_url

import pytest

def validate_test_database(url, temporary_path=None):
    parsed = make_url(url)
    database = parsed.database or ""
    is_temporary = (parsed.get_backend_name() == "sqlite" and temporary_path is not None
                    and Path(database).resolve() == Path(temporary_path).resolve())
    if not is_temporary and "test" not in database.lower():
        raise RuntimeError("Refusing non-test DATABASE_URL; use a separate database whose name contains 'test'")


_path = None
if not os.getenv("DATABASE_URL"):
    _fd, _path = tempfile.mkstemp(suffix=".db")
    os.close(_fd)
    os.environ["DATABASE_URL"] = "sqlite:///" + _path.replace("\\", "/")
validate_test_database(os.environ["DATABASE_URL"], _path)
# Prevent implicit .env reads and real transport calls in every test/subprocess.
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
os.environ.setdefault("SECRET_KEY", "isolated-test-secret-key-at-least-32-characters")
os.environ["EMAIL_PROVIDER"] = "console"

from fastapi.testclient import TestClient  # noqa: E402
from app.database import Base, engine, SessionLocal  # noqa: E402
from app.main import app  # noqa: E402


# ── DB lifecycle ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _clean():
    """Empty every table after each test so tests stay independent."""
    yield
    db = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()


# ── Clients & auth helpers ────────────────────────────────────────────────────

@pytest.fixture
def client():
    return TestClient(app)


_counter = {"n": 0}


def _unique_email(prefix: str) -> str:
    _counter["n"] += 1
    return f"{prefix}{_counter['n']}@test.com"


def register(client, role, email=None, password="secret123"):
    email = email or _unique_email(role)
    r = client.post("/signup", json={"email": email, "password": password, "role": role})
    assert r.status_code == 201, r.text
    return email, password


def auth_headers(client, role, email=None, password="secret123"):
    email, password = register(client, role, email, password)
    r = client.post("/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def new_user(client):
    """Factory: fresh authenticated user headers for a given role."""
    def _new(role):
        return auth_headers(client, role)
    return _new


@pytest.fixture
def organizer(client):
    return auth_headers(client, "organizer")


@pytest.fixture
def customer(client):
    return auth_headers(client, "customer")


@pytest.fixture
def make_event(client):
    """Factory: create an event as the given organizer, returns the event JSON."""
    def _make(headers, **overrides):
        body = {
            "name": "Rock Night",
            "venue": "Arena",
            "event_date": "2099-12-01T20:00:00",
            "total_tickets": 10,
        }
        body.update(overrides)
        r = client.post("/events", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()
    return _make
