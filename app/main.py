import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import Base, engine
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

Base.metadata.create_all(bind=engine)

app = FastAPI(
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
    version="2.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Origins are env-driven so the deployed frontend (Vercel) can be allowed without
# a code change. `CORS_ORIGINS` is a comma-separated list; localhost is the default.
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "ok", "service": "Jtickets API v2.0", "docs": "/docs"}
