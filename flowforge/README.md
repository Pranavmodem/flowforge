# Flowforge

Flowforge seals a JSON workflow into immutable tasks, computes a deterministic
dependency order, and previews task outcomes.

```sh
python3 flowforge.py examples/workflow.json --fail fetch
python3 -m unittest discover -s tests -v
```

The preview returns a SHA-256 digest of the canonical spec, a topological
order, and a status per task. A failed task blocks its descendants. Independent
tasks keep their own outcomes. Unknown dependencies and cycles are rejected.
Preview uses the sealed spec and does not execute tasks or read external state.

The fixture suite covers dependency shapes, cycles, and failure propagation.
Only the Python standard library is required.
