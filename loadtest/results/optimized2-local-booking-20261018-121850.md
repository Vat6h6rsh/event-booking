# optimized2-local / booking

Target: http://127.0.0.1:8011

Run status: complete

BREAKING POINT: concurrency 300 (p95 exceeds threshold).

| C | Sent | 2xx | 409 | Other 4xx | 5xx | Timeout | Conn | Dropped | Error % | p50 ms | p95 ms | p99 ms | Max ms | Wall s | Req/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 66.6 | 73.3 | 73.3 | 73.3 | 0.1 | 134.8 |
| 25 | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 218.5 | 259.9 | 264.3 | 264.3 | 0.3 | 90.3 |
| 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 431.7 | 504.6 | 516.1 | 516.1 | 0.5 | 95.9 |
| 100 | 100 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 663.1 | 775.1 | 780.7 | 784.2 | 0.8 | 119.0 |
| 200 | 200 | 200 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 1121.8 | 1640.2 | 1686.5 | 1692.6 | 1.8 | 109.4 |
| 300 | 300 | 300 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 1485.1 | 2706.7 | 2837.4 | 2867.0 | 3.0 | 98.4 |
| 500 | 500 | 500 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 3336.2 | 7414.2 | 7445.7 | 7460.2 | 7.7 | 64.8 |
| 750 | 750 | 750 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 7642.0 | 9266.0 | 9369.5 | 9400.0 | 9.6 | 78.2 |
| 1000 | 1000 | 878 | 0 | 0 | 0 | 122 | 0 | 122 | 12.2 | 9815.7 | 11633.2 | 11868.0 | 11899.8 | 12.2 | 82.0 |

Stage 10 inventory: `{"ok": true, "sold": 10, "available": 99990, "expected_201": 10}`

Stage 25 inventory: `{"ok": true, "sold": 35, "available": 99965, "expected_201": 35}`

Stage 50 inventory: `{"ok": true, "sold": 85, "available": 99915, "expected_201": 85}`

Stage 100 inventory: `{"ok": true, "sold": 185, "available": 99815, "expected_201": 185}`

Stage 200 inventory: `{"ok": true, "sold": 385, "available": 99615, "expected_201": 385}`

Stage 300 inventory: `{"ok": true, "sold": 685, "available": 99315, "expected_201": 685}`

Stage 500 inventory: `{"ok": true, "sold": 1185, "available": 98815, "expected_201": 1185}`

Stage 750 inventory: `{"ok": true, "sold": 1935, "available": 98065, "expected_201": 1935}`

Stage 1000 inventory: `{"ok": false, "sold": 2935, "available": 97065, "expected_201": 2813}`
