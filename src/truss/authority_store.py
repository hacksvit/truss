"""Durable epoch/controls, separate from event evidence. Owner M1."""

import fcntl
import json
import sqlite3
from pathlib import Path


class AuthorityStore:
    def __init__(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=5)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS operations (key TEXT PRIMARY KEY, body TEXT NOT NULL, result TEXT NOT NULL)"
        )
        self.db.commit()
        self.lock_handle = None

    def get(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key: str, value):
        with self.db:
            self.db.execute(
                "INSERT INTO kv VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value)),
            )

    def claim_epoch(self, lock_path: str | Path) -> int:
        if self.lock_handle is not None:
            raise RuntimeError("epoch already claimed by this store")
        handle = open(lock_path, "a+")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.db.execute("BEGIN IMMEDIATE")
            epoch = self.get("epoch", 0) + 1
            self.db.execute(
                "INSERT INTO kv VALUES ('epoch',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (json.dumps(epoch),),
            )
            self.db.commit()
        except BaseException:
            self.db.rollback()
            handle.close()
            raise
        self.lock_handle = handle
        return epoch

    def remember_operation(self, key: str, body: dict, result: dict) -> dict:
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        with self.db:
            old = self.db.execute(
                "SELECT body,result FROM operations WHERE key=?", (key,)
            ).fetchone()
            if old:
                if old[0] != canonical:
                    raise ValueError("idempotency_conflict")
                return json.loads(old[1])
            self.db.execute(
                "INSERT INTO operations VALUES (?,?,?)",
                (key, canonical, json.dumps(result)),
            )
        return result

    def close(self):
        self.db.close()
        if self.lock_handle:
            self.lock_handle.close()
            self.lock_handle = None
