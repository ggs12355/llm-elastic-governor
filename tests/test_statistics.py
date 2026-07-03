from common.statistics import percentile, safe_div, summarize


def test_percentile_interpolates():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 99) == 0.0


def test_summarize_empty_and_values():
    assert summarize([])["count"] == 0
    summary = summarize([1, 2, 3])
    assert summary["count"] == 3
    assert summary["p50"] == 2


def test_safe_div():
    assert safe_div(1, 0) == 0.0
    assert safe_div(4, 2) == 2

