import logging
import os
from contextlib import asynccontextmanager

import anyio
from sqlalchemy import select, func, text

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import SessionLocal, ensure_schema
from app.models import OutboxJob
from app import outbox, auth as auth_service
from app.middleware import BookingAdmissionMiddleware
from app.routers import (auth, users, events, bookings, venues, support,
                        upload, legal, notifications)

# ── Logging ───────────────────────────────────────────────────────────────────
# Configure once so background-task logs (the [EMAIL] / [NOTIFY] markers) and the
# unhandled-error handler below emit with a consistent, readable format.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-5s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("jtickets")

ensure_schema()


@asynccontextmanager
async def lifespan(app):
    auth_service.validate_secret()
    anyio.to_thread.current_default_thread_limiter().total_tokens = int(os.getenv("THREADPOOL_SIZE", "60"))
    outbox.start()
    try:
        yield
    finally:
        await anyio.to_thread.run_sync(outbox.stop)

app = FastAPI(
    lifespan=lifespan,
    title="Jtickets API",
    description="""
## Jtickets — Event Booking Platform

### How to authenticate
1. Call **`POST /login`** with your email + password.
2. Copy the `access_token` from the response.
3. Click **Authorize** (top-right 🔒) and paste the token in the **Value** field.

All protected endpoints will then work automatically.

### Roles
| Role | Can do |
|------|--------|
| **organizer** | Create/edit events, manage venues & tiers, view support tickets |
| **customer** | Browse events, book tickets, cancel bookings, open support tickets |
""",
    version="3.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Local dev origins are always allowed; the deployed frontend origin(s) come from
# the environment (comma-separated). We accept CORS_ORIGINS (preferred) or the
# common CORS_ORIGIN typo so a misnamed var still works.
_local_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_env_origins = os.getenv("CORS_ORIGINS") or os.getenv("CORS_ORIGIN") or ""
origins = list(dict.fromkeys(
    _local_origins + [o.strip().rstrip("/") for o in _env_origins.split(",") if o.strip()]
))
logger.info("CORS allowed origins: %s", origins)

# Last-added middleware is outermost: CORS must wrap admission-control 503s.
app.add_middleware(BookingAdmissionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Idempotent-Replayed", "Retry-After"],
)

for r in [auth.router, users.router, events.router, bookings.router,
          venues.router, support.router, upload.router, legal.router,
          notifications.router]:
    app.include_router(r)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all so an unexpected error is logged with its traceback and the client
    still gets a clean JSON body instead of a bare 500. (HTTPExceptions keep their
    default `{"detail": ...}` shape, which the frontend already reads.)"""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/", tags=["health"])
def root():
    result = {"status": "ok", "service": "Jtickets API v3.0", "docs": "/docs"}
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
            pending = db.scalar(select(func.count()).select_from(OutboxJob).where(
                OutboxJob.status.in_(["pending", "processing"])
            ))
        return {**result, "db": "ok", "outbox_pending": pending}
    except Exception:
        logger.error("Health database check failed")
        return JSONResponse(status_code=503, content={**result, "status": "error", "db": "error", "outbox_pending": None})
