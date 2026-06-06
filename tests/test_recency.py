from datetime import date

from main import annotate_recency

TODAY = date(2026, 6, 6)


def _perk(pid: str) -> dict:
    return {"id": pid}


def test_new_when_absent_from_previous_run():
    perks = [_perk("a")]
    annotate_recency(perks, [], TODAY)
    assert perks[0]["first_seen"] == "2026-06-06"
    assert perks[0]["is_new"] is True


def test_recent_first_seen_stays_new():
    perks = [_perk("a")]
    prev = [{"id": "a", "first_seen": "2026-06-02"}]  # 4 days ago
    annotate_recency(perks, prev, TODAY)
    assert perks[0]["first_seen"] == "2026-06-02"
    assert perks[0]["is_new"] is True


def test_old_first_seen_ages_out():
    perks = [_perk("a")]
    prev = [{"id": "a", "first_seen": "2026-05-01"}]  # >7 days ago
    annotate_recency(perks, prev, TODAY)
    assert perks[0]["first_seen"] == "2026-05-01"
    assert perks[0]["is_new"] is False


def test_present_before_without_record_is_not_flagged_new():
    perks = [_perk("a")]
    prev = [{"id": "a"}]  # seen last run but no first_seen recorded
    annotate_recency(perks, prev, TODAY)
    assert perks[0]["is_new"] is False
