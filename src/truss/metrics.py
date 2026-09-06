"""Quality-aware metrics. Owner M5. Unknown never becomes zero load."""

from collections.abc import Sequence


def percentage(numerator: int, denominator: int) -> float | None:
    return 100 * numerator / denominator if denominator else None


def observed_total(
    samples: Sequence[tuple[int | None, int | None]], stale_ms: int = 1500
) -> int | None:
    if not samples or any(
        w is None or age is None or not 0 <= age <= stale_ms for w, age in samples
    ):
        return None
    return sum(w for w, _ in samples)


def jain(ratios: Sequence[float]) -> float | None:
    if len(ratios) < 2 or any(r < 0 for r in ratios) or sum(r * r for r in ratios) == 0:
        return None
    return sum(ratios) ** 2 / (len(ratios) * sum(r * r for r in ratios))
