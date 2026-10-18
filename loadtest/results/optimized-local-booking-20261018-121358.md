# optimized-local / booking

Target: http://127.0.0.1:8011

Run status: complete

BREAKING POINT: concurrency 200 (p95 exceeds threshold).

| C | Sent | 2xx | 409 | Other 4xx | 5xx | Timeout | Conn | Dropped | Error % | p50 ms | p95 ms | p99 ms | Max ms | Wall s | Req/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 129.5 | 137.3 | 137.3 | 137.3 | 0.1 | 70.5 |
| 25 | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 352.4 | 396.8 | 400.9 | 400.9 | 0.4 | 58.4 |
| 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 750.1 | 867.6 | 879.2 | 879.2 | 0.9 | 54.1 |
| 100 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 1377.7 | 1719.4 | 1735.4 | 1736.4 | 1.9 | 52.0 |
| 200 | 200 | 200 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 2100.8 | 3340.3 | 3483.7 | 3501.1 | 3.9 | 51.6 |
| 300 | 300 | 300 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 3275.0 | 6544.0 | 6575.7 | 6586.7 | 7.1 | 42.0 |
| 500 | 500 | 489 | 0 | 0 | 0 | 11 | 0 | 11 | 2.2 | 8336.1 | 9887.5 | 10308.3 | 10354.7 | 10.8 | 46.3 |
| 750 | 750 | 750 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 8141.4 | 9776.0 | 9832.7 | 9851.8 | 10.1 | 74.5 |
| 1000 | 1000 | 292 | 0 | 0 | 0 | 708 | 0 | 708 | 70.8 | 13036.8 | 13706.5 | 13741.1 | 14279.5 | 15.3 | 65.6 |

Stage 10 inventory: `{"ok": true, "sold": 10, "available": 99990, "expected_201": 10}`

Stage 25 inventory: `{"ok": true, "sold": 35, "available": 99965, "expected_201": 35}`

Stage 50 inventory: `{"ok": true, "sold": 85, "available": 99915, "expected_201": 85}`

Stage 100 inventory: `{"ok": true, "sold": 185, "available": 99815, "expected_201": 185}`

Stage 200 inventory: `{"ok": true, "sold": 385, "available": 99615, "expected_201": 385}`

Stage 300 inventory: `{"ok": true, "sold": 685, "available": 99315, "expected_201": 685}`

Stage 500 inventory: `{"ok": false, "sold": 1185, "available": 98815, "expected_201": 1174}`

Stage 750 inventory: `{"ok": false, "sold": 1935, "available": 98065, "expected_201": 1924}`

Stage 1000 inventory: `{"ok": false, "sold": 2578, "available": 97422, "expected_201": 2216}`
