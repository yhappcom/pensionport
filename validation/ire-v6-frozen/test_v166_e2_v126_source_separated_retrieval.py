"""E2 actual V126 private-knowledge retrieval cannot conflate speaker and reviewer.

The synthetic V128 parent first publishes, then E2 joins attested original
cue text and source-only caution into a safe research context. NO real owner,
financial original, independent meaning gold or investment advice in this test.
"""
from __future__ import annotations
import copy
import json
import sqlite3
import unittest
from unittest.mock import patch

from ire.v6.codec import json_digest,sha256
from ire.v6.errors import InvalidInput
from ire.v6.tests.test_atomic_exchange import HostAtomExchangeTests
from test_v128_continuous_chat_atomic_parent import V128HostRunAndAtomicParentTests
from v146_source_meaning_provenance import SCHEMA as V146_SCHEMA, _source_anchor_hash
from v166_e2_semantic_separation import (
    SCHEMA, source_separated_evidence_for_question,
)


class V166E2ActualV126SafeAnswerContext(unittest.TestCase):
    def setUp(self):
        original_sample=HostAtomExchangeTests.sample

        def unknown_speaker_source(test_case):
            ex=original_sample(test_case)
            for atom in ex["atoms"]:
                atom["speaker"]="UNKNOWN"
            return ex

        self.fx=V128HostRunAndAtomicParentTests(
            "test_01_two_native_v6_children_seam_and_atomic_private_parent_publication")
        with patch.object(HostAtomExchangeTests,"sample",unknown_speaker_source):
            self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        # Frozen V146 demands explicit provenance for every accepted V6 atom
        # whose speaker is UNKNOWN. This is a synthetic reviewer provenance
        # fixture, not audio authentication and not independent semantic gold.
        for packet in self.fx.packets:
            case=packet["case"]
            atoms={a["claim_id"]:a for a in case["exchange"]["atoms"]}
            selected=[v["claim_id"] for v in case["chat_review"]["atom_verdicts"]
                      if v["status"]=="ACCEPT_FOR_RESEARCH"
                      and atoms[v["claim_id"]]["speaker"]=="UNKNOWN"]
            if selected:
                rows=[]
                for cid in selected:
                    atom=atoms[cid]
                    indices=sorted(set(atom["context_cue_indices"]))
                    rows.append({
                        "claim_id":cid,"atom_sha256":json_digest(atom),
                        "source_cue_indices":indices,
                        "source_context_sha256":_source_anchor_hash(
                            case["source"],indices),
                        "resolved_speaker_role":"UNATTRIBUTED_VIDEO_SPEAKER",
                        "resolved_speech_act":"ASSERTION",
                        "speaker_identity_not_inferred":True,
                        "source_condition_exception_checked":True,
                        "private_review_note_sha256":
                            sha256(("synthetic reviewed unknown "+cid).encode("utf-8")),
                    })
                case["chat_review"]["source_meaning_provenance"]={
                    "schema":V146_SCHEMA,
                    "source_sha256":case["source"].source_sha256,
                    "manifest_sha256":case["source"].manifest_sha256,
                    "review_executor":"CHATGPT_IN_CHAT",
                    "atom_rows":rows,
                    "private_chat_source_meaning_sha256":
                        sha256(b"synthetic V146 ChatGPT input, not owner audio")
                }
        self.case=self.fx.packets[0]["case"]
        self.source=self.case["source"]
        self.exchange=self.case["exchange"]
        self.rows=[]
        for atom in self.exchange["atoms"]:
            idx=atom["source_refs"][0]["cue_index"]
            original=self.source.cues[idx-1].text
            contexts=sorted(set(atom["context_cue_indices"]))
            note=("이 문장은 원문 화자의 주장과 검토자의 외부 원전 및 "
                  "개인 적용 제한을 엄격히 분리해야 하며 어떤 숫자도 "
                  "확정 금융 성과나 법적 유효성으로 자동 승인하지 않습니다.")
            row={
                "claim_id":atom["claim_id"],
                "atom_sha256":json_digest(atom),
                "source_speech_type":"FINANCIAL_ASSERTION",
                "source_context_cue_indices":contexts,
                "source_context_sha256":json_digest([
                    {"cue_index":i,
                     "cue_text_sha256":sha256(self.source.cues[i-1].text.encode("utf-8"))}
                    for i in contexts]),
                "verbatim_cue_index":idx,
                "verbatim_excerpt":original,
                "source_speaker_identity":"UNKNOWN_NOT_AUDIO_AUTHENTICATED",
                "original_condition_cue_indices":atom["condition_cue_indices"],
                "original_exception_cue_indices":atom["exception_cue_indices"],
                "source_speech_summary":"원본 금융 자막의 수치 설명을 문맥에 따라 검토합니다.",
                "reviewer_caution_note":note,
                "reviewer_note_sha256":sha256(note.encode("utf-8")),
                "reviewer_caution_not_original_speaker_quote":True,
                "fact_dependencies":[{
                    "cue_index":idx,"verbatim_excerpt":original,
                    "status":"OPEN_PRIMARY_REQUIRED",
                    "reviewer_note_sha256":sha256(note.encode("utf-8"))}],
                "numeric_token_roles":[{
                    "cue_index":r["cue_index"],
                    "token":r["token"],
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
            "private_review_note_sha256":sha256(b"synthetic mock ChatGPT review"),
            "semantic_accuracy_independent_gold_certified":False,
            "personal_advice_approved":False,
        }

    def _publish_and_select(self, claim_id="C00001"):
        published=self.fx.run_engine()
        self.assertEqual(published["publication_receipt"]["entry_count"],3)
        with sqlite3.connect(self.fx.knowledge.path) as conn:
            rows=[json.loads(r[0]) for r in conn.execute("SELECT entry_json FROM knowledge")]
        matches=[r["knowledge_id"] for r in rows if r["claim_id"]==claim_id]
        self.assertEqual(len(matches),1)
        return matches

    def test_01_real_v126_retrieval_strips_mixed_proposition(self):
        ids=self._publish_and_select()
        got=source_separated_evidence_for_question(
            self.fx.knowledge,"수익에 관한 위험 질문",
            source=self.source,exchange=self.exchange,ledger=self.ledger,
            selected_knowledge_ids=ids)
        self.assertEqual(got["count"],1)
        self.assertFalse(got["reviewed_financial_facts_authorized"])
        self.assertTrue(got["requires_live_official_source_recheck"])
        self.assertTrue(got["chatgpt_final_answer_review_required"])
        item=got["claims"][0]
        self.assertNotIn("atom",item)
        self.assertNotIn("proposition",item)
        self.assertFalse(item["legacy_mixed_proposition_exposed_to_answer_generator"])
        self.assertEqual(item["reviewer_role"],"CHATGPT_CAUTION_NOT_ORIGINAL_SPEAKER_QUOTE")
        self.assertIn(item["source_verbatim_quote"],
                      self.source.cues[item["source_quote_cue_index"]-1].text)
        self.assertNotEqual(item["reviewer_caution"],item["source_verbatim_quote"])
        self.assertFalse(got["personalized_advice_auto_approved"])

    def test_02_second_video_scope_without_matching_e2_custody_fails(self):
        ids=self._publish_and_select(claim_id="C00003")
        with self.assertRaises(InvalidInput):
            source_separated_evidence_for_question(
                self.fx.knowledge,"수익에 관한 위험 질문",
                source=self.source,exchange=self.exchange,ledger=self.ledger,
                selected_knowledge_ids=ids)

    def test_03_wrong_reviewer_note_digest_blocks_approved_retrieval(self):
        ids=self._publish_and_select()
        ledger=copy.deepcopy(self.ledger)
        ledger["rows"][0]["reviewer_note_sha256"]="0"*64
        with self.assertRaises(InvalidInput):
            source_separated_evidence_for_question(
                self.fx.knowledge,"수익에 관한 위험 질문",
                source=self.source,exchange=self.exchange,ledger=ledger,
                selected_knowledge_ids=ids)

    def test_04_no_source_quote_downgrade_from_legacy_atom_proposition(self):
        ids=self._publish_and_select()
        ledger=copy.deepcopy(self.ledger)
        legacy_atom=self.exchange["atoms"][0]
        ledger["rows"][0]["verbatim_excerpt"]=legacy_atom["proposition"]
        with self.assertRaises(InvalidInput):
            source_separated_evidence_for_question(
                self.fx.knowledge,"수익에 관한 위험 질문",
                source=self.source,exchange=self.exchange,ledger=ledger,
                selected_knowledge_ids=ids)


if __name__=="__main__":
    unittest.main()
