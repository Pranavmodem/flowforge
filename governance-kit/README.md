# Governance Kit

Compare access snapshots, route findings by ownership, and preview deletion
actions against an explicit inventory. An ambiguous or missing owner routes
to manual triage. A deletion preview reports completion only after all required
locations have been discovered and every discovered target is verified.

```sh
python3 governance.py drift examples/drift.json
python3 governance.py deletion examples/deletion.json
python3 -m unittest discover -s tests -v
```

The commands operate on input files. They make no IAM or storage changes.
