"""Actual 1195-cue private first-video source-first tax adjudication public-safe replay.

Original SRT is private; this CI does NOT reconstruct, download, or independently
validate the original cue text. It verifies official text byte identity and
case-decision safety for the 12 privately inspected atom candidates.
"""
import hashlib,json,re,subprocess,unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[2]
PATH=Path(__file__).with_name("ACTUAL_HIGH_RISK_TAX_CLAIM_DISPOSITIONS_V2.json")
class Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.fragments=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):self.skip+=1
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript"):self.skip=max(0,self.skip-1)
    def handle_data(self,text):
        if not self.skip:self.fragments.append(text)

def normalized(s):return re.sub(r"\s+","",s)

def validate_doc(doc):
    if not doc["url"].startswith("https://"):
        raise ValueError("REQUIRES_FIRST_PARTY_HTTPS")
    host=doc["url"].split("/")[2]
    if host not in ("nts.go.kr","www.law.go.kr"):
        raise ValueError("OFFICIAL_ISSUER_HOST_UNKNOWN")
    raw=(ROOT/doc["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=doc["sha256"]:
        raise ValueError("PINNED_SOURCE_RAW_BYTES_CHANGED")
    parser=Visible()
    parser.feed(raw.decode("utf-8",errors="replace"))
    txt=normalized("".join(parser.fragments))
    for phrase in doc["verified_visible_phrases"]:
        if normalized(phrase) not in txt:
            raise ValueError("OFFICIAL_TEXT_ENTAILMENT_CANDIDATE_NOT_PRESENT")
    if doc["id"]=="LAW-40-3" and doc["effective_date"]!="2026-10-01":
        raise ValueError("WRONG_LAW_EFFECTIVE_VERSION")
    if doc["id"]=="NTS-1500" and doc["effective_date"]!="UNKNOWN_ON_PAGE":
        raise ValueError("FABRICATED_NTS_PUBLICATION_DATE")

def check_cases(report):
    cases=report["cases"]
    if len(cases)!=12 or len({x["id"] for x in cases})!=12:
        raise ValueError("DUPLICATE_OR_MISSING_REAL_CASE")
    source=report["original_source_sha256"]
    if source!="2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f":
        raise ValueError("REAL_PRIVATE_SOURCE_ID_DRIFT")
    statuses={"VERIFIED","UNVERIFIED","CONTRADICTED","NOT_FACT_CLAIM"}
    ids={x["id"] for x in report["official_documents"]}
    for c in cases:
        if not (1<=c["first_cue"]<=c["last_cue"]<=1195):
            raise ValueError("BAD_ORIGINAL_SOURCE_CUE")
        if (not re.fullmatch(r"W\d{5}",c["first_window"]) or
            not re.fullmatch(r"W\d{5}",c["last_window"])):
            raise ValueError("ORIGINAL_WINDOW_BINDING_BAD")
        if not re.fullmatch(r"[0-9a-f]{64}",c["private_quote_sha256"]):
            raise ValueError("ORIGINAL_PRIVATE_QUOTE_DIGEST_BAD")
        if c["official_rule_id"] not in ids or c["verdict"] not in statuses:
            raise ValueError("BAD_OFFICIAL_REFERENCE_OR_VERDICT")
        if c["private_verbatim_in_github"] or not c["semantic_check_performed_privately"]:
            raise ValueError("PRIVATE_ORIGINAL_MUST_REMAIN_SEPARATE")
        if c["role"]=="QUESTION" and c["verdict"]!="NOT_FACT_CLAIM":
            raise ValueError("QUESTION_TO_FACT_LAUNDERING")
        if c["verdict"]=="VERIFIED":
            if c["role"]!="FACT" or c["official_rule_id"]!="LAW-40-3":
                raise ValueError("FALSE_VERIFIED_FACT")
            if not c["fact_release_allowed"] or "section 201-10" not in c["review_note"]:
                raise ValueError("MATERIAL_LEGAL_CONDITIONS_OMITTED")
        if c["verdict"]=="UNVERIFIED" and (c["fact_release_allowed"] or not c["critical_unresolved"]):
            raise ValueError("UNVERIFIED_FACT_AUTO_RELEASE")
    counts={k:sum(c["verdict"]==k for c in cases) for k in statuses}
    if counts!={"VERIFIED":1,"UNVERIFIED":5,"CONTRADICTED":0,"NOT_FACT_CLAIM":6}:
        raise ValueError("FALSE_CASE_COMPLETENESS")
    if report["all_critical_tax_claims_resolved"] or report["final_p0_go"]:
        raise ValueError("CRITICAL_TAX_ERRORS_NOT_CLOSED")
    if report["full_video_67_windows_semantic_exhaustiveness_verified"]:
        raise ValueError("FALSE_FULL_VIDEO_COVERAGE")
    if report["github_can_replay_private_srt"] or report["private_srt_bytes_or_quotes_published_to_github"]:
        raise ValueError("PRIVACY_OR_EVIDENCE_SCOPE_BREACH")
    return True

class RealTaxV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(PATH.read_text(encoding="utf-8"))
    def test_law_and_nts_byte_exact_originals_with_visible_2026_rule(self):
        for x in self.d["official_documents"]:validate_doc(x)
    def test_original_private_cue_hash_and_roles_are_fail_closed(self):
        check_cases(self.d)
    def test_67_real_windows_are_only_lexically_screened_not_semantically_finished(self):
        self.assertEqual(self.d["first_video_original_cue_count"],1195)
        self.assertEqual(self.d["historical_v5_windows"],67)
        self.assertEqual(self.d["all_historical_windows_lexically_screened"],67)
        self.assertEqual(self.d["windows_flagged_by_keyword_for_tax_or_pension_followup"],59)
        self.assertEqual(self.d["windows_intersecting_manual_case_review"],8)
        self.assertFalse(self.d["full_video_67_windows_semantic_exhaustiveness_verified"])
    def test_actual_116_originals_and_relation_are_open(self):
        p=ROOT/"data/claims.jsonl"
        sha=subprocess.check_output(["git","hash-object",str(p)],text=True).strip()
        self.assertEqual(sha,self.d["master116_blob_sha"])
        claims=[json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]
        self.assertEqual(len(claims),116)
        self.assertEqual(len([c for c in claims if "sz5N9WJS310" in c["supporting_videos"]]),0)
        self.assertEqual(self.d["candidate_prior_relation_verdict"],"OPEN_NOT_APPROVED")
        self.assertTrue(any(c["claim_id"]=="GOMHEE-C78" for c in claims))
    def test_false_claim_promotion_rejected(self):
        d=json.loads(json.dumps(self.d))
        d["cases"][0]["verdict"]="VERIFIED"
        with self.assertRaisesRegex(ValueError,"QUESTION_TO_FACT_LAUNDERING"):check_cases(d)
        d=json.loads(json.dumps(self.d))
        d["cases"][1]["verdict"]="VERIFIED"
        with self.assertRaisesRegex(ValueError,"FALSE_VERIFIED_FACT"):check_cases(d)
    def test_unsupported_claim_cannot_escape_by_self_approval(self):
        d=json.loads(json.dumps(self.d))
        d["cases"][2]["fact_release_allowed"]=True
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_FACT_AUTO_RELEASE"):check_cases(d)
    def test_fake_official_document_rejected(self):
        d=json.loads(json.dumps(self.d["official_documents"][1]))
        d["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"PINNED_SOURCE_RAW_BYTES_CHANGED"):validate_doc(d)
    def test_false_issuer_publication_date_rejected(self):
        d=json.loads(json.dumps(self.d["official_documents"][0]))
        d["effective_date"]="2026-11-08"
        with self.assertRaisesRegex(ValueError,"FABRICATED_NTS_PUBLICATION_DATE"):validate_doc(d)
    def test_score_not_manipulated_by_partial_scope(self):
        self.assertEqual((self.d["evidence_score_before"],self.d["evidence_score_delta"],self.d["evidence_score_after"]),(60,0,60))
        self.assertFalse(self.d["full_model_semantic_accuracy_measured"])
        self.assertEqual(self.d["verified_fact_cases"],1)
        self.assertEqual(self.d["unverified_fact_cases"],5)
        self.assertEqual(self.d["correctly_nonfact_cases"],6)
if __name__=="__main__":unittest.main()
