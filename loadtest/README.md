# Booking stress harness

Run from the repository root with Python 3.12 or 3.13. Uses `asyncio`, the standard
library, and the installed `httpx` (verified 0.28.1); no new dependencies.

## Local baseline

Start a dedicated API in one PowerShell terminal. Use a throwaway database so the
test does not mix with demo bookings:

```powershell
$env:DATABASE_URL = 'sqlite:///./loadtest_tmp.db'
python -m uvicorn app.main:app --port 8011
```

In a second terminal:

```powershell
python loadtest/stress.py --base-url http://127.0.0.1:8011 --stages 5,20 --label smoke
python loadtest/stress.py --base-url http://127.0.0.1:8011 --label baseline
# After applying an optimization and restarting the API:
python loadtest/stress.py --base-url http://127.0.0.1:8011 --label optimized
```

SQLite does not implement the booking route's row locks. Inventory mismatches on
SQLite are correctness findings, not proof of PostgreSQL behavior. For a meaningful
locking/concurrency baseline, start the repository's PostgreSQL service and run the
API against it:

```powershell
docker compose up -d db
$env:DATABASE_URL = 'postgresql://jtickets:jtickets_dev@localhost:5432/eventbooking'
python -m uvicorn app.main:app --port 8011
```

Then use the same harness commands in the second terminal. The Docker credentials
above are the repository's local development defaults. In Bash, the equivalent is:

```bash
DATABASE_URL=postgresql://jtickets:jtickets_dev@localhost:5432/eventbooking python -m uvicorn app.main:app --port 8011
```

## Deployed baseline

These commands write real test accounts, published events, bookings, and
notifications to the target. Run against an API you control. The harness does not
delete this data; event IDs are saved in results for later cleanup.

```powershell
python loadtest/stress.py --base-url https://event-booking-nnr7.onrender.com --label baseline
# After deploying the optimization:
python loadtest/stress.py --base-url https://event-booking-nnr7.onrender.com --label optimized
```

The repo's [deployment notes](../AGENTS.md) report roughly 30-50 seconds of Render
free-tier cold-start delay. This is a project observation, not a timing guarantee.
The script automatically warms up with `GET /` using at least a 120-second timeout.
Warm-up, authentication, event creation, and seed bookings are outside measurement.

Accounts and tokens are cached per base URL in `loadtest/.users.json`. Before
committing, exclude this file (and any alternate users files) from version control;
it contains generated passwords and bearer tokens. The harness never prints them or
includes them in result files. Cached tokens are validated using `GET /users/me`;
expired/invalid tokens trigger login. A missing account triggers signup then login.
Use `--users-file loadtest/.smoke-users.json` for a separate cache. A database reset
can invalidate cached accounts; they will be recreated. Avoid simultaneous harness
processes sharing a cache. The harness bypasses environment HTTP proxies so proxy
limits do not silently become the measured limit.

## Scenarios and options

```powershell
python loadtest/stress.py --scenario update --stages 10,25,50 --label baseline
python loadtest/stress.py --scenario mixed --label baseline
python loadtest/stress.py --tickets 7 --stages 5,20 --label oversell
python loadtest/stress.py --timeout 15 --error-threshold 0.01 --p95-threshold-ms 2000 --setup-concurrency 5 --stop-on-break
```

| Option | Default | Meaning |
|---|---|---|
| `--base-url` | `http://127.0.0.1:8000` | Target API, without `/docs` |
| `--scenario` | `booking` | `booking`, `update`, or `mixed` |
| `--stages` | `10,25,50,100,200,300,500` | Strictly increasing concurrency levels |
| `--tickets` | `100000` | Capacity of the new event; small values exercise sell-out |
| `--timeout` | `10` | Overall deadline seconds per measured request |
| `--label` | `baseline` | Result name; letters, digits, `_`, `-` |
| `--users-file` | `loadtest/.users.json` | Private account cache; resolved relative to cwd if supplied |
| `--setup-concurrency` | `10` | Maximum concurrent account setup operations |
| `--error-threshold` | `0.01` | Dropped/sent breaking threshold |
| `--p95-threshold-ms` | `2000` | p95 breaking threshold |
| `--stop-on-break` | off | Stop after first failing stage |
| `--compare` | off | Two result JSON paths; skip all network activity |

`booking`: at stage C, C distinct cached customers each send one quantity-one
booking for the same event. Customers are reused across stages. Each run creates a
fresh published, untiered event with price 100 paise. No publish step is needed.

