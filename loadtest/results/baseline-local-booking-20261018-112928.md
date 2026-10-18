# baseline-local / booking

Target: http://127.0.0.1:8011

Run status: failed

BREAKING POINT: concurrency 100 (error rate exceeds threshold, p95 exceeds threshold).

| C | Sent | 2xx | 409 | Other 4xx | 5xx | Timeout | Conn | Dropped | Error % | p50 ms | p95 ms | p99 ms | Max ms | Wall s | Req/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 108.3 | 182.5 | 182.5 | 182.5 | 0.2 | 52.2 |
| 25 | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 363.5 | 475.2 | 476.4 | 476.4 | 0.5 | 50.9 |
| 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 445.3 | 668.6 | 675.7 | 675.7 | 0.7 | 71.7 |
| 100 | 100 | 0 | 0 | 0 | 0 | 100 | 0 | 100 | 100.0 | 10007.7 | 10020.4 | 10021.9 | 10022.3 | 10.1 | 9.9 |
| 200 | 200 | 0 | 0 | 0 | 0 | 200 | 0 | 200 | 100.0 | 10009.6 | 10020.1 | 10023.5 | 10023.8 | 10.3 | 19.5 |
| 300 | 300 | 0 | 0 | 0 | 0 | 300 | 0 | 300 | 100.0 | 10084.9 | 10246.2 | 10254.2 | 10255.0 | 10.6 | 28.4 |
| 500 | 500 | 0 | 0 | 0 | 0 | 500 | 0 | 500 | 100.0 | 10018.8 | 10056.8 | 10058.5 | 10060.2 | 10.6 | 47.1 |
| 750 | 750 | 0 | 0 | 0 | 0 | 750 | 0 | 750 | 100.0 | 10012.1 | 10043.4 | 10044.6 | 10046.3 | 10.9 | 68.7 |
| 1000 | 1000 | 0 | 0 | 0 | 0 | 1000 | 0 | 1000 | 100.0 | 12440.7 | 12962.8 | 13119.1 | 13124.9 | 14.6 | 68.6 |

Stage 10 inventory: `{"ok": true, "sold": 10, "available": 99990, "expected_201": 10}`

Stage 25 inventory: `{"ok": true, "sold": 35, "available": 99965, "expected_201": 35}`

Stage 50 inventory: `{"ok": true, "sold": 85, "available": 99915, "expected_201": 85}`

Stage 100 inventory: `{"ok": false, "sold": 125, "available": 99875, "expected_201": 85}`

Stage 200 inventory: `{"ok": false, "sold": 159, "available": 99841, "expected_201": 85}`

Stage 300 inventory: `{"ok": null, "error_type": "ReadTimeout"}`

Stage 500 inventory: `{"ok": null, "error_type": "ReadTimeout"}`

Stage 750 inventory: `{"ok": null, "error_type": "ReadTimeout"}`

Stage 1000 inventory: `{"ok": null, "error_type": "ReadTimeout"}`

Run failed: ReadTimeout
