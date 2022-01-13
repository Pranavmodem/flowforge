"""Synchronize local tenant fixtures with content checks and atomic writes."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

TENANT_NAME = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")
LEDGER = ".dataforge-ledger.json"


def _digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def _atomic_write(target, writer):
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=str(target.parent), delete=False) as output:
        temporary = Path(output.name)
    try:
        writer(temporary)
        os.replace(str(temporary), str(target))
    finally:
        if temporary.exists():
            temporary.unlink()


def _safe_target(root, relative):
    target = root
    for part in relative.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError("symbolic link in destination")
    return target


def _sync_tenant(source, target, dry_run):
    if source.is_symlink() or not source.is_dir():
        raise ValueError("tenant source must be a directory without symbolic links")
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError("tenant destination must be a directory without symbolic links")

    inventory = {}
    transfers = []
    for folder, dirs, files in os.walk(str(source), onerror=_raise):
        folder = Path(folder)
        if any((folder / name).is_symlink() for name in dirs):
            raise ValueError("symbolic link in source")
        for name in sorted(files):
            entry = folder / name
            relative = entry.relative_to(source)
            if relative == Path(LEDGER) or entry.is_symlink() or not entry.is_file():
                raise ValueError("reserved filename or unsupported source entry")
            destination = _safe_target(target, relative)
            if destination.exists() and not destination.is_file():
                raise ValueError("destination entry is not a regular file")
            digest = _digest(entry)
            inventory[relative.as_posix()] = digest
            if not destination.exists() or _digest(destination) != digest:
                transfers.append((entry, destination, digest))

    if not dry_run:
        ledger = _safe_target(target, Path(LEDGER))
        if ledger.exists() and not ledger.is_file():
            raise ValueError("ledger is not a regular file")
        for entry, destination, digest in transfers:
            _atomic_write(destination, lambda temporary: _copy(entry, temporary, digest))
        payload = json.dumps(inventory, indent=2, sort_keys=True) + "\n"
        if not ledger.exists() or ledger.read_text(encoding="utf-8") != payload:
            _atomic_write(ledger, lambda temporary: temporary.write_text(payload, encoding="utf-8"))

    return {
        "status": "ok",
        "copied": 0 if dry_run else len(transfers),
        "planned": len(transfers),
        "unchanged": len(inventory) - len(transfers),
    }


def _raise(exc):
    raise exc


def _copy(source, destination, digest):
    checksum = hashlib.sha256()
    with source.open("rb") as incoming, destination.open("wb") as outgoing:
        for block in iter(lambda: incoming.read(1024 * 1024), b""):
            checksum.update(block)
            outgoing.write(block)
    if checksum.hexdigest() != digest:
        raise ValueError("source changed during transfer")


def _run(source, target, tenants, dry_run):
    results = {}
    for name in sorted(tenants):
        try:
            results[name] = _sync_tenant(source / name, target / name, dry_run)
        except (OSError, ValueError) as exc:
            results[name] = {"status": "failed", "error": str(exc)}
    return results


def sync(source, target, tenants, *, dry_run=False):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("source and output roots must be disjoint")
    if not isinstance(tenants, list) or not tenants:
        raise ValueError("tenant list must be nonempty")
    if not all(isinstance(name, str) and TENANT_NAME.fullmatch(name) for name in tenants):
        raise ValueError("invalid tenant name")
    if len(set(tenants)) != len(tenants):
        raise ValueError("duplicate tenant")
    if dry_run:
        return _run(source, target, tenants, True)

    target.mkdir(parents=True, exist_ok=True)
    lock = target / ".dataforge.lock"
    descriptor = os.open(str(lock), os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return _run(source, target, tenants, False)
    finally:
        os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("manifest")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        with open(args.manifest, encoding="utf-8") as source:
            tenants = json.load(source)
        report = sync(args.source, args.target, tenants, dry_run=args.dry_run)
        print(json.dumps(report, indent=2, sort_keys=True))
    except (OSError, ValueError) as exc:
        parser.exit(2, "dataforge: {}\n".format(exc))
    return int(any(result["status"] == "failed" for result in report.values()))


if __name__ == "__main__":
    raise SystemExit(main())