`update`: before measurement, book once for each of up to 10 distinct customers
(bounded by capacity and largest stage). Every stage then sends C concurrent
organizer `PUT` updates to the same event with unique descriptions. The fixed seed
count is saved as `seed_bookings`; compare runs with the same count. This measures
response throughput while background notification tasks run, not notification
delivery completion or successful email delivery.

`mixed`: approximately 80% bookings, 10% event detail GETs, 10% event list GETs.
Booking and detail counts round to nearest integers; remaining requests are lists.
Use multiples of ten for the exact ratio. Each booking uses a distinct customer.

Every stage uses one `httpx.AsyncClient` with C connection and keep-alive slots.
All workers reach an `asyncio.Event` barrier before release. Connections are cold
at every stage; DNS/TCP/TLS time is included. There is a two-second pause before the
first stage and between stages. There are no measured request retries. An asyncio
deadline caps the whole request; HTTPX also applies the same timeout to each phase
(connect/read/write/pool). A single bad response or transport failure does not stop
a stage.

## Metrics and interpretation

| Metric | Meaning |
|---|---|
| C / sent | Requested concurrency / requests started (partial on interruption) |
| 2xx | All successful responses; raw records retain exact codes |
| 409 | Business rejection such as sell-out; excluded from dropped |
| Other 4xx | Authentication, validation, rate-limit or other client failures |
| 5xx | Server failures |
| Timeout | Any HTTPX timeout; exact exception type retained |
| Conn | Non-timeout transport failures, including connect/read/write/protocol errors |
| Dropped | `5xx + timeouts + connection_errors` |
| Error % | `100 * dropped / sent` |
| p50/p95/p99/max | Latency milliseconds for all completed attempts, including HTTP errors and transport exceptions; nearest-rank percentiles |
| Wall s | Barrier release through final attempt completion |
| Req/s | All attempts / wall time, including failures; consult 2xx too |

Raw JSON retains each operation, status code, latency, and exception type/category.
It also records unexpected exceptions (`other_errors`), unusual HTTP statuses, and
cancelled attempts. Cancelled attempts are excluded from latency percentiles; a
partial stage never establishes a breaking point. Other 4xx and unexpected errors
are visible but excluded from the requested dropped formula. A run full of 401,
422, 429 or 409 responses is not evidence of useful booking capacity.

The **breaking point** is the first completed stage where error rate is strictly
greater than the configured threshold **or** p95 is strictly greater than its
threshold. Later stages continue unless `--stop-on-break` is set. If none breaks,
report "not observed within tested stages", not unlimited capacity. This is one
synchronized burst per stage, not a sustained-load capacity measurement. Repeat
runs to check variability; record API version, database, worker count, client
machine/network, deployment plan, and competing traffic alongside the results.
Keep these and all scenario settings consistent for baseline/optimized comparisons.

After each booking/mixed stage, an unmeasured GET checks that
`total_tickets - available_tickets == cumulative booking 201 responses` and
`available_tickets >= 0`. Violations print `OVERSOLD / INVENTORY INVARIANT VIOLATED`
and remain in results even when performance passes. A failed inventory GET is
reported as unknown rather than passing. A timed-out request may commit on the
server after the client gives up: mismatches need investigation and do not alone
prove overselling. This comparison cannot independently count booking rows or
detect hidden overselling combined with lost counter updates. Small capacity
tests and database inspection complement it. No timed-out booking is retried.

Background tasks can outlive HTTP responses and the two-second pause. Update
notification backlogs may therefore carry into later stages. This harness measures
client-visible responses, not durable background-task completion. It does not
implement or prove real booking email delivery.

## Results and comparison

Results are checkpointed after every stage under
`loadtest/results/<label>-<scenario>-<YYYYmmdd-HHMMSS>.json` and `.md`.
JSON contains run configuration, event ID, raw requests, metrics and inventory
checks; Markdown contains a pasteable table and breaking point. Files use local
time in names and UTC in `started_at`. Ctrl-C saves partial results; allow the
first interrupt to finish writing. Interrupted setup may leave test data behind.
Setup failure also writes a result with `status: failed`; do not treat it as a
completed benchmark. Exit codes are 0 completed, 1 failed, 130 interrupted.

```powershell
python loadtest/stress.py --compare loadtest/results/baseline-booking-20261018-120000.json loadtest/results/optimized-booking-20261018-130000.json
```

Pass baseline first, optimized second. Comparison joins concurrency levels and
prints 2xx, error percentage, p95, req/s, and both breaking points. Review inventory
and run status in both inputs before claiming an improvement. Times above are
filename examples; replace them with your generated paths.
