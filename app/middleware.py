"""Cheap event-loop admission control before booking work enters the threadpool."""
import asyncio
import os
from weakref import WeakKeyDictionary

from starlette.responses import JSONResponse

# Bookings currently admitted or queued. The outbox dispatcher reads this to defer
# background work (emails) while customers are waiting on the foreground path.
inflight = 0


class BookingAdmissionMiddleware:
    def __init__(self, app, max_inflight=None, queue_timeout=None):
        self.app = app
        self.max_inflight = max_inflight if max_inflight is not None else int(os.getenv("BOOKING_MAX_INFLIGHT", "50"))
        self.queue_timeout = queue_timeout if queue_timeout is not None else float(os.getenv("BOOKING_QUEUE_TIMEOUT", "8"))
        if self.max_inflight < 1 or self.queue_timeout <= 0:
            raise ValueError("Booking admission limits must be positive")
        # A deployed ASGI worker has one loop. Keeping loop-local semaphores also
        # supports TestClient's independent portals without cross-loop waiters.
        self._semaphores = WeakKeyDictionary()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"].rstrip("/") != "/bookings":
            return await self.app(scope, receive, send)
        global inflight
        loop = asyncio.get_running_loop()
        semaphore = self._semaphores.setdefault(loop, asyncio.Semaphore(self.max_inflight))
        inflight += 1
        try:
            try:
                await asyncio.wait_for(semaphore.acquire(), timeout=self.queue_timeout)
            except asyncio.TimeoutError:
                return await JSONResponse(
                    status_code=503, content={"detail": "High demand - please retry in a moment"},
                    headers={"Retry-After": "2"},
                )(scope, receive, send)
            try:
                await self.app(scope, receive, send)
            finally:
                semaphore.release()
        finally:
            inflight -= 1
