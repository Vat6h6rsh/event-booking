"""One synchronized burst per stage; no application imports or extra dependencies."""
import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import secrets
import sys
import time
import uuid

import httpx


ROOT = Path(__file__).resolve().parent


def say(message):
    print(str(message).encode("ascii", "backslashreplace").decode("ascii"), flush=True)


def headers(user):
    return {"Authorization": "Bearer " + user["token"]}


async def checked(client, method, path, **kwargs):
    response = await client.request(method, path, **kwargs)
    if not response.is_success:
        raise RuntimeError(f"Setup/check {method} {path}: HTTP {response.status_code}")
    return response.json()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    temporary.replace(path)


async def setup(client, args, runid):
    path = Path(args.users_file)
    cache = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    host = cache.setdefault(args.base_url, {"organizer": None, "customers": []})
    count = max(args.stages)

    def account(role, index):
        return {"email": f"lt_{runid}_{index}@loadtest.jtickets.dev",
                "password": secrets.token_urlsafe(24), "role": role, "token": None}

    if not host["organizer"]:
        host["organizer"] = account("organizer", "org")
    while len(host["customers"]) < count:
        host["customers"].append(account("customer", len(host["customers"])))
    save_json(path, cache)
    semaphore = asyncio.Semaphore(args.setup_concurrency)

    async def authenticate(user):
        async with semaphore:
            if user.get("token"):
                response = await client.get("/users/me", headers=headers(user))
                if response.status_code == 200:
                    if response.json().get("role") != user["role"]:
                        raise RuntimeError("Cached account has wrong role")
                    return
                if response.status_code != 401:
                    raise RuntimeError(f"Token validation: HTTP {response.status_code}")
            # Try login first: cached accounts survive expired tokens and interrupted setup.
            response = await client.post("/login", data={"username": user["email"],
                                                         "password": user["password"]})
            if response.status_code == 401:
                await checked(client, "POST", "/signup", json={
                    "email": user["email"], "password": user["password"],
                    "role": user["role"], "full_name": "Load Test"})
                response = await client.post("/login", data={"username": user["email"],
                                                             "password": user["password"]})
            if response.status_code != 200:
                raise RuntimeError(f"Login: HTTP {response.status_code}")
            user["token"] = response.json()["access_token"]
            save_json(path, cache)

    jobs = [asyncio.create_task(authenticate(u)) for u in
            [host["organizer"], *host["customers"][:count]]]
    try:
        await asyncio.gather(*jobs)
    finally:
        for job in jobs:
            if not job.done():
                job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
        save_json(path, cache)
    event = await checked(client, "POST", "/events", headers=headers(host["organizer"]), json={
        "name": f"LOADTEST {args.label} {runid}", "venue": "Load test - no admission",
        "event_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "total_tickets": args.tickets, "price": 100, "status": "published", "age_rating": "U"})
    seeded = 0
    if args.scenario == "update":
        # Fixed fan-out for every measured stage, bounded by capacity.
        for user in host["customers"][:min(10, args.tickets, count)]:
            await checked(client, "POST", "/bookings", headers=headers(user),
                          json={"event_id": event["id"], "quantity": 1})
            seeded += 1
    return host, event, seeded


def percentile(values, percent):
    if not values:
        return None
    # Nearest rank; includes unsuccessful responses and transport failures.
    return sorted(values)[max(0, math.ceil(len(values) * percent / 100) - 1)]


def summarize(stage, records, wall, interrupted):
    codes = [r["status"] for r in records]
    errors = [r["exception_category"] for r in records]
    result = {"concurrency": stage, "sent": len(records),
              "2xx": sum(s is not None and 200 <= s < 300 for s in codes),
              "409": codes.count(409),
              "4xx_other": sum(s is not None and 400 <= s < 500 and s != 409 for s in codes),
              "5xx": sum(s is not None and 500 <= s < 600 for s in codes),
              "timeouts": errors.count("timeout"), "connection_errors": errors.count("connection"),
              "other_errors": errors.count("other"), "cancelled": errors.count("cancelled"),
              "other_http": sum(s is not None and not 200 <= s < 600 for s in codes),
              "wall_seconds": wall, "throughput_rps": len(records) / wall if wall else 0,
              "interrupted": interrupted, "requests": sorted(records, key=lambda r: r["index"])}
    result["dropped"] = result["5xx"] + result["timeouts"] + result["connection_errors"]
    result["error_rate"] = result["dropped"] / len(records) if records else 0
    latencies = [r["latency_ms"] for r in records if r["exception_category"] != "cancelled"]
    for p in (50, 95, 99):
        result[f"p{p}_ms"] = percentile(latencies, p)
    result["max_ms"] = max(latencies, default=None)
    return result


async def burst(client, args, users, organizer, event_id, concurrency, records):
    gate, ready = asyncio.Event(), asyncio.Event()
    ready_count = 0

    async def worker(index):
        nonlocal ready_count
        operation = "booking"
        if args.scenario == "update":
            operation = "update"
        elif args.scenario == "mixed":
            # Round to closest integer counts for stages not divisible by ten.
            bookings = int(concurrency * .8 + .5)
            details = int(concurrency * .1 + .5)
            operation = "booking" if index < bookings else (
                "detail" if index < bookings + details else "list")
        method, path, kwargs = "POST", "/bookings", {
            "headers": headers(users[index]), "json": {"event_id": event_id, "quantity": 1}}
        if operation == "update":
            method, path, kwargs = "PUT", f"/events/{event_id}", {
                "headers": headers(organizer), "json": {"description": f"Stage {concurrency} update {index}"}}
        elif operation in ("detail", "list"):
            method, path, kwargs = "GET", f"/events/{event_id}" if operation == "detail" else "/events", {}
        ready_count += 1
        if ready_count == concurrency:
            ready.set()
        await gate.wait()
        start = time.perf_counter()
        record = {"index": index, "operation": operation, "status": None,
                  "exception_type": None, "exception_category": None}
        try:
            async with asyncio.timeout(args.timeout):
                response = await client.request(method, path, **kwargs)
            record["status"] = response.status_code
        except asyncio.CancelledError:
            record.update(exception_type="CancelledError", exception_category="cancelled")
            raise
        except Exception as exc:
            category = "other"
            if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
                category = "timeout"
            elif isinstance(exc, httpx.TransportError):
                category = "connection"
            record.update(exception_type=type(exc).__name__, exception_category=category)
        finally:
            record["latency_ms"] = (time.perf_counter() - start) * 1000
            records.append(record)

    jobs = [asyncio.create_task(worker(i)) for i in range(concurrency)]
    start = None
    try:
        await ready.wait()
        start = time.perf_counter()
        gate.set()
        await asyncio.gather(*jobs)
    finally:
        for job in jobs:
            if not job.done():
                job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
    return time.perf_counter() - start


def fmt(value):
    return "-" if value is None else f"{value:.1f}"


def table(stages):
    lines = ["| C | Sent | 2xx | 409 | Other 4xx | 5xx | Timeout | Conn | Dropped | Error % | p50 ms | p95 ms | p99 ms | Max ms | Wall s | Req/s |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in stages:
        cells = [s[k] for k in ("concurrency", "sent", "2xx", "409", "4xx_other", "5xx", "timeouts", "connection_errors", "dropped")]
        cells += [fmt(s["error_rate"] * 100)]
        cells += [fmt(s[k]) for k in ("p50_ms", "p95_ms", "p99_ms", "max_ms", "wall_seconds", "throughput_rps")]
        lines.append("| " + " | ".join(map(str, cells)) + " |")
    return "\n".join(lines)


def breaking_text(run):
    if run["breaking_point"]:
        return f"BREAKING POINT: concurrency {run['breaking_point']['concurrency']} ({', '.join(run['breaking_point']['reasons'])})."
    return "Breaking point not observed in completed stages; this is not a capacity guarantee."


def persist(run, output):
    save_json(output.with_suffix(".json"), run)
    notes = [f"# {run['config']['label']} / {run['config']['scenario']}",
             f"Target: {run['config']['base_url']}", f"Run status: {run['status']}",
             breaking_text(run), table(run["stages"])]
    for s in run["stages"]:
        if "inventory" in s:
            notes.append(f"Stage {s['concurrency']} inventory: `{json.dumps(s['inventory'])}`")
    if run.get("error"):
        notes.append(run["error"])
    output.with_suffix(".md").write_text("\n\n".join(notes) + "\n", encoding="utf-8")


async def execute(args, run, output):
    try:
        # Warm-up and setup use a separate generous timeout, never measured.
        async with httpx.AsyncClient(base_url=args.base_url, timeout=max(120, args.timeout),
                                     limits=httpx.Limits(max_connections=args.setup_concurrency),
                                     trust_env=False) as client:
            say("Warming up GET / (timeout >= 120s); setup is not measured.")
            await checked(client, "GET", "/")
            host, event, seeded = await setup(client, args, uuid.uuid4().hex[:12])
            run.update(event_id=event["id"], seed_bookings=seeded)
            cumulative = seeded
            say(f"Setup ready: event {event['id']}, {max(args.stages)} customers, {seeded} seed bookings.")
            await asyncio.sleep(2)
            for concurrency in args.stages:
                records, interrupted = [], False
                start = time.perf_counter()
                try:
                    async with httpx.AsyncClient(base_url=args.base_url, timeout=args.timeout,
                                                 limits=httpx.Limits(max_connections=concurrency,
                                                                    max_keepalive_connections=concurrency),
                                                 trust_env=False) as measured:
                        wall = await burst(measured, args, host["customers"], host["organizer"],
                                           event["id"], concurrency, records)
                except asyncio.CancelledError:
                    interrupted, wall = True, time.perf_counter() - start
                s = summarize(concurrency, records, wall, interrupted)
                run["stages"].append(s)
                cumulative += sum(r["operation"] == "booking" and r["status"] == 201 for r in records)
                reasons = []
                if not interrupted:
                    if s["error_rate"] > args.error_threshold:
                        reasons.append("error rate exceeds threshold")
                    if s["p95_ms"] is not None and s["p95_ms"] > args.p95_threshold_ms:
                        reasons.append("p95 exceeds threshold")
                    if reasons and run["breaking_point"] is None:
                        run["breaking_point"] = {"concurrency": concurrency, "reasons": reasons}
                        say(breaking_text(run))
                say(table([s]))
                # Save before checks so failures/interrupts cannot lose a measured stage.
                persist(run, output)
                if interrupted:
                    raise asyncio.CancelledError
                if args.scenario in ("booking", "mixed"):
                    try:
                        current = await checked(client, "GET", f"/events/{event['id']}")
                        sold = current["total_tickets"] - current["available_tickets"]
                        ok = sold == cumulative and current["available_tickets"] >= 0
                        s["inventory"] = {"ok": ok, "sold": sold, "available": current["available_tickets"],
                                          "expected_201": cumulative}
                        say(f"Inventory: {s['inventory']}" if ok else
                            f"OVERSOLD / INVENTORY INVARIANT VIOLATED: {s['inventory']} (timeouts may still commit)")
                    except Exception as exc:
                        s["inventory"] = {"ok": None, "error_type": type(exc).__name__}
                        say("INVENTORY CHECK FAILED: " + type(exc).__name__)
                persist(run, output)
                if args.stop_on_break and run["breaking_point"]:
                    break
                await asyncio.sleep(2)
            if not args.keep_event:
                # Unpublish so the load-test event never shows in the public listing.
                r = await client.put(f"/events/{event['id']}", headers=headers(host["organizer"]),
                                     json={"status": "draft"})
                say(f"Load-test event {event['id']} unpublished (HTTP {r.status_code}).")
        run["status"] = "complete"
    except asyncio.CancelledError:
        run["status"] = "interrupted"
        say("Interrupted; saving partial results. In-flight bookings may still commit.")
    except Exception as exc:
        run["status"] = "failed"
        # Do not serialize exceptions containing credentials, headers, or response bodies.
        run["error"] = "Run failed: " + type(exc).__name__
        say(run["error"])
    finally:
        persist(run, output)
        say(breaking_text(run))
        say(f"Results: {output.with_suffix('.json')} and {output.with_suffix('.md')}")


def compare(paths):
    a, b = [json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]
    if a["config"]["scenario"] != b["config"]["scenario"]:
        raise ValueError("Compare matching scenarios")
    say("| C | Baseline 2xx | Optimized 2xx | Baseline error % | Optimized error % | Baseline p95 ms | Optimized p95 ms | Baseline req/s | Optimized req/s |")
    say("|---|---|---|---|---|---|---|---|---|")
    aa, bb = [{s["concurrency"]: s for s in r["stages"]} for r in (a, b)]
    for c in sorted(aa.keys() | bb.keys()):
        cells = [c]
        for key in ("2xx", "error_rate", "p95_ms", "throughput_rps"):
            for mapping in (aa, bb):
                value = mapping.get(c, {}).get(key)
                cells.append(fmt(value * 100 if key == "error_rate" and value is not None else value))
        say("| " + " | ".join(map(str, cells)) + " |")
    say("Baseline: " + breaking_text(a))
    say("Optimized: " + breaking_text(b))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--scenario", choices=("booking", "update", "mixed"), default="booking")
    parser.add_argument("--stages", default="10,25,50,100,200,300,500")
    parser.add_argument("--tickets", type=int, default=100000)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--users-file", default=str(ROOT / ".users.json"))
    parser.add_argument("--error-threshold", type=float, default=.01)
    parser.add_argument("--p95-threshold-ms", type=float, default=2000)
    parser.add_argument("--setup-concurrency", type=int, default=10)
    parser.add_argument("--stop-on-break", action="store_true")
    parser.add_argument("--keep-event", action="store_true", help="leave the load-test event published")
    parser.add_argument("--compare", nargs=2, metavar=("BASELINE", "OPTIMIZED"))
    args = parser.parse_args()
    if args.compare:
        compare(args.compare)
        return 0
    try:
        args.stages = [int(c) for c in args.stages.split(",")]
        if not args.stages or any(c <= 0 for c in args.stages) or args.stages != sorted(set(args.stages)):
            raise ValueError
    except ValueError:
        parser.error("--stages must be strictly increasing positive integers")
    if (args.tickets <= 0 or args.setup_concurrency <= 0 or args.timeout <= 0
            or args.p95_threshold_ms <= 0 or not 0 <= args.error_threshold <= 1
            or not all(math.isfinite(v) for v in (args.timeout, args.p95_threshold_ms, args.error_threshold))):
        parser.error("Use positive capacity/concurrency/timeouts and an error threshold in [0, 1]")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.label):
        parser.error("--label must contain only ASCII letters, digits, underscores or hyphens")
    args.base_url = args.base_url.rstrip("/")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = ROOT / "results" / f"{args.label}-{args.scenario}-{stamp}"
    if output.with_suffix(".json").exists():
        parser.error("Result name already exists; wait one second or change --label")
    config = {k: v for k, v in vars(args).items() if k not in ("compare", "users_file")}
    run = {"config": config, "started_at": datetime.now(timezone.utc).isoformat(),
           "status": "running", "breaking_point": None, "stages": []}
    asyncio.run(execute(args, run, output))
    return 1 if run["status"] == "failed" else (130 if run["status"] == "interrupted" else 0)


if __name__ == "__main__":
    sys.exit(main())
