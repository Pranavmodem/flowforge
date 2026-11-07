# Flowforge

Local tools for previewing workflows, transferring files by tenant, comparing
workload costs, and checking data governance decisions.

| Tool | What it does |
|---|---|
| [Flowforge](flowforge/README.md) | Validates and seals workflow specs, orders dependencies, and shows how failures block downstream tasks. |
| [Dataforge](dataforge/README.md) | Transfers local files with tenant isolation, checksums, and repeatable retries. |
| [Queryscope](queryscope/README.md) | Compares SQL scan costs and cluster costs under supplied workload and freshness assumptions. |
| [Governance Kit](governance-kit/README.md) | Compares access snapshots, routes findings to owners, and previews deletion actions against an inventory. |

## Try the examples

Run from the repository root.

```sh
(cd flowforge && python3 flowforge.py examples/workflow.json --fail fetch)
(cd dataforge && python3 dataforge.py examples/source output examples/tenants.json --dry-run)
(cd queryscope && python3 queryscope.py examples/workload.json)
(cd governance-kit && python3 governance.py drift examples/drift.json)
```

These commands use the included fixtures and require no cloud credentials.
Dataforge uses POSIX file locking on macOS and Linux. The other modules use
portable Python standard-library APIs. Each module guide includes its test
command.

Original course files are available as [example.py](example.py) and
[example1.py](example1.py).
