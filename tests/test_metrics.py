from truss.metrics import observed_total, percentage, jain


def test_unknown_is_not_zero():
    assert observed_total([(100, 0), (None, 0)]) is None
    assert observed_total([(100, 1501)]) is None
    assert observed_total([(0, 0)]) == 0
    assert percentage(0, 0) is None and jain([0, 0]) is None
    assert jain([1, 1]) == 1
