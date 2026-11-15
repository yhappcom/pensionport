"""V123.3 current chat-last policy/document/code consistency (no private SRT)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
PROTOCOL = BASE / 'V6_CURRENT_CHATGPT_FINAL_APPROVAL_PROTOCOL.md'
REPORT = BASE / 'V6_V123_CHATGPT_FINAL_REVIEW_GATE_REPORT.md'
POLICY = BASE / 'V123_CHATGPT_FINAL_REVIEW_POLICY.json'
V119 = BASE / 'V119_CHAT_NATIVE_REVIEW_GOVERNANCE.md'
GATE = BASE / 'v123_chat_final_gate.py'
PREVIEW = BASE / 'v123_chat_validated_knowledge_preview.py'


class ChatFinalProtocolDocs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = PROTOCOL.read_text(encoding='utf-8')
        cls.report = REPORT.read_text(encoding='utf-8')
        cls.v119 = V119.read_text(encoding='utf-8')
        cls.policy = json.loads(POLICY.read_text(encoding='utf-8'))
        cls.gate = GATE.read_text(encoding='utf-8')
        cls.preview = PREVIEW.read_text(encoding='utf-8')

    def test_current_protocol_is_linked_from_v123_report(self):
        self.assertIn('V6_CURRENT_CHATGPT_FINAL_APPROVAL_PROTOCOL.md', self.report)

    def test_current_protocol_is_linked_from_v119(self):
        self.assertIn('V6_CURRENT_CHATGPT_FINAL_APPROVAL_PROTOCOL.md', self.v119)

    def test_current_protocol_is_machine_policy_canonical(self):
        self.assertEqual(self.policy['canonical_operating_standard'],
                         'validation/ire-v6-frozen/V6_CURRENT_CHATGPT_FINAL_APPROVAL_PROTOCOL.md')

    def test_chat_is_final_executor_no_external_reviewer(self):
        self.assertEqual(self.policy['user_selected_final_review_executor'], 'CHATGPT_IN_CHAT')
        self.assertIs(self.policy['external_reviewer_required'], False)
        self.assertIn('ChatGPT 채팅이 최종 품질 검토자', self.protocol)

    def test_ci_never_approves_by_itself(self):
        self.assertIs(self.policy['engine_ci_cannot_approve_research'], True)
        self.assertIn('소프트웨어 PASS는', self.protocol)

    def test_all_original_cues_and_atomic_claims(self):
        self.assertIs(self.policy['requires_all_original_cues_and_atom_claims_reviewed'], True)
        self.assertIn('전체 원본 cue', self.protocol)
        self.assertIn('각 원자 주장', self.protocol)

    def test_finance_requires_actual_primary_bytes_and_date(self):
        self.assertIs(self.policy['requires_private_primary_official_document_bytes_replay_for_finance_pass'], True)
        self.assertIs(self.policy['hash_without_body_is_open'], True)
        self.assertIn('실제 바이트의 해시 재검증', self.protocol)
        self.assertIn('sha256(original_body)', self.gate)

    def test_current_store_and_real_host_batch_required(self):
        self.assertIs(self.policy['requires_current_v6_owner_store_head_and_window_proofs'], True)
        self.assertIn('HOST_STORE_STALE_OR_PROOF_NOT_COMMITTED', self.gate)

    def test_required_holds_and_rejections_documented(self):
        for status in ('HOLD_MISSING_V6_HOST_BATCH_OR_STORE',
                       'HOLD_MISSING_CHAT_FINAL_REVIEW', 'CHAT_FINAL_HOLD_OPEN',
                       'CHAT_FINAL_REJECTED', 'CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY'):
            self.assertIn(status, self.protocol)

    def test_actual_gate_exports_only_candidates(self):
        self.assertIn('require_chat_final_release', self.preview)
        self.assertIn('require_chat_final_release(', self.preview)
        self.assertIn('research_candidate_export_allowed', self.gate)
        self.assertIn('P1 읽기 전용', self.protocol)
        self.assertIs(self.policy['financial_fact_formal_approval_automatically_granted'], False)

    def test_no_automatic_master_p4_or_personal_advice(self):
        self.assertIs(self.policy['master116_p4_auto_merge'], False)
        self.assertIs(self.policy['personal_investment_advice_auto_approved'], False)
        self.assertIn('개인 투자자문', self.protocol)

    def test_same_chat_is_not_external_gold(self):
        self.assertIs(self.policy['same_chat_review_is_externally_independent'], False)
        self.assertIn('독립 블라인드', self.protocol)

    def test_real_v122_hold_not_falsely_released(self):
        self.assertEqual(self.policy['V122_source_cues'], 47)
        self.assertEqual(self.policy['V122_financial_open'], 12)
        self.assertIs(self.policy['V122_actual_v6_owner_host_batch_complete'], False)
        self.assertIs(self.policy['V122_chat_final_pass'], False)
        self.assertIn('금융 OPEN 12건', self.protocol)

    def test_frozen_core_not_modified_or_misdocumented(self):
        self.assertIs(self.policy['frozen_core_ire_v6_source_tree_untouched'], True)
        self.assertFalse((ROOT / 'ire/v6/chat_final_gate.py').exists())
        self.assertFalse((ROOT / 'ire/v6/chat_validated_knowledge_preview.py').exists())
        self.assertNotIn('`ire/v6/chat_final_gate.py`:', self.report)
        self.assertNotIn('`ire/v6/chat_validated_knowledge_preview.py`:', self.report)

    def test_code_paths_exist_and_match_policy(self):
        for name in ('gate','readonly_p1_entrypoint','unit_tests'):
            path = self.policy['implementation'][name]
            self.assertTrue((ROOT/path).is_file(), path)
            self.assertIn(path, self.protocol)

    def test_no_false_full_go(self):
        self.assertIs(self.policy['p0_go'], False)
        self.assertIn('P0 `NO_GO`', self.protocol)


if __name__ == '__main__':
    unittest.main()
