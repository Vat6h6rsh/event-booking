# optimized-render / booking

Target: https://event-booking-nnr7.onrender.com

Run status: complete

BREAKING POINT: concurrency 50 (p95 exceeds threshold).

| C | Sent | 2xx | 409 | Other 4xx | 5xx | Timeout | Conn | Dropped | Error % | p50 ms | p95 ms | p99 ms | Max ms | Wall s | Req/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 725.0 | 746.8 | 746.8 | 746.8 | 0.7 | 13.3 |
| 25 | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 1694.3 | 1844.5 | 1860.2 | 1860.2 | 1.9 | 13.3 |
| 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 2849.2 | 3564.2 | 3587.1 | 3587.1 | 3.7 | 13.7 |
| 100 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 4748.1 | 9558.4 | 9739.8 | 9794.3 | 10.0 | 10.0 |
| 150 | 150 | 132 | 0 | 0 | 0 | 18 | 0 | 18 | 12.0 | 6333.1 | 10020.7 | 10027.3 | 10028.9 | 10.3 | 14.6 |
| 200 | 200 | 76 | 0 | 0 | 0 | 124 | 0 | 124 | 62.0 | 10069.9 | 10293.8 | 10304.4 | 10306.9 | 10.7 | 18.7 |

Stage 10 inventory: `{"ok": true, "sold": 10, "available": 99990, "expected_201": 10}`

Stage 25 inventory: `{"ok": true, "sold": 35, "available": 99965, "expected_201": 35}`

Stage 50 inventory: `{"ok": true, "sold": 85, "available": 99915, "expected_201": 85}`

Stage 100 inventory: `{"ok": true, "sold": 185, "available": 99815, "expected_201": 185}`

Stage 150 inventory: `{"ok": false, "sold": 335, "available": 99665, "expected_201": 317}`

Stage 200 inventory: `{"ok": false, "sold": 434, "available": 99566, "expected_201": 393}`
