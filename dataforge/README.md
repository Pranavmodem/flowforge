# Dataforge

Dataforge copies files between local directories with tenant isolation,
checksums, and an atomic per-tenant inventory.

```sh
python3 dataforge.py examples/source output examples/tenants.json --dry-run
python3 dataforge.py examples/source output examples/tenants.json
python3 -m unittest discover -s tests -v
```

Each manifest entry names a tenant directory under the source and output
roots. Reruns compare content hashes. A dry run reports planned transfers
without writing files. Each transferred file is replaced atomically, and the
ledger updates only after all transfers for its tenant succeed. If a transfer
fails, a rerun checks the output and resumes. Other tenants continue. Files
removed from the source are removed from the inventory. Existing output files
are retained.

Use this local, POSIX prototype with trusted directory owners. Run it against
test data. It does not connect to cloud storage or delete files.
