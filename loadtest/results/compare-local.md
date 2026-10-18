| C | Baseline 2xx | Optimized 2xx | Baseline error % | Optimized error % | Baseline p95 ms | Optimized p95 ms | Baseline req/s | Optimized req/s |
|---|---|---|---|---|---|---|---|---|
| 10 | 10.0 | 10.0 | 0.0 | 0.0 | 182.5 | 73.3 | 52.2 | 134.8 |
| 25 | 25.0 | 25.0 | 0.0 | 0.0 | 475.2 | 259.9 | 50.9 | 90.3 |
| 50 | 50.0 | 50.0 | 0.0 | 0.0 | 668.6 | 504.6 | 71.7 | 95.9 |
| 100 | 0.0 | 100.0 | 100.0 | 0.0 | 10020.4 | 775.1 | 9.9 | 119.0 |
| 200 | 0.0 | 200.0 | 100.0 | 0.0 | 10020.1 | 1640.2 | 19.5 | 109.4 |
| 300 | 0.0 | 300.0 | 100.0 | 0.0 | 10246.2 | 2706.7 | 28.4 | 98.4 |
| 500 | 0.0 | 500.0 | 100.0 | 0.0 | 10056.8 | 7414.2 | 47.1 | 64.8 |
| 750 | 0.0 | 750.0 | 100.0 | 0.0 | 10043.4 | 9266.0 | 68.7 | 78.2 |
| 1000 | 0.0 | 878.0 | 100.0 | 12.2 | 12962.8 | 11633.2 | 68.6 | 82.0 |
Baseline: BREAKING POINT: concurrency 100 (error rate exceeds threshold, p95 exceeds threshold).
Optimized: BREAKING POINT: concurrency 300 (p95 exceeds threshold).
