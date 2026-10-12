"""Private SQLite backup and recovery checks for ReferDue."""
import argparse
import os
import sqlite3
import tempfile
from pathlib import Path


def _resolved(path):
    return Path(path).expanduser().resolve()


def integrity(path):
    path = _resolved(path)
    if not path.is_file():
        raise ValueError("Database file does not exist")
    with sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True) as db:
        return [row[0] for row in db.execute("PRAGMA integrity_check")]


def _verify(path):
    rows = integrity(path)
    if rows != ["ok"]:
        raise ValueError("SQLite integrity check failed: " + "; ".join(rows))


def backup(source, destination):
    """Create an integrity-checked backup without replacing a prior backup."""
    source, destination = _resolved(source), _resolved(destination)
    if source == destination:
        raise ValueError("Source and destination must differ")
    if not source.is_file():
        raise ValueError("Source database does not exist")
    if destination.exists():
        raise FileExistsError("Destination already exists; backups are never overwritten")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    temporary = Path(temporary)
    try:
        with sqlite3.connect(source) as original, sqlite3.connect(temporary) as copy:
            original.backup(copy)
        os.chmod(temporary, 0o600)
        _verify(temporary)
        temporary.replace(destination)
        return destination
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def restore(source, destination):
    """Restore a verified backup into a new path; never overwrite live data."""
    source, destination = _resolved(source), _resolved(destination)
    _verify(source)
    if destination.exists():
        raise FileExistsError("Restore destination already exists")
    restored = backup(source, destination)
    _verify(restored)
    return restored


def main(argv=None):
    parser = argparse.ArgumentParser(description="ReferDue SQLite backup and recovery verifier")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("backup", "restore"):
        command = sub.add_parser(name)
        command.add_argument("source")
        command.add_argument("destination")
    check = sub.add_parser("check")
    check.add_argument("source")
    args = parser.parse_args(argv)
    if args.command == "check":
        _verify(args.source)
        print("Integrity check: ok")
        return 0
    result = backup(args.source, args.destination) if args.command == "backup" else restore(args.source, args.destination)
    print(f"{args.command.title()} verified: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
