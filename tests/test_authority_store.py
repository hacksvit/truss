"""M1: durable epochs, exclusive issuer lock and persisted operation conflicts."""

import pytest
from truss.authority_store import AuthorityStore


def test_singleton_and_durable_epoch(tmp_path):
    path = tmp_path / "authority.sqlite"
    lock = tmp_path / "coordinator.lock"
    a = AuthorityStore(path)
    b = AuthorityStore(path)
    try:
        assert a.claim_epoch(lock) == 1
        with pytest.raises(BlockingIOError):
            b.claim_epoch(lock)
        a.close()
        a = None
        assert b.claim_epoch(lock) == 2
    finally:
        if a:
            a.close()
        b.close()


def test_idempotency_conflict_is_durable(tmp_path):
    p = tmp_path / "authority.sqlite"
    a = AuthorityStore(p)
    a.remember_operation("k", {"watts": 100}, {"result": "applied"})
    a.close()
    b = AuthorityStore(p)
    try:
        assert b.remember_operation("k", {"watts": 100}, {"result": "other"}) == {
            "result": "applied"
        }
        with pytest.raises(ValueError):
            b.remember_operation("k", {"watts": 200}, {})
    finally:
        b.close()
