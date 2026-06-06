from smoke_sources import _label, render


def test_label_prefers_name():
    assert _label("curated", {"name": "Foo", "url": "https://x"}) == "Foo"


def test_label_falls_back_to_query_then_subreddit():
    assert _label("search", {"query": "free credits"}) == "free credits"
    assert _label("reddit", {"subreddit": "PhD"}) == "PhD"


def test_render_has_table_and_totals():
    out = render([("curated", "Foo", 3), ("reddit", "PhD", 0)])
    assert "| type | source | candidates |" in out
    assert "| curated | Foo | 3 |" in out
    assert "Total candidates: 3" in out
    assert "producing 0: 1" in out
