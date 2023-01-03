"""Estimate workload costs and test a batch freshness budget."""

import argparse
import json
from decimal import Decimal, InvalidOperation, localcontext


def number(data, key):
    value = data.get(key)
    if isinstance(value, bool) or value is None:
        raise ValueError(key + " must be a finite nonnegative number")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(key + " must be a number") from exc
    if not amount.is_finite() or amount < 0 or amount > 10**20:
        raise ValueError(key + " must be a finite nonnegative number")
    return amount


def estimate(spec):
    if not isinstance(spec, dict):
        raise ValueError("workload must be a JSON object")
    runs = number(spec, "runs")
    scan = number(spec, "scan_tib")
    sql_price = number(spec, "sql_per_tib")
    hours = number(spec, "cluster_hours")
    cluster_price = number(spec, "cluster_per_hour")
    retry = number(spec, "retry_fraction")
    sql_retry_scan = number(spec, "retry_scan_fraction")
    cluster_retry_time = number(spec, "retry_time_fraction")
    if max(retry, sql_retry_scan, cluster_retry_time) > 1:
        raise ValueError("retry fractions must be between zero and one")

    sql = runs * scan * sql_price * (1 + retry * sql_retry_scan)
    cluster = runs * hours * cluster_price * (1 + retry * cluster_retry_time)
    freshness = number(spec, "cadence_minutes") + number(spec, "processing_minutes")
    budget = number(spec, "freshness_budget_minutes")
    with localcontext() as context:
        context.prec = 70
        sql_display = str(sql.quantize(Decimal("0.01")))
        cluster_display = str(cluster.quantize(Decimal("0.01")))
    return {
        "sql_cost": sql_display,
        "cluster_cost": cluster_display,
        "lower_cost": "sql" if sql < cluster else "cluster" if cluster < sql else "tie",
        "worst_case_freshness_minutes": str(freshness),
        "within_freshness_budget": freshness <= budget,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workload")
    args = parser.parse_args()
    try:
        with open(args.workload, encoding="utf-8") as source:
            report = estimate(json.load(source, parse_float=Decimal))
        print(json.dumps(report, indent=2, sort_keys=True))
    except (OSError, ValueError, InvalidOperation) as exc:
        parser.exit(2, "queryscope: {}\n".format(exc))


if __name__ == "__main__":
    main()
