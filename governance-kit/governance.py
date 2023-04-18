"""Compare access snapshots and preview deletion actions."""

import argparse
import json

ACTIONS = {"queued", "acknowledged", "verified"}


def strings(value, field):
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(field + " must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError(field + " contains duplicates")
    return set(value)


def mapping(value, field):
    if not isinstance(value, dict) or any(not isinstance(key, str) or not key for key in value):
        raise ValueError(field + " must be an object with named entries")
    return value


def findings(baseline, current, owners):
    baseline = mapping(baseline, "baseline")
    current = mapping(current, "current")
    owners = mapping(owners, "owners")
    before = {asset: strings(roles, asset) for asset, roles in baseline.items()}
    after = {asset: strings(roles, asset) for asset, roles in current.items()}
    routes = {asset: strings(names, asset) for asset, names in owners.items()}
    output = []
    for asset in sorted(after):
        added = sorted(after[asset] - before.get(asset, set()))
        if asset in before and not added:
            continue
        candidates = sorted(routes.get(asset, set()))
        output.append({
            "asset": asset, "new_asset": asset not in before, "new_roles": added,
            "route": candidates[0] if len(candidates) == 1 else "manual-triage",
            "owner_candidates": candidates,
        })
    return output


def deletion_plan(discovered, expected, ledger):
    targets = strings(discovered, "discovered")
    required = strings(expected, "expected")
    if not required:
        raise ValueError("expected locations cannot be empty")
    states = mapping(ledger, "ledger")
    for target, state in states.items():
        if target not in targets or not isinstance(state, str) or state not in ACTIONS:
            raise ValueError("invalid ledger entry for " + target)
    missing = sorted(required - targets)
    unverified = sorted(target for target in targets if states.get(target) != "verified")
    return {
        "missing_locations": missing,
        "actions": [{"target": target, "action": "queue" if target not in states else "verify"}
                    for target in unverified],
        "complete": not missing and not unverified,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("drift", "deletion"))
    parser.add_argument("fixture")
    args = parser.parse_args()
    try:
        with open(args.fixture, encoding="utf-8") as source:
            fixture = json.load(source)
        if not isinstance(fixture, dict):
            raise ValueError("fixture must be an object")
        result = findings(**fixture) if args.mode == "drift" else deletion_plan(**fixture)
        print(json.dumps(result, indent=2, sort_keys=True))
    except (OSError, ValueError, TypeError) as exc:
        parser.exit(2, "governance: {}\n".format(exc))


if __name__ == "__main__":
    main()
