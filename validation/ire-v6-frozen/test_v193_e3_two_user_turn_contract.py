"""Synthetic tests that prevent an E3 second-pass batch being called another user turn."""
import copy
import unittest
from ire.v6.errors import InvalidInput
from v193_e3_two_user_turn_contract import validate_manual_turn_receipt, SCHEMA

A = 'a' * 64
B = 'b' * 64
C = 'c' * 64
D = 'd' * 64
E = 'e' * 64


class TestTwoUserTurnContract(unittest.TestCase):
    def setUp(self):
        self.first = dict(phase='RESEARCH_AND_FREEZE', user_message_ref='user:message-1',
                          user_message_sha256=C, source_sha256=A, owner_head_sha256=B,
                          research_frozen=True)
        self.second = dict(phase='CHATGPT_FINAL_SEMANTIC_VERIFICATION',
                           user_message_ref='user:message-2', user_message_sha256=D,
                           source_sha256=A, owner_head_sha256=B,
                           review_recorded=True, review_head_sha256=E)

    def call(self, **kwargs):
        return validate_manual_turn_receipt(first=self.first, second=self.second,
                                            source_sha256=A, owner_head_sha256=B,
                                            **kwargs)

    def test_01_first_command_only_blocks_final_review(self):
        r = validate_manual_turn_receipt(first=self.first, second=None,
                                         source_sha256=A, owner_head_sha256=B,
                                         batch_count=250)
        self.assertEqual(r['phase'], 'AWAIT_SEPARATE_USER_VERIFICATION_COMMAND')
        self.assertFalse(r['two_user_turns_proven'])
        self.assertFalse(r['e3_semantic_accuracy_certified'])
        self.assertEqual(r['batch_count'], 250)

    def test_02_distinct_caller_refs_are_not_host_verified(self):
        r = self.call(batch_count=15)
        self.assertEqual(r['schema'], SCHEMA)
        self.assertEqual(r['recorded_distinct_user_commands'], 2)
        self.assertFalse(r['host_separate_turns_verified'])
        self.assertFalse(r['two_user_turns_proven'])
        self.assertFalse(r['e3_semantic_accuracy_certified'])

    def test_03_same_message_ref_rejected_even_for_two_processes(self):
        self.second['user_message_ref'] = self.first['user_message_ref']
        with self.assertRaisesRegex(InvalidInput, 'SAME_USER_COMMAND'):
            self.call(batch_count=15)

    def test_04_identical_message_text_may_be_separate_user_turns(self):
        # The user may say '진행해 주세요' twice; same text is NOT same user message.
        self.second['user_message_sha256'] = self.first['user_message_sha256']
        receipt = self.call()
        self.assertEqual(receipt['recorded_distinct_user_commands'], 2)
        self.assertFalse(receipt['host_separate_turns_verified'])

    def test_05_research_continuation_cannot_be_final_review(self):
        self.second['phase'] = 'RESEARCH_AND_FREEZE'
        with self.assertRaisesRegex(InvalidInput, 'SECOND_NOT_FINAL_REVIEW'):
            self.call()

    def test_06_first_not_frozen_rejected(self):
        self.first['research_frozen'] = False
        with self.assertRaisesRegex(InvalidInput, 'FIRST_PHASE_NOT_FROZEN'):
            self.call()

    def test_07_checkpoint_mismatch_rejected(self):
        self.second['owner_head_sha256'] = E
        with self.assertRaisesRegex(InvalidInput, 'SECOND_SOURCE_OR_FROZEN_HEAD_MISMATCH'):
            self.call()

    def test_08_no_second_review_result_rejected(self):
        self.second['review_head_sha256'] = ''
        with self.assertRaisesRegex(InvalidInput, 'SECOND_USER_OR_REVIEW_EVIDENCE_MISSING'):
            self.call()

    def test_09_independent_gold_forgery_rejected(self):
        with self.assertRaisesRegex(InvalidInput, 'NO_AUTHORITY_TO_APPROVE'):
            self.call(independent_gold_certified=True)

    def test_10_e3_approval_forgery_rejected(self):
        with self.assertRaisesRegex(InvalidInput, 'NO_AUTHORITY_TO_APPROVE'):
            self.call(e3_approved=True)

    def test_11_e4_or_e5_approval_forgery_rejected(self):
        for props in (dict(v123_e4_approved=True), dict(e5_published=True)):
            with self.subTest(props=props), self.assertRaisesRegex(InvalidInput, 'NO_AUTHORITY_TO_APPROVE'):
                self.call(**props)

    def test_12_missing_phase_receipt_field_rejected(self):
        del self.second['review_recorded']
        with self.assertRaisesRegex(InvalidInput, 'SECOND_RECEIPT_SCHEMA'):
            self.call()

    def test_13_second_ref_is_not_a_process_id(self):
        self.second['user_message_ref'] = 'process:12345'
        with self.assertRaisesRegex(InvalidInput, 'SECOND_USER_OR_REVIEW_EVIDENCE_MISSING'):
            self.call()

    def test_14_user_ref_lexical_form_does_not_create_host_proof(self):
        self.second['user_message_ref'] = 'user:made-up-message-ref'
        receipt = self.call()
        self.assertFalse(receipt['host_separate_turns_verified'])
        self.assertFalse(receipt['two_user_turns_proven'])


if __name__ == '__main__':
    unittest.main()