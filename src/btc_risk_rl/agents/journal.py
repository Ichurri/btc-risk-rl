"""Append-only state with locked revisions: stale writers cannot roll back a run."""

import fcntl
import hashlib
import json
import os
from pathlib import Path


class RunJournal:
    def __init__(self, path, *, create):
        self.path = Path(path).resolve()
        if create:
            self.path.mkdir(parents=True, exist_ok=False)
            (self.path / "events.jsonl").touch(exist_ok=False)
        elif not (self.path / "events.jsonl").is_file():
            raise ValueError("Missing run journal")
        self.revision = hashlib.sha256((self.path / "events.jsonl").read_bytes()).hexdigest()
        if create:
            self.append(status="new")

    def append(self, **record):
        # Linux CPU runtime. All cooperating writers must own the current revision.
        with (self.path / "events.jsonl").open("r+b") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            content = f.read()
            if hashlib.sha256(content).hexdigest() != self.revision:
                raise ValueError("Stale run journal revision; rollback/concurrent writer forbidden")
            line = (json.dumps(record, sort_keys=True) + "\n").encode()
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
            self.revision = hashlib.sha256(content + line).hexdigest()

    def last(self):
        try:
            lines = (self.path / "events.jsonl").read_text().splitlines()
            return json.loads(lines[-1])
        except (ValueError, IndexError) as exc:
            raise ValueError("Incomplete run journal") from exc
