#!/usr/bin/env python3
"""Independent synthetic regression; does not use real holdout labels."""
import tempfile
import zipfile
from pathlib import Path
from v33_source_overlap_gate import parse_srt, screen, zip_srt_map, token_ngrams


def make_srt(tokens):
    text = " ".join(tokens)
    return f"1\n00:00:00,000 --> 00:00:05,000\n{text}\n".encode("utf-8")


def run():
    exposed = make_srt([f"반복문장{i}" for i in range(25)])
    novel = make_srt([f"새문장{i}" for i in range(25)])
    assert len(token_ngrams(parse_srt(exposed))) > 0
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "fixture.zip"
        a = "aaaaaaaaaaa"; b = "bbbbbbbbbbb"; c = "ccccccccccc"
        with zipfile.ZipFile(path, "w") as z:
            for vid, srt in [(a, exposed), (b, exposed), (c, novel)]:
                z.writestr("fixture/youtube-transcript-"+vid+".srt", srt)
        sources = zip_srt_map([path])
        roster = {1:a, 261:b, 262:c}
        out = screen(roster, sources, 1, [261,262])
        assert out["cases"][0]["status"] == "EXCLUDE_HISTORICAL_REUSE"
        assert out["cases"][1]["status"] == "PROVISIONAL_LEXICAL_NOVELTY_ONLY"
        assert out["cases"][0]["max_7gram_containment"] == 1.0
        assert out["release"].startswith("BLOCKED_") and out["recall"] is None
        incomplete = screen(roster, sources, 2, [261,262])
        assert incomplete["missing_historical_numbers"] == [2]
        assert not incomplete["complete_historical_corpus"]
        try:
            screen(roster, sources, 261, [261]); assert False
        except ValueError: pass
        try:
            parse_srt(b"1\n00:00:05,000 --> 00:00:00,000\ninvalid\n");assert False
        except ValueError: pass
    print("PASS: synthetic duplicate, synthetic novel, incomplete history, leakage/format guards")


if __name__ == "__main__":
    run()
