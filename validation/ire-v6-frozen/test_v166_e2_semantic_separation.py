"""E2 source/reviewer separation and negative controls. All data synthetic."""
import copy
import unittest

from ire.v6.codec import sha256,json_digest
from ire.v6.errors import InvalidInput
from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
from v166_e2_semantic_separation import SCHEMA,audit_e2_semantic_ledger,build_e2_source_separated_context_packet,audit_e2_cross_atom_discourse


class V166E2SourceAndReviewerSeparationTests(unittest.TestCase):
    def setUp(self):
        self.fx=HostAtomExchangeTests("test_all_cues_number_context_and_stance_bound_but_not_semantic_gold")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.source=self.fx.source
        self.exchange=copy.deepcopy(self.fx.exchange)
        self.rows=[]
        for atom in self.exchange["atoms"]:
            atom["speaker"]="UNKNOWN"
            indices=sorted(set(atom["context_cue_indices"]))
            idx=atom["source_refs"][0]["cue_index"]
            original=self.source.cues[idx-1].text
            note=("검토자가 외부 금융근거와 개인 적용 조건을 추가로 확인해야 하며 "
                  "원문 화자가 제공하지 않은 보장이나 예외를 발언으로 위장하지 않습니다.")
            row={
                "claim_id":atom["claim_id"],
                "atom_sha256":json_digest(atom),
                "source_speech_type":"FINANCIAL_ASSERTION",
                "source_context_cue_indices":indices,
                "source_context_sha256":json_digest([
                    {"cue_index":i,"cue_text_sha256":sha256(self.source.cues[i-1].text.encode("utf-8"))}
                    for i in indices]),
                "verbatim_cue_index":idx,
                "verbatim_excerpt":original,
                "source_speaker_identity":"UNKNOWN_NOT_AUDIO_AUTHENTICATED",
                "original_condition_cue_indices":atom["condition_cue_indices"],
                "original_exception_cue_indices":atom["exception_cue_indices"],
                "source_speech_summary":"이 영상에서 금융 관련 주장을 실제로 소개합니다.",
                "reviewer_caution_note":note,
                "reviewer_note_sha256":sha256(note.encode("utf-8")),
                "reviewer_caution_not_original_speaker_quote":True,
                "fact_dependencies":[{
                    "cue_index":idx,"verbatim_excerpt":original,
                    "status":"OPEN_PRIMARY_REQUIRED",
                    "reviewer_note_sha256":sha256(note.encode("utf-8"))}],
                "numeric_token_roles":[{
                    "cue_index":r["cue_index"],"token":r["token"],
                    "role":"FINANCIAL_QUANTITY_UNVERIFIED"}
                    for r in atom["numeric_references"]],
                "chat_source_reviewed":True,
                "investment_effectiveness_certified":False,
                "personal_advice_approved":False,
                "independent_gold_certified":False,
            }
            self.rows.append(row)
        self.ledger={
            "schema":SCHEMA,
            "source_sha256":self.source.source_sha256,
            "manifest_sha256":self.source.manifest_sha256,
            "review_executor":"CHATGPT_IN_CHAT",
            "as_of":"2026-11-17",
            "rows":self.rows,
            "private_review_note_sha256":sha256(b"private ChatGPT synthetic E2 notes"),
            "semantic_accuracy_independent_gold_certified":False,
            "personal_advice_approved":False,
        }

    def audit(self,ledger=None,exchange=None):
        return audit_e2_semantic_ledger(self.source,exchange or self.exchange,
                                        ledger or self.ledger)

    def test_01_all_source_and_reviewer_layers_and_conditions_accounted(self):
        result=self.audit()
        self.assertEqual(result["checked_atom_count"],3)
        self.assertEqual(result["conditioned_atoms_accounted"],1)
        self.assertEqual(result["unverified_embedded_factual_dependencies"],3)
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["independent_recall_certified"])

    def test_02_missing_condition_is_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][2]["original_condition_cue_indices"]=[]
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_03_source_quote_tampering_is_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["verbatim_excerpt"]="가짜 투자 원문 20%"
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_04_source_context_cue_digest_tampering_is_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][1]["source_context_sha256"]="0"*64
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_05_missing_factual_dependency_is_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["fact_dependencies"]=[]
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_06_source_and_reviewer_cannot_be_merged(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["reviewer_caution_not_original_speaker_quote"]=False
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_07_asr_numeric_or_finance_token_cannot_disappear(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["numeric_token_roles"]=[]
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_08_forged_numerical_token_is_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][1]["numeric_token_roles"][0]["token"]="80%"
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_09_cannot_claim_independent_gold_or_personal_advice(self):
        l=copy.deepcopy(self.ledger)
        l["semantic_accuracy_independent_gold_certified"]=True
        with self.assertRaises(InvalidInput):self.audit(ledger=l)
        l["semantic_accuracy_independent_gold_certified"]=False
        l["rows"][0]["personal_advice_approved"]=True
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_10_mixed_opinion_embedded_facts_require_source_refs(self):
        e=copy.deepcopy(self.exchange)
        l=copy.deepcopy(self.ledger)
        a=e["atoms"][0]
        a["kind"]="OPINION"
        l["rows"][0]["atom_sha256"]=json_digest(a)
        l["rows"][0]["source_speech_type"]="MIXED_OPINION_WITH_FACTUAL_DEPENDENCY"
        self.assertEqual(self.audit(ledger=l,exchange=e)["checked_atom_count"],3)
        l["rows"][0]["fact_dependencies"]=[]
        with self.assertRaises(InvalidInput):self.audit(ledger=l,exchange=e)

    def test_11_factual_assertion_cannot_be_unilaterally_retyped_as_opinion(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["source_speech_type"]="PERSONAL_OPINION"
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_12_missing_one_atom_cannot_be_called_full_review(self):
        l=copy.deepcopy(self.ledger)
        l["rows"].pop()
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_14_quoted_principle_keeps_verifiable_source_dependency(self):
        e=copy.deepcopy(self.exchange)
        l=copy.deepcopy(self.ledger)
        a=e["atoms"][0]
        a["kind"]="OPINION"
        l["rows"][0]["atom_sha256"]=json_digest(a)
        l["rows"][0]["source_speech_type"]="QUOTED_SOURCE_PRINCIPLE"
        self.assertEqual(self.audit(ledger=l,exchange=e)["checked_atom_count"],3)
        l["rows"][0]["fact_dependencies"]=[]
        with self.assertRaises(InvalidInput):self.audit(ledger=l,exchange=e)

    def test_15_e2_cannot_self_certify_primary_original_evidence(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["fact_dependencies"][0]["status"]="PRIMARY_VERIFIED_SEPARATELY"
        with self.assertRaises(InvalidInput):self.audit(ledger=l)

    def test_16_source_quote_and_chat_review_note_never_merge_in_context(self):
        packet=build_e2_source_separated_context_packet(
            self.source,self.exchange,self.ledger)
        self.assertEqual(packet["entry_census"],3)
        self.assertFalse(packet["knowledge_publication_authorized"])
        self.assertFalse(packet["final_chat_semantic_approval_authorized"])
        for item in packet["entries"]:
            self.assertIn(item["source_verbatim_quote"],
                          self.source.cues[item["source_quote_cue_index"]-1].text)
            self.assertEqual(item["reviewer_role"],
                             "CHATGPT_CAUTION_NOT_ORIGINAL_SPEAKER_QUOTE")
            self.assertFalse(item["legacy_v6_proposition_exported_as_speaker_quote"])
            self.assertNotIn(item["reviewer_caution"],item["source_verbatim_quote"])
            self.assertTrue(all(dep["evidence_status"] == "OPEN_PRIMARY_REQUIRED"
                                for dep in item["unverified_fact_dependencies"]))

    def test_17_review_risk_cannot_be_rebranded_as_original_speaker_quote(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["verbatim_excerpt"]=l["rows"][0]["reviewer_caution_note"]
        with self.assertRaises(InvalidInput):
            build_e2_source_separated_context_packet(self.source,self.exchange,l)

    def test_18_no_legacy_proposition_as_speaker_quote(self):
        # The V6 proposition is deliberately a mixture of paraphrase and
        # reviewer caution, so it cannot be used as an exact source quotation.
        packet=build_e2_source_separated_context_packet(
            self.source,self.exchange,self.ledger)
        for item in packet["entries"]:
            original=next(x for x in self.exchange["atoms"]
                          if x["claim_id"] == item["claim_id"])
            self.assertNotEqual(item["source_verbatim_quote"],
                                original["proposition"])

    def _discourse_fixture(self):
        idx=2
        quote=self.source.cues[idx-1].text
        note=("원문 두 발언의 대비 관계만 확인하며 서로 다른 주장 사이의 "
              "차이를 실제 금융 손익 보장이나 공식적 반증으로 승인하지 않습니다.")
        return {
            "schema":"IRE_V166_E2_CROSS_ATOM_DISCOURSE_V1",
            "source_sha256":self.source.source_sha256,
            "review_executor":"CHATGPT_IN_CHAT",
            "rows":[{
                "left_claim_id":"C00001","right_claim_id":"C00002",
                "relation_type":"CONTRAST","source_cue_index":idx,
                "source_quote":quote,
                "source_cue_sha256":sha256(quote.encode("utf-8")),
                "chat_meaning_note":note,
                "chat_meaning_note_sha256":sha256(note.encode("utf-8")),
                "source_checked":True,"financial_fact_verified":False,
            }],
            "private_chat_review_sha256":sha256(b"synthetic review notes"),
            "financial_fact_auto_approved":False,
        }

    def test_19_cross_atom_contrast_remains_source_pinned(self):
        d=self._discourse_fixture()
        result=audit_e2_cross_atom_discourse(
            self.source,self.exchange,self.ledger,d)
        self.assertEqual(result["cross_atom_relations_verified"],1)
        self.assertEqual(result["source_conditions_preserved"],1)
        self.assertFalse(result["research_knowledge_release_authorized"])

    def test_20_forged_cross_atom_contrast_quote_rejected(self):
        d=self._discourse_fixture()
        d["rows"][0]["source_quote"]="원문에 없는 허위 금융 보장 문구"
        with self.assertRaises(InvalidInput):
            audit_e2_cross_atom_discourse(self.source,self.exchange,self.ledger,d)

    def test_21_cross_atom_claim_id_substitution_rejected(self):
        d=self._discourse_fixture()
        d["rows"][0]["right_claim_id"]="C99999"
        with self.assertRaises(InvalidInput):
            audit_e2_cross_atom_discourse(self.source,self.exchange,self.ledger,d)

    def test_22_false_financial_factual_certification_rejected(self):
        d=self._discourse_fixture()
        d["rows"][0]["financial_fact_verified"]=True
        with self.assertRaises(InvalidInput):
            audit_e2_cross_atom_discourse(self.source,self.exchange,self.ledger,d)

    def test_13_unauthenticated_speaker_name_rejected(self):
        l=copy.deepcopy(self.ledger)
        l["rows"][0]["source_speaker_identity"]="PRESENTER"
        with self.assertRaises(InvalidInput):self.audit(ledger=l)


if __name__=="__main__":
    unittest.main()
