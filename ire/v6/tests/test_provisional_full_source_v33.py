"""V33 synthetic-only source-census negative controls, NOT semantic gold."""
import copy,unittest
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.source import verify_source
from ire.v6.tests.test_source_and_proof import make_srt,make_manifest
from ire.v6.provisional_full_source_v33 import (
    draft_full_original_utterance_exchange_v33,audit_full_original_provisional_v33)

class FullOriginalDraftV33Tests(unittest.TestCase):
    def setUp(self):
        self.raw=make_srt(['ISA 기간 3년입니다.','연금 조건이면 20만 원이 달라집니다.',
                           '그렇죠.','IRP 수령은 언제 할까요?'])
        self.manifest=make_manifest(self.raw,cut=2)
        self.src=verify_source(self.raw,self.manifest,
            expected_source_sha256=sha256(self.raw),expected_manifest_sha256=json_digest(self.manifest))
        self.ex,self.stats=draft_full_original_utterance_exchange_v33(self.src)

    def test_original_four_cues_are_explicitly_dispositioned_not_semantic_gold(self):
        a=audit_full_original_provisional_v33(self.src,self.ex,expected_window_count=2)
        self.assertEqual(a['original_cue_count'],4)
        self.assertEqual(a['cue_dispositions_audited'],4)
        self.assertGreaterEqual(a['provisional_utterance_candidates'],2)
        self.assertFalse(a['all_original_utterances_semantically_atomic'])
        self.assertFalse(a['chat_meaning_review_completed'])
        self.assertFalse(a['p0_go'])

    def test_all_atoms_are_unresolved_and_speaker_unidentified(self):
        self.assertTrue(all(a['stance']=='UNRESOLVED' and a['speaker']=='UNKNOWN' for a in self.ex['atoms']))

    def test_source_cue_was_deleted_rejected(self):
        x=copy.deepcopy(self.ex)
        x['cue_dispositions'].pop()
        with self.assertRaises(InvalidInput):audit_full_original_provisional_v33(self.src,x)

    def test_fake_original_quote_rejected(self):
        x=copy.deepcopy(self.ex)
        x['atoms'][0]['source_refs'][0]['quote']='NOT THE ORIGINAL CUE'
        with self.assertRaises(InvalidInput):audit_full_original_provisional_v33(self.src,x)

    def test_premature_fact_approval_rejected(self):
        x=copy.deepcopy(self.ex)
        x['atoms'][0]['stance']='AFFIRMED'
        with self.assertRaises(InvalidInput):audit_full_original_provisional_v33(self.src,x)

    def test_wrong_window_census_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V33_WHOLE_SOURCE_WINDOW_COUNT_DRIFT'):
            audit_full_original_provisional_v33(self.src,self.ex,expected_window_count=3)

    def test_partial_scope_rejected(self):
        m=make_manifest(self.raw,scope_first=2,scope_last=4,mode='PARTIAL',cut=2)
        s=verify_source(self.raw,m,expected_source_sha256=sha256(self.raw),
                         expected_manifest_sha256=json_digest(m))
        with self.assertRaisesRegex(InvalidInput,'V33_FULL_SOURCE_REQUIRED'):
            draft_full_original_utterance_exchange_v33(s)

    def test_numeric_only_cue_cannot_be_discarded_as_no_atom(self):
        raw=make_srt(['여기 숫자는', '3', '투자 관련', '장기 계획입니다.'])
        m=make_manifest(raw,cut=2)
        s=verify_source(raw,m,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(m))
        ex,_=draft_full_original_utterance_exchange_v33(s)
        with self.assertRaisesRegex(InvalidInput,'V33_RISKY_OR_NUMERIC_NO_ATOM_REQUIRES_REVIEW'):
            audit_full_original_provisional_v33(s,ex)

    def test_segment_cap_bound_rejected(self):
        with self.assertRaisesRegex(InvalidInput,'V33_PROVISIONAL_SEGMENT_LIMIT_INVALID'):
            draft_full_original_utterance_exchange_v33(self.src,max_cues=1)

    def test_cue_divided_money_unit_does_not_invent_verbatim_number(self):
        raw=make_srt(['금액은 25만','원에 해당합니다.','기간은 7%로 12년입니다.','다른 가정도 합니다.'])
        m=make_manifest(raw,cut=2)
        s=verify_source(raw,m,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(m))
        ex,_=draft_full_original_utterance_exchange_v33(s)
        proof=audit_full_original_provisional_v33(s,ex)
        self.assertEqual(proof['original_cue_count'],4)
        self.assertFalse(proof['complete_original_claim_recall_certified'])

if __name__=='__main__':unittest.main()
