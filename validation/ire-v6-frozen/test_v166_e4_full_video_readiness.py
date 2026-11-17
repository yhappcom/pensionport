"""Synthetic contract tests; actual private 13-child data is never in CI."""
import copy
import unittest
from v166_e4_full_video_readiness import audit_video_readiness,digest,h

def fixture():
    cues={1:"첫 사실을 검토합니다.",2:"조건부 위험을 질문합니다.",
          3:"정정이 필요한 사실입니다.",4:"투자와 무관한 끝 인사입니다."}
    raw="\n\n".join(f"{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},500\n{t}"
                      for i,t in cues.items()).encode()
    source=h(raw)
    segments=[]
    for j in range(2):
        first=2*j+1
        last=first+1
        plan={"source_sha256":source,"cue_count":4,
              "scope":{"first_cue":first,"last_cue":last}}
        atoms=[{"claim_id":f"C{i:05d}","context_cue_indices":[i],
                "source_refs":[{"cue_index":i,"quote":cues[i]}]}
               for i in range(first,last+1)]
        statuses=["ACCEPT_FOR_RESEARCH","OPEN"] if j==0 else [
            "OPEN","EXCLUDE_FROM_RESEARCH"]
        verdicts=[{"claim_id":a["claim_id"],"atom_sha256":digest(a),
                   "status":status,"high_risk":status=="OPEN"}
                  for a,status in zip(atoms,statuses)]
        event=digest(["event",j])
        bundle=digest(["bundle",j])
        review={"source_sha256":source,"manifest_sha256":digest(plan),
                "host_event_sha256":event,"host_bundle_sha256":bundle,
                "source_cues":[{"cue_index":i,"status":"REVIEWED",
                    "cue_text_sha256":h(cues[i].encode())}
                    for i in range(first,last+1)],
                "atom_verdicts":verdicts,
                "unresolved_high_risk_omissions":2 if j==0 else 1,
                "disagreements_adjudicated":False}
        segments.append({"segment_id":f"B{j+1:04d}","plan":plan,
                         "exchange":{"source_sha256":source,
                                     "manifest_sha256":digest(plan),
                                     "atoms":atoms},
                         "review":review,
                         "host":{"event_sha256":event,"bundle_sha256":bundle,
                                 "atomic_batch_committed":True}})
    return raw,cues,segments

class E4ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.raw,self.cues,self.segments=fixture()

    def run_audit(self):
        return audit_video_readiness(self.raw,self.cues,self.segments,
                                     expected_source_sha256=h(self.raw))

    def test_01_legacy_counts_not_independent_false_negatives(self):
        r=self.run_audit()
        self.assertEqual(r["source_cue_count"],4)
        self.assertEqual(r["distinct_claim_count"],4)
        self.assertEqual(r["totals"]["accepted_candidate_count"],1)
        self.assertEqual(r["totals"]["open_atom_count"],2)
        self.assertEqual(r["totals"]["open_high_risk_atom_count"],2)
        self.assertEqual(r["totals"]["legacy_unresolved_high_risk_omissions_field"],3)
        self.assertIsNone(r["actual_independent_high_risk_false_negative_count"])
        self.assertFalse(r["native_v123_approval_granted"])
        self.assertFalse(r["real_knowledge_publication_authorized"])

    def test_02_missing_source_tail(self):
        self.segments.pop()
        with self.assertRaisesRegex(ValueError,"TRAILING_SOURCE_GAP"):self.run_audit()

    def test_03_gap_or_overlap(self):
        self.segments[1]["plan"]["scope"]["first_cue"]=2
        with self.assertRaisesRegex(ValueError,"GAP_OR_OVERLAP"):self.run_audit()

    def test_04_external_owner_source_pin(self):
        with self.assertRaisesRegex(ValueError,"OWNER_SOURCE_PIN_MISMATCH"):
            audit_video_readiness(self.raw,self.cues,self.segments,
                                  expected_source_sha256="0"*64)

    def test_05_recomputed_fake_cue_hash_not_raw_text(self):
        self.cues[1]="위조된 원문"
        self.segments[0]["review"]["source_cues"][0]["cue_text_sha256"]=h(
            self.cues[1].encode())
        with self.assertRaisesRegex(ValueError,"CUE_MAP_NOT_RAW_SOURCE_TEXT"):
            self.run_audit()

    def test_06_review_host_revision_mismatch(self):
        self.segments[0]["review"]["host_event_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"FROZEN_SOURCE_MANIFEST_HOST"):
            self.run_audit()

    def test_07_atom_hash_tamper(self):
        self.segments[0]["exchange"]["atoms"][0]["source_refs"][0]["quote"]="위조"
        with self.assertRaisesRegex(ValueError,"ATOM_DIGEST_DRIFT"):self.run_audit()

    def test_08_rehashed_wrong_quote(self):
        a=self.segments[0]["exchange"]["atoms"][0];a["source_refs"][0]["quote"]="위조"
        self.segments[0]["review"]["atom_verdicts"][0]["atom_sha256"]=digest(a)
        with self.assertRaisesRegex(ValueError,"SOURCE_REF_DRIFT"):self.run_audit()

    def test_09_reused_claim_id_across_segments(self):
        a=self.segments[1]["exchange"]["atoms"][0]
        v=self.segments[1]["review"]["atom_verdicts"][0]
        a["claim_id"]="C00001";v["claim_id"]="C00001";v["atom_sha256"]=digest(a)
        with self.assertRaisesRegex(ValueError,"DUPLICATE_CROSS_SEGMENT"):self.run_audit()

    def test_10_other_segment_context_even_if_real_quote(self):
        a=self.segments[0]["exchange"]["atoms"][0]
        a["context_cue_indices"]=[3];a["source_refs"]=[{"cue_index":3,"quote":self.cues[3]}]
        self.segments[0]["review"]["atom_verdicts"][0]["atom_sha256"]=digest(a)
        with self.assertRaisesRegex(ValueError,"CONTEXT_SCOPE"):self.run_audit()

    def test_11_accepted_overlaps_quarantined_cue_is_exposed(self):
        self.segments[0]["review"]["source_cues"][0]["status"]="EXCLUDED_FROM_RESEARCH"
        r=self.run_audit()
        self.assertEqual(r["accepted_candidate_ids_touching_excluded_cue"],["C00001"])
        self.assertFalse(r["real_knowledge_publication_authorized"])

    def test_12_zero_counters_alone_never_authorize(self):
        for s in self.segments:
            s["review"]["unresolved_high_risk_omissions"]=0
            s["review"]["disagreements_adjudicated"]=True
            for v in s["review"]["atom_verdicts"]:
                if v["status"]=="OPEN":v["status"]="EXCLUDE_FROM_RESEARCH"
        r=self.run_audit()
        self.assertEqual(r["totals"]["open_atom_count"],0)
        self.assertIsNone(r["actual_independent_high_risk_false_negative_count"])
        self.assertFalse(r["real_knowledge_publication_authorized"])
        self.assertFalse(r["e5_authorized"])

if __name__=="__main__":unittest.main()
