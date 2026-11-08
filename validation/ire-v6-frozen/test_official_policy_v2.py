"""V2: fixed official primary-source anchors and no human reviewer as a release requirement.

These tests prove original FIRST-PARTY document bytes and visible text; they
do not falsely 'prove' an SRT speaker's actual proposition by keyword match.
"""
import hashlib
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript"):
            self.hidden+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript"):
            self.hidden=max(0,self.hidden-1)
    def handle_data(self,text):
        if not self.hidden:self.parts.append(text)

def normalize(v):
    return re.sub(r"\s+","",v)

def ensure_official_anchor(anchor,raw):
    if anchor["url"].startswith("http://") or not anchor["url"].startswith("https://"):
        raise ValueError("NOT_SECURE_PRIMARY_URL")
    host=anchor["url"].split("/")[2].lower()
    if host not in ("nts.go.kr","www.nts.go.kr","law.go.kr","www.law.go.kr"):
        raise ValueError("NOT_ALLOWLISTED_OFFICIAL_DOMAIN")
    if hashlib.sha256(raw).hexdigest()!=anchor["sha256"]:
        raise ValueError("ORIGINAL_SOURCE_BYTES_DRIFT")
    parser=VisibleText()
    parser.feed(raw.decode("utf-8",errors="replace"))
    visible=normalize("".join(parser.parts))
    if not all(normalize(x) in visible for x in anchor["required_visible_phrases"]):
        raise ValueError("OFFICIAL_EXCERPT_NOT_PRESENT")
    if anchor["effective_date_verified"]:
        if not anchor["effective_from"]:
            raise ValueError("OFFICIAL_LEGAL_DATE_NOT_MATCHED")
        y,m,d=[int(x) for x in anchor["effective_from"].split("-")]
        exact_visible_date=f"[시행{y}.{m}.{d}.]"
        if exact_visible_date not in visible:
            raise ValueError("OFFICIAL_LEGAL_DATE_NOT_MATCHED")
    return True

class OfficialPolicyV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads((HERE/"OFFICIAL_SOURCE_VERIFICATION_POLICY_V2.json").read_text(encoding="utf-8"))
        cls.ledger=json.loads((HERE/"FIRST_PARTY_PUBLIC_RULE_ANCHORS_V2.json").read_text(encoding="utf-8"))
    def test_independent_human_is_not_a_gate(self):
        p=self.policy
        self.assertFalse(p["independent_human_review_required"])
        self.assertFalse(p["independent_human_gold_required"])
        self.assertFalse(p["independent_adjudicator_required"])
        self.assertFalse(p["statistical_precision_recall_claims_allowed_without_independent_gold"])
    def test_source_statuses_are_explicit_and_fail_closed(self):
        p=self.policy
        self.assertEqual(set(p["allowed_verdicts"]),{"VERIFIED","CONTRADICTED","UNVERIFIED","NOT_FACT_CLAIM"})
        self.assertIn("A search result",p["verified_rule"])
        self.assertIn("UNVERIFIED",p["completeness_rule"])
        self.assertFalse(p["p0_go"])
    def test_original_source_sha_and_excerpts_real(self):
        self.assertEqual(len(self.ledger["official_rule_anchors"]),2)
        for a in self.ledger["official_rule_anchors"]:
            self.assertTrue(ensure_official_anchor(a,(ROOT/a["path"]).read_bytes()))
    def test_nts_question_not_misclassified_as_true_speaker_fact(self):
        a=self.ledger["official_rule_anchors"][0]
        self.assertEqual(a["original_role"],"QUESTION")
        self.assertEqual(a["speaker_claim_verdict"],"NOT_FACT_CLAIM")
        self.assertFalse(a["effective_date_verified"])
        self.assertIsNone(a["published_at"])
        self.assertFalse(a["finance_fact_auto_approved"])
    def test_law_timed_rule_but_original_video_not_certified(self):
        a=self.ledger["official_rule_anchors"][1]
        self.assertEqual(a["effective_from"],"2026-10-01")
        self.assertEqual(a["speaker_claim_verdict"],"UNVERIFIED")
        self.assertFalse(self.ledger["video_level_legal_accuracy_certified"])
        self.assertEqual(self.ledger["verified_video_claim_count"],0)
        self.assertFalse(self.ledger["p0_go"])
    def test_wrong_source_bytes_rejected(self):
        a=self.ledger["official_rule_anchors"][1]
        with self.assertRaisesRegex(ValueError,"ORIGINAL_SOURCE_BYTES_DRIFT"):
            ensure_official_anchor(a,b"fake govt evidence")
    def test_host_and_http_downgrade_rejected(self):
        a=self.ledger["official_rule_anchors"][1]
        raw=(ROOT/a["path"]).read_bytes()
        with self.assertRaisesRegex(ValueError,"NOT_SECURE_PRIMARY_URL"):
            ensure_official_anchor(dict(a,url="http://www.law.go.kr/fake"),raw)
        with self.assertRaisesRegex(ValueError,"NOT_ALLOWLISTED_OFFICIAL_DOMAIN"):
            ensure_official_anchor(dict(a,url="https://example.com/fake"),raw)
    def test_false_visible_excerpt_rejected(self):
        a=self.ledger["official_rule_anchors"][1]
        raw=(ROOT/a["path"]).read_bytes()
        with self.assertRaisesRegex(ValueError,"OFFICIAL_EXCERPT_NOT_PRESENT"):
            ensure_official_anchor(dict(a,required_visible_phrases=["this phrase does not exist 35942"]),raw)
    def test_no_fake_statistical_accuracy_or_fact_go(self):
        self.assertIsNone(self.ledger["self_reported_precision_recall"])
        self.assertFalse(self.ledger["legacy116_semantic_merge_approved"])
        self.assertEqual(self.ledger["source_windows_verified_factual_claims"],0)
        self.assertFalse(self.ledger["human_review_required"])
        self.assertTrue(self.policy["legacy_v1_preserved_unchanged"])
if __name__=="__main__":
    unittest.main()
