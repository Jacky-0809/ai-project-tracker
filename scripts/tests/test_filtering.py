"""Unit tests for the content filtering module (scripts/filtering.py).

Run:  python -m pytest scripts/tests/test_filtering.py  (or)  python scripts/tests/test_filtering.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from filtering import score_item, _load_lists, filter_and_rank_top

LISTS = _load_lists({})


def kept(item, platform):
    it = dict(item)
    r = score_item(it, platform, LISTS)
    return r is not None, (r.get("score") if r else None)


def test_keeps_good_tutorial():
    ok, _ = kept({"title": "Claude Skill 入门", "text": "step by step guide to install and use skills",
                  "likes": 500, "author": "@dev"}, "x")
    assert ok


def test_blocks_cn_spam():
    ok, _ = kept({"title": "限时抢购", "text": "扫码加微信 立即购买 仅限今天 免费领取",
                  "likes": 9999, "author": "@promo"}, "x")
    assert not ok


def test_blocks_en_spam():
    ok, _ = kept({"title": "sponsored post", "text": "click here sign up today earn money crypto % off",
                  "likes": 7000, "author": "@p"}, "x")
    assert not ok


def test_blocks_low_stars_github():
    ok, _ = kept({"name": "a/b", "description": "x" * 40, "stars": 1, "owner": "a"}, "github")
    assert not ok


def test_keeps_good_github():
    ok, _ = kept({"name": "Awesome Skills", "description": "curated agent skill list with guides",
                  "stars": 500, "owner": "x"}, "github")
    assert ok


def test_keeps_high_views_youtube():
    ok, _ = kept({"title": "How to build AI skills", "description": "full walkthrough " * 4,
                  "views": 5000, "channel": "c"}, "youtube")
    assert ok


def test_blocks_graylist_strong_promo():
    # two hard-promo words => always dropped even with high engagement
    ok, _ = kept({"title": "限时优惠 免费领取", "text": "立即购买 best skill course",
                  "likes": 5000, "author": "@a"}, "x")
    assert not ok


def test_end_to_end_rank():
    sections = {
        "x": [
            {"title": "How to use Claude Skills", "text": "step by step guide to install and use agent skills",
             "likes": 800, "author": "@good1", "url": "x/1"},
            {"title": "限时抢购 Claude 账号", "text": "扫码加微信 立即购买 仅限今天", "likes": 5000, "author": "@s", "url": "x/2"},
            {"title": "Best agent skill list", "text": "top curated AI skills with comparisons", "likes": 300, "author": "@good2", "url": "x/3"},
        ],
        "date": "2026-09-04",  # non-list key must be skipped
    }
    r = filter_and_rank_top(sections, 20, {})
    assert "date" not in r
    assert len(r["x"]) == 2
    titles = [i["title"] for i in r["x"]]
    assert all("抢购" not in t for t in titles)
    assert r["x"][0]["score"] >= r["x"][1]["score"]


if __name__ == "__main__":
    import traceback
    passed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"✓ {name}")
                passed += 1
            except Exception:
                print(f"✗ {name}")
                traceback.print_exc()
    print(f"\n{passed} passed")