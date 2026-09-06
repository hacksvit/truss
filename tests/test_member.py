from truss.member import MemberReceiver


def receiver(registration, lease):
    return MemberReceiver(
        registration, lease.ref.member_boot_id, lease.site_id, lease.run_id, 1
    )


def test_delayed_grant_cannot_restart_ttl(registration, lease):
    m = receiver(registration, lease)
    m.open_request(lease.ref.request_id, 0)
    assert m.accept(lease, 6_000_000_000) == "expired"
    assert m.budget(6_000_000_000) == 100


def test_duplicate_and_partition_heal(registration, lease):
    m = receiver(registration, lease)
    m.open_request(lease.ref.request_id, 0)
    assert m.accept(lease, 1_000_000_000) == "applied"
    assert m.accept(lease, 5_000_000_000) == "duplicate"
    assert m.budget(6_000_000_000) == 100
    m.open_request("new-request", 6_000_000_001)
    assert m.accept(lease, 6_000_000_002) == "expired"
    assert m.budget(6_000_000_002) == 100


def test_unrequested_grant_rejected(registration, lease):
    assert receiver(registration, lease).accept(lease, 0) == "wrong_request"
