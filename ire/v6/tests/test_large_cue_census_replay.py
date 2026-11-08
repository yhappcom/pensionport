"""Large-cue-census SHA compatibility: synthetic public-safe reproducer."""
from __future__ import annotations
import hashlib
import json
import unittest

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.source import cue_census_digest, parse_srt, verify_source


def _clock(seconds):
    return f"{seconds//3600:02}:{(seconds//60)%60:02}:{seconds%60:02},000"


class LargeCensusCases(unittest.TestCase):
    def test_legacy_digest_is_identical_for_small_video(self):
        raw = b"1\n00:00:01,000 --> 00:00:02,000\nfirst fact\n\n2\n00:00:03,000 --> 00:00:04,000\nsecond fact"
        cues = parse_srt(raw)
        rows = [{"index": c.index, "start_ms": c.start_ms,
                 "end_ms": c.end_ms, "text": c.text} for c in cues]
        self.assertEqual(cue_census_digest(cues), sha256(canonical(rows)))

    def test_event_payload_size_limit_is_unchanged(self):
        from ire.v6.errors import InvalidInput
        with self.assertRaisesRegex(InvalidInput, "CANONICAL_OBJECT_TOO_LARGE"):
            canonical({"payload": "x" * 1_048_576})

    def test_large_valid_srt_is_not_rejected_by_event_size_cap(self):
        count=11000
        raw = "\n\n".join(f"{i}\n{_clock(i)} --> {_clock(i+1)}\n"
                          + ("valid source context " * 4)
                          for i in range(1,count+1)).encode("utf-8")
        cues = parse_srt(raw)
        self.assertEqual(len(cues),count)
        # 18-cue chunks mirror the public-safe real-source structural probe,
        # not the old V5 historical planning algorithm.
        windows=[]
        for ix, first in enumerate(range(1,count+1,18),1):
            last=min(count,first+17)
            window_text=' '.join(c.text for c in cues[first-1:last])
            windows.append({"window_id":f"W{ix:05d}","first_cue":first,"last_cue":last,
                            "text_sha256":sha256(window_text.encode("utf-8"))})
        plan={"schema":"IRE_V6_SOURCE_PLAN_V1","video_id":"abcdefghijk",
              "source_sha256":sha256(raw),"cue_count":count,
              "scope":{"mode":"FULL_VIDEO","first_cue":1,"last_cue":count},
              "windows":windows}
        result=verify_source(raw,plan,expected_source_sha256=sha256(raw),
                             expected_manifest_sha256=json_digest(plan))
        rows=[{"index":c.index,"start_ms":c.start_ms,"end_ms":c.end_ms,
               "text":c.text} for c in cues]
        independently_serialized = json.dumps(rows,ensure_ascii=False,sort_keys=True,
                                              separators=(',',':')).encode('utf-8')
        self.assertGreater(len(independently_serialized),1_048_576)
        self.assertEqual(result.cue_census_sha256,hashlib.sha256(independently_serialized).hexdigest())
        self.assertEqual(result.owner(count),windows[-1]['window_id'])

if __name__=='__main__': unittest.main()
