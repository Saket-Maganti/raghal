### Deployment Pareto (latency vs faith)

| dataset   | condition   |   n |   faith |   halluc_rate |    sim |   median_latency |   p95_latency | pareto   |
|:----------|:------------|----:|--------:|--------------:|-------:|-----------------:|--------------:|:---------|
| hotpotqa  | crag        |  30 |  0.6314 |        0.2333 | 0.6051 |            1.21  |        2.704  | True     |
| hotpotqa  | hcpc_v1     |  30 |  0.6498 |        0.1667 | 0.5699 |            1.455 |        3.0165 | True     |
| hotpotqa  | hcpc_v2     |  30 |  0.6073 |        0.2333 | 0.5519 |            1.71  |        3.515  | False    |
| hotpotqa  | baseline    |  30 |  0.6091 |        0.1667 | 0.552  |            1.84  |        3.586  | False    |
| hotpotqa  | selfrag     |  30 |  0.5509 |        0.4333 | 0.552  |            4.63  |        8.069  | False    |
| pubmedqa  | crag        |  30 |  0.5862 |        0.3333 | 0.7206 |            2.495 |        5.3845 | True     |
| pubmedqa  | hcpc_v1     | 150 |  0.5696 |        0.2333 | 0.6963 |            6.065 |       11.265  | False    |
| pubmedqa  | hcpc_v2     | 150 |  0.5902 |        0.1667 | 0.6828 |            8.665 |       15.623  | True     |
| pubmedqa  | baseline    | 150 |  0.6013 |        0.1733 | 0.6828 |           10.935 |       16.3905 | True     |
| squad     | crag        |  30 |  0.7872 |        0.0333 | 0.6264 |            1.155 |        2.4165 | True     |
| squad     | hcpc_v1     | 150 |  0.7664 |        0.04   | 0.716  |            1.965 |        4.662  | False    |
| squad     | hcpc_v2     | 150 |  0.8077 |        0.0133 | 0.7117 |            3.145 |        5.9705 | True     |
| squad     | baseline    | 150 |  0.7987 |        0.0267 | 0.7117 |            3.815 |        6.7825 | False    |
| squad     | selfrag     |  22 |  0.5504 |        0.4545 | 0.604  |            4.905 |       10.184  | False    |

