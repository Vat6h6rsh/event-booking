# baseline-render / booking

Target: https://event-booking-nnr7.onrender.com

Run status: complete

BREAKING POINT: concurrency 25 (p95 exceeds threshold).

| C | Sent | 2xx | 409 | Other 4xx | 5xx | Timeout | Conn | Dropped | Error % | p50 ms | p95 ms | p99 ms | Max ms | Wall s | Req/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 1150.6 | 1452.4 | 1452.4 | 1452.4 | 1.5 | 6.8 |
| 25 | 25 | 25 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 1890.4 | 2606.7 | 2619.3 | 2619.3 | 2.6 | 9.5 |
| 50 | 50 | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | 3228.5 | 4980.6 | 5128.5 | 5128.5 | 5.2 | 9.7 |
| 100 | 100 | 4 | 0 | 0 | 0 | 96 | 0 | 96 | 96.0 | 10008.0 | 10033.2 | 10035.4 | 10049.3 | 10.2 | 9.8 |
| 150 | 150 | 11 | 0 | 0 | 0 | 139 | 0 | 139 | 92.7 | 10008.8 | 10016.3 | 10019.9 | 10033.4 | 10.3 | 14.5 |
| 200 | 200 | 5 | 0 | 0 | 0 | 195 | 0 | 195 | 97.5 | 10008.3 | 10013.6 | 10018.2 | 10033.3 | 10.1 | 19.7 |

Stage 10 inventory: `{"ok": true, "sold": 10, "available": 99990, "expected_201": 10}`

Stage 25 inventory: `{"ok": true, "sold": 35, "available": 99965, "expected_201": 35}`

Stage 50 inventory: `{"ok": true, "sold": 85, "available": 99915, "expected_201": 85}`

Stage 100 inventory: `{"ok": false, "sold": 105, "available": 99895, "expected_201": 89}`

Stage 150 inventory: `{"ok": false, "sold": 155, "available": 99845, "expected_201": 100}`

Stage 200 inventory: `{"ok": false, "sold": 197, "available": 99803, "expected_201": 105}`
