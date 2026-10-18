| C | Baseline 2xx | Optimized 2xx | Baseline error % | Optimized error % | Baseline p95 ms | Optimized p95 ms | Baseline req/s | Optimized req/s |
|---|---|---|---|---|---|---|---|---|
| 10 | 10.0 | 10.0 | 0.0 | 0.0 | 1452.4 | 746.8 | 6.8 | 13.3 |
| 25 | 25.0 | 25.0 | 0.0 | 0.0 | 2606.7 | 1844.5 | 9.5 | 13.3 |
| 50 | 50.0 | 50.0 | 0.0 | 0.0 | 4980.6 | 3564.2 | 9.7 | 13.7 |
| 100 | 4.0 | 100.0 | 96.0 | 0.0 | 10033.2 | 9558.4 | 9.8 | 10.0 |
| 150 | 11.0 | 132.0 | 92.7 | 12.0 | 10016.3 | 10020.7 | 14.5 | 14.6 |
| 200 | 5.0 | 76.0 | 97.5 | 62.0 | 10013.6 | 10293.8 | 19.7 | 18.7 |
Baseline: BREAKING POINT: concurrency 25 (p95 exceeds threshold).
Optimized: BREAKING POINT: concurrency 50 (p95 exceeds threshold).
