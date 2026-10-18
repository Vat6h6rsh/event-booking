# JTickets - Event Booking System

JTickets is an India-focused event-booking app: organizers manage events and tiers, customers browse and book, and the API enforces
roles and ownership. FastAPI, SQLAlchemy and PostgreSQL provide the backend, SQLite supports local development, and a React frontend
uses the same API. Bookings confirm immediately, prices are integer paise, and a database-backed outbox delivers real confirmation
email and event-update alerts outside the booking transaction.

- Frontend: [event-booking-nine-blue.vercel.app](https://event-booking-nine-blue.vercel.app)
- API: [event-booking-nnr7.onrender.com](https://event-booking-nnr7.onrender.com)
- Interactive reference: [Swagger](https://event-booking-nnr7.onrender.com/docs)
- Demo organizer: `admin@jtickets.com` / `jtickets2026` (public demo credentials).
- Create a separate customer account to book; organizers cannot book as customers.

The measured local improvement is **50 -> 200 simultaneous customers** within the chosen latency/error targets. The final run completed
every request through a **750-customer burst**, with higher latency at larger stages. These are local single-process measurements, not
a claim about deployed capacity.

## Requirement map

| Take-home requirement | Implementation | Evidence |
|---|---|---|
| Two roles and role-controlled APIs | [auth.py](app/auth.py), router dependencies | [RBAC tests](tests/test_rbac.py) |
| Organizers manage; customers browse/book | [events.py](app/routers/events.py), [bookings.py](app/routers/bookings.py) | [Booking tests](tests/test_booking.py), Swagger |
| Task 1: real confirmation email | Transactional outbox -> handler -> Brevo HTTP | [email.py](app/email.py), [transport tests](tests/test_outbox.py); mailbox verification below |
| Task 2: notify booked customers on update | Distinct confirmed bookers -> durable jobs -> email and in-app alert | [outbox.py](app/outbox.py), [recipient tests](tests/test_outbox.py) |
| Find and improve simultaneous-booking limit | Same-event synchronized bursts, baseline and two optimized runs | [Baseline](loadtest/results/baseline-local-booking-20261018-112928.md), [final](loadtest/results/optimized2-local-booking-20261018-121850.md) |
| Deploy and demonstrate | Render API/PostgreSQL, Vercel frontend | Live links above; deployed performance placeholder below |

## Quick start

Use Python 3.12 (the deployment pin), Node/npm, and optionally Docker for PostgreSQL. Run commands from the repository root unless a
directory change is shown.

```powershell
# Backend (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py
python -m uvicorn app.main:app --reload
```

On macOS/Linux, activate with `source venv/bin/activate` instead. Open `http://127.0.0.1:8000/docs`. Default DB:
`sqlite:///./booking.db`. The seed creates the demo organizer and 50 events with tiers across India, including Bihar and Jharkhand. It
exits when the organizer already exists; it does not repair partially seeded data. Event images are compressed local static assets.

For PostgreSQL, start only the database service and supply a strong key:

```powershell
docker compose up -d db
$env:DATABASE_URL = 'postgresql://jtickets:jtickets_dev@localhost:5432/eventbooking'
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(48))")
python seed.py
python -m uvicorn app.main:app --reload
```

Compose DB credentials are local defaults. Its API service's example key is shorter than the current minimum; use the commands above or
supply a strong key to that service. Use separate credentials in production.

```powershell
# Frontend, another terminal
cd frontend
npm install
npm run dev
# Compilation check:
npm run build
```

Open `http://localhost:5173`; Vite proxies `/api` to `http://127.0.0.1:8000`. For another API host, set `VITE_API_URL` before building.
React 18 uses CSS Modules and page state in [AppContext.jsx](frontend/src/context/AppContext.jsx), without react-router. The
notification bell polls every 15 seconds.

```powershell
# Tests: terminal without an external DATABASE_URL
python -m pytest -q --tb=short -p no:cacheprovider
# Stress: against an isolated running API you control (setup below)
python loadtest/stress.py --base-url http://127.0.0.1:8011 --stages 10,25,50,100,200,300,500,750,1000 --timeout 10 --label optimized
```

Tests default to disposable SQLite. External test DB names must contain `test`; fixtures clear their tables. Stress runs create and
retain accounts/events/bookings.

## Architecture and storage

```text
React / Swagger / stress client
              |
              v
FastAPI: CORS -> booking admission middleware -> auth/RBAC -> routers
                                                              |
                                                        one transaction
                                                              v
                                              PostgreSQL (SQLite in dev)
                                              events / tiers / bookings
                                              attendees / idempotency_keys
                                              outbox_jobs / notifications
                                                         ^
                                                         | claim / ack / retry
                                          lifespan dispatcher thread
                                                |                |
                                          Brevo HTTPS      in-app notification
                                                                 |
                                                    GET /notifications -> bell
```

One API process keeps deployment simple. Sync SQLAlchemy routes run in the AnyIO threadpool; admission waits in the event loop before
DB/auth work uses a thread. PostgreSQL is the production inventory authority. SQLite supports the same conditional inventory algorithm
but serializes writers. SQLAlchemy supplies transactions/portable statements; Pydantic validates bounds and serializes responses.

Main relationships: `User -> Event -> TicketTier` for organizers and `User -> Booking -> BookingAttendee` for customers. A booking
references an event and optionally a tier. `IdempotencyKey` references its user and resulting booking; unique `Notification.job_id`
identifies an outbox delivery's in-app record. Venues, support tickets/messages and optional R2 uploads are supporting features. See
[models.py](app/models.py) and [schemas.py](app/schemas.py) for the data contract. Money uses integer paise: `10000` means INR 100.00.
Server prices determine the stored booking total; later price edits do not recalculate that total.

## Roles, authentication and API access

Public event lists return published events with `skip >= 0` and `limit` 1-100 (default
100), ordered by date/id. Filters include category, age rating, city and `q` for name
matching; tiers are eagerly loaded. Targeted indexes cover event status/date and category,
booking event/status and user/created time, attendee booking ID, notification user/read
state, and outbox status/next-attempt time. They support those access paths without
claiming that substring search is fully indexed or that every list is paginated.

`POST /login` accepts form fields `username` (email) and `password`, returning an HS256 JWT valid for 24 hours. Passwords use bcrypt.
Send `Authorization: Bearer <token>`; in Swagger, paste it into **Authorize**. Authentication loads the current DB user;
`require_role(role)` checks that user's role. Missing/invalid tokens return 401, wrong roles 403. Ownership is checked separately from
role membership.

| Method | Route | Access / ownership |
|---|---|---|
| POST | `/signup`, `/login` | Public; signup chooses `organizer` or `customer` |
| GET, PUT | `/users/me` | Authenticated, current user |
| GET | `/events`, `/events/{id}`, `/events/{id}/tiers`, `/events/{id}/seats` | Public |
| GET | `/events/mine` | Organizer's own events |
| POST | `/events` | Organizer |
| PUT, DELETE | `/events/{id}` | Organizer owner; actual PUT changes trigger Task 2 |
| POST, PUT, DELETE | `/events/{id}/tiers[/{tier_id}]` | Organizer owning parent event |
| POST | `/bookings` | Customer; triggers Task 1 |
| GET | `/bookings`, `/bookings/{id}` | Customer's own bookings |
| DELETE | `/bookings/{id}` | Customer owner; cancels/restores stock |
| GET | `/notifications` | Authenticated, own records |
| POST | `/notifications/{id}/read`, `/notifications/read-all` | Authenticated, own records |
| GET | `/venues`, `/venues/{id}` | Public; `/venues/mine` requires organizer |
| POST, PUT, DELETE | `/venues[/{id}]` | Organizer; existing venue writes require owner |
| GET, POST, PUT | `/support/tickets[...]`, messages | Authenticated; owner or organizer for individual ticket access |
| POST | `/upload/image` | Authenticated; optional Cloudflare R2 |
| GET | `/legal/terms`, `/legal/privacy`, `/`, `/docs` | Public |

An organizer cannot edit another organizer's event; customers cannot read another's booking. Support currently treats every organizer
as staff, a known limitation below. Errors retain `{"detail": ...}` for frontend compatibility. Unexpected errors are logged and return
generic 500 JSON without exposing a traceback to the caller.

## Booking flow and inventory design

### One atomic purchase

1. Authenticate; validate quantity, attendees and the optional idempotency key.
2. Reserve the key when supplied, or replay a completed matching purchase.
3. Read event/tier; validate publication, tier membership and age eligibility.
4. Prepare the confirmed booking, bulk attendees/ticket codes and confirmation
   outbox job; attach the booking to its key, all in one transaction.
5. Claim event inventory, then optional tier inventory, using conditional SQL.
6. Use the claimed row's price, build the response without lazy reads, commit and
   wake the dispatcher. Failed claims roll back every prepared write.

The core claim in [bookings.py](app/routers/bookings.py) is equivalent to:

```sql
UPDATE events
SET available_tickets = available_tickets - :quantity
WHERE id = :event_id AND status = 'published'
  AND available_tickets >= :quantity
RETURNING available_tickets;
```

No returned row means no purchase: missing event is 404; closed/insufficient stock is 409. Predicate and decrement run together.
PostgreSQL still locks the row until commit: atomic SQL shortens the critical section rather than removing serialization. Preparing
inserts first leaves only final updates/commit under the hot event lock in the common path. A concurrent price edit can require another
booking-total update.

### Shared event/tier capacity and cancellation

- `0 <= event.available_tickets <= event.total_tickets`.
- `0 <= tier.available_seats <= tier.total_seats`.
- A tier sale consumes **both** pools; an untiered sale consumes event capacity.
- Sum of tier allocations cannot exceed event capacity; tiers are not extra stock.
- Inventory writers touch event before tier. Capacity editors serialize on the
  parent before checking allocations. Failed tier claims roll back the event claim.
- Capacity edits adjust remaining stock by the delta and cannot go below sales.
  Events/tiers with any booking history cannot be deleted (409).

The original SQLite smoke test returned 25 confirmations but deducted only four tickets: `FOR UPDATE` did not protect the
read-modify-write, and updates were lost. Conditional SQL removes that dependency; race tests now run on both engines.

Cancellation uses a guarded `confirmed -> cancelled` update with `RETURNING`, sets `cancelled_at`, and restores event/optional tier
stock in the same transaction. Only the request changing status restores stock, preventing double restoration. Cancellation after event
start, duplicate cancellation or invalid restoration is 409.

Quantity is 1-10; attendees must be empty/omitted or exactly match quantity. For `A`/`18+` events, every attendee must supply an age
>=18. Event/tier schemas bound prices/capacity, reject forbidden nulls, constrain statuses and validate dates. Booking totals above
2,147,483,647 paise return 422 to fit PostgreSQL Integer. Seat labels are free text, not exclusive reservations. There is no payment or
hold state: successful bookings are immediately confirmed.

### Idempotent retries

Reuse one `Idempotency-Key` for an intended purchase after an uncertain response:

```http
POST /bookings
Authorization: Bearer <customer-token>
Idempotency-Key: <one-client-generated-uuid>
Content-Type: application/json

{"event_id": 1, "quantity": 1, "attendees": []}
```

| Condition | Result |
|---|---|
| New key and valid purchase | 201; key, purchase, inventory and job commit together |
| Same user/key and canonical body, completed booking | 200 + `Idempotent-Replayed: true`; no new deduction/job |
| Key reused with changed body | 422 |
| Existing unresolved key | 409, request already in progress |
| Key older than 24 hours | Expired record removed on reuse; a new purchase is possible |

Keys are optional for compatibility, 1-80 characters and unique per user. SHA-256 of canonical validated JSON detects changed requests.
A SAVEPOINT handles unique collisions without invalidating the outer transaction. SQLite explicitly begins that transaction so
releasing a SAVEPOINT cannot commit a key independently. Replay returns the existing booking model, not a stored byte-for-byte
response. The frontend retains an intent key for retries and accepts 201/200; a new intended purchase needs a new key. Retrying without
one can still double-buy.

## Background tasks and real email

### Durable intent and bounded delivery

[Outbox producers](app/outbox.py) write jobs with the business change. This closes the original commit-to-scheduling crash window of
per-request FastAPI `BackgroundTasks`. A lifespan-managed daemon thread processes the durable DB queue. `kick()` wakes it after commit;
it also polls every five seconds. Each drain handles up to 20 jobs, claiming **one at a time**: PostgreSQL uses `FOR UPDATE SKIP
LOCKED`, SQLite a guarded status update. Queue claiming is separate from stock claiming; locked stock is not skipped. Handlers use
their own sessions, persist the alert and release the connection before network email. Provider calls never hold inventory locks.

Jobs move `pending -> processing -> done`, or retry and eventually become `failed`. Five failed attempts exhaust delivery, with
10/20/40/80-second retry delays. Processing jobs older than two minutes recover after a crash. Unique `job_id` and conflict-ignore
insertion prevent duplicate in-app alerts. Email is **at-least-once**: a crash after provider acceptance but before acknowledgement can
duplicate email. Failed jobs remain inspectable; no operator redrive UI exists. Error persistence is sanitized; credentials and raw
provider response bodies are not saved in jobs.

While admitted or queued bookings exist, each drain defers up to `OUTBOX_MAX_DEFER_SECONDS` (default 20), prioritizing foreground CPU
without indefinite starvation. This is a per-drain cap, not an email latency guarantee. Without lifespan, `kick()` drains synchronously
after commit for deterministic tests.

### The two tasks

**Task 1:** one confirmation job per new booking. [tasks.py](app/tasks.py) and [EmailNotifier](app/notifications.py) load
booking/user/event/tier/tickets and send escaped HTML and plain text: event, IST date/time, venue, tier, quantity, INR total, booking
ID and ticket codes. An in-app confirmation is also saved. Event metadata is loaded at delivery time; the total is stored, but full
immutable event quotes are future work.

**Task 2:** actual event changes insert jobs with one `INSERT ... SELECT DISTINCT user_id` over confirmed bookings, inside the update
transaction. Duplicate bookings yield one recipient per update; cancelled-only bookers and bystanders are excluded. Eligibility is
determined by that producer query. No-op updates enqueue nothing. The summary snapshots changed field names and the new IST date/venue.
Each recipient gets email and an in-app alert; one failed recipient does not discard other jobs.

### Email configuration and evidence

`EMAIL_PROVIDER=brevo` calls `https://api.brevo.com/v3/smtp/email` over HTTPS with a 10-second transport timeout. Use a verified
`EMAIL_FROM`, a restricted transactional-email API key, and Brevo's authorized-IP allowlist with Render outbound IPs. These are
deployment settings, not committed values. See Brevo's [authentication](https://developers.brevo.com/docs/api-key-authentication) and
[IP security](https://developers.brevo.com/docs/ip-security) documentation. HTTP was chosen because Render free web services block SMTP
ports 25/465/587. [Render free-service limits](https://render.com/docs/free)

SMTP with certificate-verified STARTTLS remains available locally. Default `console` does **not** satisfy real email delivery.
`loadtest.jtickets.dev` and `example.com` recipients are suppressed by default, separating burst tests from provider/inbox tests.
Verify the graded requirement with an unsuppressed controlled mailbox: book, show the confirmation, update as organizer, then show
update email and the notification bell. A console marker, mock or provider acceptance alone does not prove inbox receipt. Automated
transports are mocked; mailbox evidence and credentials are not stored here.

The DB outbox avoids a broker on one small instance. Celery/Redis would add independent worker scaling and operational cost; atomic
delivery intent would still be needed. The current worker shares API CPU, and notification latency can rise during bursts.

## Performance: baseline, diagnosis and improvements

### Method and breaking-point definition

All three local runs used PostgreSQL 16 and one Uvicorn process. Each stage releases C distinct authenticated customers together, each
booking one ticket on the same published, untiered event with capacity 100,000: a hot-row worst case, not sold-out work. Stages:
10,25,50,100,200,300,500,750,1000. Setup/auth/warm-up are unmeasured; each stage uses fresh connections (setup latency included) and a
two-second inter-stage gap.

**Breaking point:** first completed stage with `error rate > 1%` **or** `p95 > 2 s`. Client timeout is 10 seconds. Errors are 5xx +
timeouts + connection errors; admission 503s count, business 409s/other 4xx are separate. Percentiles include failed attempts. There
are no measured retries. This is one synchronized burst per stage, not sustained traffic, repeated-run averages or a general number of
supported active users.

### Baseline: pool-starvation convoy

The original passed C=50 (p95 668.6 ms); all requests at C=100 and larger stages timed out. Its server log recorded **2,145 QueuePool
TimeoutErrors**, with pool size 5, overflow 10 and checkout timeout 30 seconds (operator log observation; committed tables record
client failures). The failure model is a pool-starvation convoy:

1. Auth/request sessions check out connections; same-event buyers wait on a row lock.
2. The pool has 15 maximum connections, while blocked sync requests occupy threads.
3. Post-commit `refresh()` opens a request transaction retaining a connection while
   its per-request background task asks for another connection.
4. Requests/tasks exhaust the pool and delay progress beyond the client deadline.

Timeout did not mean rollback: after stage 100, cumulative sales were 125 versus 85 successful responses, so 40 purchases committed
without client confirmation. This motivates durable idempotency independently of oversell protection. The baseline eventually failed
its own inventory read with ReadTimeout.

### Optimizations and measured effect

| Change | Reason / evidence boundary |
|---|---|
| Conditional claims near commit | Shortens hot-row lock time; fixes original SQLite lost updates |
| Bulk attendees; response built before commit; no refresh/lazy reads afterward | Less DB work; removes request/task second-connection cycle |
| Outbox with business writes, delivery outside request | Durable intent; provider latency removed from foreground |
| Pool 20 + 20, checkout timeout 10 s, pre-ping | Bounded larger pool and shorter checkout waits |
| Threadpool 60, admitted bookings 50, queue timeout 8 s | Coordinates sync work; cheap queueing and explicit overload |
| Eager tiers, event-list limit 100 and query indexes | Bounds browse work; no isolated index speedup claimed |
| Foreground-first outbox deferral, 20 s cap | Less API/worker CPU and GIL competition; run 2 adds this change |
| Production `--no-access-log` | Reduces logging CPU; no standalone gain attributed |

Run 1 combined v3 changes without deferral; first degradation moved to C=200 on latency. Deferral moved it to C=300: at C=200, p95 fell
**3340.3 -> 1640.2 ms** and rate rose **51.6 -> 109.4 req/s**. Other v3 changes were measured as a bundle, so independent numeric gains
cannot be assigned to each SQL/pool/validation change.

### Local comparison (2026-10-18)

Cells show **successful responses / sent; p95 milliseconds**.

| Concurrent customers | Original baseline | V3, no deferral | V3 + foreground first |
|---:|---:|---:|---:|
| 10 | 10/10; 182.5 | 10/10; 137.3 | 10/10; 73.3 |
| 25 | 25/25; 475.2 | 25/25; 396.8 | 25/25; 259.9 |
| 50 | 50/50; 668.6 | 50/50; 867.6 | 50/50; 504.6 |
| 100 | 0/100; 10020.4 | 100/100; 1719.4 | 100/100; 775.1 |
| 200 | 0/200; 10020.1 | 200/200; 3340.3 | 200/200; 1640.2 |
| 300 | 0/300; 10246.2 | 300/300; 6544.0 | 300/300; 2706.7 |
| 500 | 0/500; 10056.8 | 489/500; 9887.5 | 500/500; 7414.2 |
| 750 | 0/750; 10043.4 | 750/750; 9776.0 | 750/750; 9266.0 |
| 1000 | 0/1000; 12962.8 | 292/1000; 13706.5 | 878/1000; 11633.2 |

| Interpretation | Baseline | V3, no deferral | Final |
|---|---:|---:|---:|
| Largest stage meeting both targets | 50 | 100 | 200 |
| First degradation by either target | 100 | 200 | 300 |
| Largest stage with zero drops throughout preceding stages | 50 | 300 | 750 |
| C=100 error rate | 100% | 0% | 0% |
| C=1000 error rate | 100% | 70.8% | 12.2% |

Healthy-stage rates improved roughly **50-70 -> 100-130 req/s** (final C=100: 119.0, C=200: 109.4). This is not constant across sizes:
final C=500/750 achieved 64.8/78.2. The harness counts all attempts in req/s, including failures; timeout-stage rates are not goodput.
Run 1's successful C=750 does not erase its earlier C=500 drops.

Final inventory matched cumulative successful responses through C=750: 1,935 sold, 98,065 remaining. At C=1000, 122 clients timed out
but all 1,000 purchases committed: cumulative 2,935 sold versus 2,813 successful responses. This is late completion, not negative
stock. Reuse the same key to resolve an uncertain purchase. The operator also observed **1,435 deferred jobs drain to zero within about
20 s after the burst**; this background observation is not an inbox SLA or a field in the committed burst tables.

Evidence: [baseline](loadtest/results/baseline-local-booking-20261018-112928.md), [run
1](loadtest/results/optimized-local-booking-20261018-121358.md), [run 2](loadtest/results/optimized2-local-booking-20261018-121850.md),
[comparison](loadtest/results/compare-local.md). Adjacent JSON contains configuration and raw attempts. These three artifacts take
precedence over older intermediate notes.

### Deployed (Render free tier) results

**Pending measured deployment results; do not substitute local values here.** Render free compute has a shared fractional budget (0.1
CPU, 512 MB), so lower absolute capacity and CPU-bound behavior are expected; verify the deployed bottleneck. [Render compute
plans](https://render.com/docs/compute-plans) Warm the service and keep thresholds, client location, stages, workers and suppression
settings consistent for before/after runs.

<!-- DEPLOYED_RESULTS -->

| Version | Largest passing burst | First degrading stage | First dropped stage | p95 / error rate | Artifact |
|---|---|---|---|---|---|
| Deployed baseline | Pending | Pending | Pending | Pending | Pending |
| Deployed optimized | Pending | Pending | Pending | Pending | Pending |

### Reproduce

Use a disposable PostgreSQL DB and API on 8011, separate from demo data. Supply your own local URL (angle-bracket fields are
placeholders), then run the Quick start stress command in another terminal:

```powershell
$env:DATABASE_URL = 'postgresql://<local-user>:<local-password>@localhost:5432/jtickets_loadtest'
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(48))")
$env:EMAIL_PROVIDER = 'console'
$env:EMAIL_SUPPRESS_DOMAINS = 'loadtest.jtickets.dev,example.com'
python -m uvicorn app.main:app --host 127.0.0.1 --port 8011 --no-access-log
```

Set `OUTBOX_MAX_DEFER_SECONDS=0` before starting to measure current v3 without deferral; use 20 for the final policy. Recreating the
original baseline requires the original application version, not setting this knob to zero. Keep all other conditions constant.

```powershell
python loadtest/stress.py --compare loadtest/results/baseline-local-booking-20261018-112928.json loadtest/results/optimized2-local-booking-20261018-121850.json
python loadtest/stress.py --base-url http://127.0.0.1:8011 --scenario mixed --stages 10,25,50 --label mixed
python loadtest/stress.py --base-url http://127.0.0.1:8011 --scenario update --stages 10,25,50 --label update
```

See the [harness reference](loadtest/README.md); its SQLite row-lock warning describes the original baseline. Private
`loadtest/.users.json` contains credentials/tokens: never publish it. Results exclude credentials. Suppressed recipients mean burst
runs do not test mail delivery throughput. Update/mixed runners exist, but no limits for those scenarios are claimed. Repeat bursts and
add sustained arrival-rate tests before treating these observations as an operating capacity.

## What larger platforms do, and what we borrowed

These are documented patterns and our decisions, not inferred ticketing internals.

| Documented example | Applied / deliberately deferred |
|---|---|
| Stripe explains idempotent mutations after ambiguous network failures. [Stripe engineering](https://stripe.com/blog/idempotency) | Persist purchase keys/hashes; stock locks cannot deduplicate retries |
| Shopify describes DB reservation units and consistent lock ordering. [Shopify engineering](https://shopify.engineering/scaling-inventory-reservations) | One DB authority, event-before-tier ordering; defer unit pools/shards until contention warrants complexity |
| Cloudflare documents edge admission with Workers/Durable Objects. [Cloudflare engineering](https://blog.cloudflare.com/building-waiting-room-on-workers-and-durable-objects/) | Bound expensive work now; externalize waiting traffic when the origin cannot afford it |
| AWS documents atomic business/outbox writes and duplicate-aware consumers. [AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | Commit delivery intent; deduplicate alerts and allow possible duplicate email |

Payment checkout would need holds with ownership tokens, TTL, conditional confirmation and late-callback recovery. Without a slow
payment step, holds add lifecycle complexity without fixing today's bottleneck. A real waiting room needs signed tokens, bypass
protection and fairness rules; the semaphore is only process-local concurrency control. Stock buckets need allocation/rebalancing
invariants. Redis can support shared limits, admission and TTL/cache work across instances; it need not become a second stock
authority.

## Security, audit fixes and remaining gaps

The original source audit identified 30 findings; v3 did not close them all.

| Audit area | Implemented response |
|---|---|
| JWT fallback (BA-01) | PostgreSQL requires >=32-character secret; SQLite random process key |
| Inventory/cancellation/SQLite (BA-04/05/06) | Shared capacity, atomic claims, guarded cancel, both-engine races |
| Simulated/lossy delivery (BA-08/09) | Real transports, outbox/retry/recovery, unique alert IDs |
| Request cost (BA-10, partial) | Quantity/attendee bounds and admission; no per-account rate limiter |
| Test cleanup (BA-11) | Reject non-test external DB names before imports/cleanup |
| Performance evidence (BA-12, partial) | Local before/after reports; deployed results pending |
| Validation/lifecycle/history/references (BA-13-17, partial) | Event/tier bounds, date checks, cancel cutoff, age enforcement, history guards, owned event venues |
| Reads/indexes/contention (BA-18-20, partial) | Eager loading, bounded event lists, indexes, shorter transactions/admission |
| Retries/money (BA-21/23) | Persistent idempotency and Integer total bound |
| Schema/operations (BA-25/29, partial) | Additive upgrade, DB/outbox readiness; migrations/telemetry remain |

Remaining gaps: rotate/replace the public seed account; separate trusted support staff from self-registered organizers; enforce real
seat identities/uniqueness; restrict draft detail visibility and past-event booking. Upload validation/stream bounds, auth abuse
controls, other-list pagination, complete DB check/FK enforcement, policy accuracy and support workflow details need work. CORS covers
admission 503s; coverage of every unexpected error path is not claimed. No payment, bot defense or refund flow is claimed.

## Configuration

Local dotenv loading is supported. Keep credentials outside version control and restart after process-setting changes. These values are
defaults/descriptions, not secrets.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./booking.db` | PostgreSQL in production; normalizes `postgres://` |
| `SECRET_KEY` | Random process key on SQLite if short/unset | Required >=32 chars on PostgreSQL; use stable random secret |
| `CORS_ORIGINS` | Localhost/127.0.0.1:5173 always allowed | Comma-separated origins; `CORS_ORIGIN` fallback |
| `EMAIL_PROVIDER` | `console` | `brevo`, `smtp`, `console`; real deployed mail uses Brevo |
| `BREVO_API_KEY` | Unset | Restricted transactional-email key |
| `EMAIL_FROM` | Unset | Verified sender required for real transports |
| `EMAIL_FROM_NAME` | `JTickets` | Display name |
| `EMAIL_SUPPRESS_DOMAINS` | `loadtest.jtickets.dev,example.com` | Exact recipient domains skipped |
| `SMTP_HOST`, `SMTP_PORT` | `localhost`, `587` | Local SMTP with verified STARTTLS |
| `SMTP_USER`, `SMTP_PASSWORD` | Unset / empty | Optional SMTP authentication |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | `20`, `20` | PostgreSQL per-process pool; checkout timeout fixed 10 s |
| `THREADPOOL_SIZE` | `60` | AnyIO sync work tokens, set in lifespan |
| `BOOKING_MAX_INFLIGHT` | `50` | Admitted booking requests per loop/process |
| `BOOKING_QUEUE_TIMEOUT` | `8` seconds | Then 503 + `Retry-After: 2` |
| `OUTBOX_MAX_DEFER_SECONDS` | `20` | Max foreground-first delay before each drain |
| `VITE_API_URL` | `/api` | Frontend build-time API URL |

Optional upload `CF_*` settings are in [r2.py](app/r2.py); bookings/local images need none. Pool defaults are not permission to exceed
DB connection budgets. Multiple processes multiply pools and local admission limits; retune before scaling.

## Deployment and schema upgrades

### Render API and PostgreSQL

1. Create PostgreSQL and a native Python web service; set `DATABASE_URL` to the internal URL.
2. Keep [.python-version](.python-version) at **3.12** for the tested dependencies.
3. Build: `pip install -r requirements.txt`.
4. Set strong `SECRET_KEY`, Vercel `CORS_ORIGINS`, and Brevo sender/key settings;
   configure transactional-only key access and authorized Render outbound IPs.
5. Start one process; disabling access logs reduces CPU work:

```bash
python seed.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-access-log
```

At import, [ensure_schema()](app/database.py) creates missing tables, adds `bookings.cancelled_at`/`notifications.job_id` if absent,
creates the unique job index and ensures model indexes. This repeatable additive upgrade preserves rows, requiring no reset for these
additions. It is not a general migration/rollback or reconciliation framework. The DB user needs DDL permission. Back up/validate older
data: added columns do not repair historical capacity inconsistencies. Seed does not backfill existing installs.

`GET /` checks DB readiness and pending/processing outbox depth; DB failure is 503. Zero pending does not prove inbox delivery or
absence of failed jobs: inspect statuses, attempts and sanitized `last_error`. Idle shutdown can delay requests/background work until
the service resumes. [Render free-service behavior](https://render.com/docs/free)

### Vercel frontend

Root Directory: `frontend`; build: `npm run build`; output: `dist`. Set `VITE_API_URL=https://event-booking-nnr7.onrender.com` without
a trailing slash before building (use your own host for another install). Add the frontend origin to `CORS_ORIGINS`, redeploy and check
preflight/login. CORS exposes replay/retry headers. Smoke check: customer booking, same-key replay, organizer update, email/bell,
cancellation.

## Testing and review evidence

Recorded v3 verification on 2026-10-18: **60 passed** on temporary SQLite (122.21 s) and **60 passed** on PostgreSQL 16 (120.66 s),
including concurrency tests. These are implementation-session results; transport mocks are not live mailbox tests.

| Suite | Coverage |
|---|---|
| [RBAC](tests/test_rbac.py) | Missing token, wrong role, cross-owner edits |
| [Bookings](tests/test_booking.py) | Deduction, insufficient stock, cancel, age gate |
| [Concurrency](tests/test_concurrency.py) | Last-ticket/small-event races, duplicate keys/cancels, tier allocation |
| [Upgrade](tests/test_upgrade.py) | Replay/conflict/expiry/rollback, shared capacity, bounds/dates, no post-commit booking queries |
| [Outbox](tests/test_outbox.py) | Recipient dedupe, retries/recovery/claims, escaping, Brevo/SMTP requests/suppression |
| [Operations](tests/test_operations.py) | Admission/CORS/disconnect, lifespan, key guard, readiness, test-target safety |
| [Background tasks](tests/test_background_tasks.py) | Confirmation/update alerts, non-booker exclusion |

For PostgreSQL, create an empty disposable database whose name contains `test`:

```powershell
$env:DATABASE_URL = 'postgresql://<local-user>:<local-password>@localhost:5432/jtickets_test'
python -m pytest -q --tb=short -p no:cacheprovider
```

Fixtures clear mapped tables after each test. Root `smoke_test.py`/`api_smoke_test.py` need a live server and are excluded by
[pytest.ini](pytest.ini). For the required 3-4 minute demo, show deployed API calls, the baseline breaking point, optimization
mechanism, final limit and actual email/alert behavior. The brief requires English speech, face and screen, and a 2-5 minute recording.

## Trade-offs and next steps

1. Complete deployed before/after measurements and controlled mailbox evidence.
2. Separate support permissions, replace demo credentials, add auth/booking rate limits
   and upload bounds before broader public use.
3. Add Alembic, data reconciliation and DB constraints beyond the small additive upgrade.
4. Add exclusive seat ownership before selling assigned seats; add TTL holds/payments
   with conditional expiry/confirmation and late-callback recovery when checkout needs them.
5. Add failed-job redrive, provider delivery/bounce tracking, immutable purchase snapshots,
   retention cleanup and lock/pool/admission/queue-age metrics.
6. Measure sustained/distributed-event traffic before edge waiting rooms, shared Redis
   limits, independent workers or stock shards. More workers alone cannot remove hot-row contention.
