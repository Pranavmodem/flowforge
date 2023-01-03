# Queryscope

Compare SQL scan cost and compute cluster cost for a workload. Supply observed
scan size, expected runtime, rates, retry frequency, and the fraction of work
repeated per retry. The freshness check adds the batch interval and processing
time and compares the result to the budget.

```sh
python3 queryscope.py examples/workload.json
python3 -m unittest discover -s tests -v
```

The workload file owns the pricing assumptions. Costs exclude storage,
transfer, and fixed platform charges. The report compares estimates and does
not query cloud accounts.
