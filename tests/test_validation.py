from src.utils.validation import validate_broadcast_segment, clamp_page


def test_validate_broadcast_segment_ok():
    for seg in ["all", "active_subs", "no_active_subs", "service:1"]:
        ok, norm = validate_broadcast_segment(seg)
        assert ok


def test_validate_broadcast_segment_fail():
    cases = ["", "service:", "service:abc", "wrong"]
    for seg in cases:
        ok, err = validate_broadcast_segment(seg)
        assert not ok


def test_clamp_page():
    assert clamp_page(0, 5) == 1
    assert clamp_page(6, 5) == 5
    assert clamp_page(3, 5) == 3
