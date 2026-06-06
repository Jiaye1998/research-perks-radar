import yaml

from validate_sources import validate, SOURCES


def test_valid_minimal():
    data = {
        "curated": [{"name": "X", "url": "https://example.com", "category": "software"}],
        "reddit": [{"subreddit": "PhD", "category": None}],
    }
    assert validate(data) == []


def test_unknown_top_level_key():
    errs = validate({"nope": []})
    assert any("unknown top-level key" in e for e in errs)


def test_missing_required_field():
    errs = validate({"curated": [{"name": "X"}]})
    assert any("missing required field 'url'" in e for e in errs)


def test_bad_category():
    errs = validate({"search": [{"query": "q", "category": "bogus"}]})
    assert any("category 'bogus'" in e for e in errs)


def test_null_category_is_allowed():
    assert validate({"reddit": [{"subreddit": "PhD", "category": None}]}) == []


def test_bad_url():
    errs = validate({"rss": [{"name": "X", "url": "not a url"}]})
    assert any("not a valid http(s) URL" in e for e in errs)


def test_duplicate_url():
    data = {"curated": [
        {"name": "A", "url": "https://example.com"},
        {"name": "B", "url": "https://example.com"},
    ]}
    errs = validate(data)
    assert any("duplicate url" in e for e in errs)


def test_real_sources_file_is_valid():
    data = yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}
    assert validate(data) == []
