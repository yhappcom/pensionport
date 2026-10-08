"""V4 schema and semantic safety-gate regression tests."""
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "scripts/validate_v4.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
ROSTER = v.inventory(ROOT / "VIDEO_INVENTORY_2026-10-07.md")
S = v.load(ROOT / "schemas/v4_video_analysis.schema.json")
M = v.load(ROOT / "schemas/v4_pilot_manifest.schema.json")

def fixture():
    return {
        "schema_version": 4,
        "video": {"video_id": "PW1EuMtw18o", "title": "ISA historical example",
                  "watch_url": "https://www.youtube.com/watch?v=PW1EuMtw18o",
                  "published_at": "2021-08-11", "content_type": "Long-form", "duration_seconds": 762},
        "status": "DRAFT", "stage": "GROUNDED",
        "sources": [{"source_id": "speech", "kind": "YOUTUBE_TRANSCRIPT",
                     "url": "https://www.youtube.com/watch?v=PW1EuMtw18o",
                     "retrieved_at": "2026-10-08", "coverage": "FULL", "language": "ko",
                     "limitations": ["ASR numerical uncertainty", "not visually reviewed"]}],
        "claims": [{"claim_id": "C01", "statement": "The speaker historically discussed ISA and health-insurance income recognition.",
                    "claim_type": "HISTORICAL_FACT",
                    "evidence": [{"source_id": "speech", "start_seconds": None,
                                  "end_seconds": None, "excerpt": None,
                                  "limitations": ["No transcript timecodes"]}],
                    "conditions": ["Historical context only"],
                    "risks": ["Changed regulations"],
                    "time_scope": {"sensitivity": "HISTORICAL", "as_of": "2021-08-11",
                                   "valid_from": None, "valid_until": None},
                    "verification": {"status": "OPEN", "checked_at": None,
                                     "official_source_ids": [], "notes": "No current rule implied"}}],
        "quality": {"transcript_coverage": "FULL", "visual_review": "NOT_REVIEWED",
                    "requires_visual_review": True, "known_asr_issues": [],
                    "reviewer_notes": ["Fixture only; not an actual analysis"]},
        "relationships": [],
        "decision_use": {"ready": False, "scope": "Historical education",
                         "constraints": [], "requires_current_recheck": True, "risks": []},
    }

class V4Tests(unittest.TestCase):
    def errors(self, doc):
        return v.audit_analysis(doc, ROSTER, S)
    def test_roster_and_manifest(self):
        self.assertEqual((len(ROSTER), list(ROSTER.values()).count("Long-form"),
                          list(ROSTER.values()).count("Short")), (791, 703, 88))
        self.assertEqual(v.audit_manifest(v.load(ROOT / "data/v4/pilot_manifest.json"), ROSTER, M), [])
    def test_grounded_fixture_valid(self):
        self.assertEqual(self.errors(fixture()), [])
    def test_reject_wrong_url_or_filename(self):
        d = fixture()
        d["video"]["watch_url"] = "https://www.youtube.com/watch?v=AAAAAAAAAAA"
        err = v.audit_analysis(d, ROSTER, S, "another.json")
        self.assertTrue(any("URL" in e for e in err))
        self.assertTrue(any("Filename" in e for e in err))
    def test_reject_secondary_only(self):
        d = fixture()
        d["sources"][0]["kind"] = "SECONDARY_SUMMARY"
        self.assertTrue(any("original" in e for e in self.errors(d)))
    def test_reject_fake_timecode(self):
        d = fixture()
        d["claims"][0]["evidence"][0].update(start_seconds=700, end_seconds=900)
        self.assertTrue(any("duration" in e for e in self.errors(d)))
    def test_reject_source_and_claim_duplicates(self):
        d = fixture()
        d["sources"].append(copy.deepcopy(d["sources"][0]))
        d["claims"].append(copy.deepcopy(d["claims"][0]))
        err = self.errors(d)
        self.assertTrue(any("Duplicate source" in e for e in err))
        self.assertTrue(any("Duplicate claim" in e for e in err))
    def test_reject_promoted_unverified(self):
        d = fixture()
        d["stage"] = "VERIFIED"
        self.assertTrue(any("primary-source" in e for e in self.errors(d)))
    def test_reject_visual_claim_without_evidence(self):
        d = fixture()
        d["quality"]["visual_review"] = "REVIEWED"
        self.assertTrue(any("VIDEO_FRAME" in e for e in self.errors(d)))
    def test_reject_premature_investment_use(self):
        d = fixture()
        d["stage"] = "DECISION_READY"
        d["decision_use"]["ready"] = True
        err = self.errors(d)
        self.assertTrue(any("visual" in e for e in err))
        self.assertTrue(any("APPROVED" in e for e in err))

if __name__ == "__main__":
    unittest.main()
