"""Ensure the real-user-turn E3 contract remains discoverable and overrides legacy phrasing."""
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
POLICY = 'V193_E3_TWO_ACTUAL_USER_TURNS_MANDATORY_PROTOCOL_20261120.md'


class TestTwoTurnOperatingDocumentation(unittest.TestCase):
    def test_01_root_readme_links_current_operating_contract(self):
        s = (REPO/'README.md').read_text(encoding='utf-8')
        self.assertIn('validation/ire-v6-frozen/' + POLICY, s)
        self.assertIn('별개의 사용자 메시지', s)

    def test_02_root_readme_overrides_protected_v3_one_turn_history(self):
        # ire/README.md is protected historical V3 documentation: do not edit it.
        s = (REPO/'README.md').read_text(encoding='utf-8')
        self.assertIn(POLICY, s)
        self.assertIn('과거 V3 한 턴', s)
        self.assertIn('최신 V6 E3', s)

    def test_03_e3_policy_clearly_distinguishes_two_turns_from_batches(self):
        s = (HERE/POLICY).read_text(encoding='utf-8')
        for phrase in ('턴 1: 연구 실행', '턴 2: 최종 의미 검증', '별개의 두 사용자 명령',
                       '별개의 사용자 대화 턴이 아니다', 'E3 HOLD', 'V123/E4', 'E5=0'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, s)

    def test_04_historical_e3_comparison_report_warns_not_actual_two_turns(self):
        s = (HERE/'V192_E3_TRIPLE_CLAIM_ALIGNMENT_INTERNAL_REFERENCE_HOLD_20261120.md').read_text(encoding='utf-8')
        self.assertIn(POLICY, s)
        self.assertIn('실제 사용자 명령 2턴', s)

    def test_05_v183_experiment_report_references_v193_correction(self):
        s = (HERE/'V183_E3_TWO_TURN_BLIND_SOURCE_COMPARE_AND_ACTUAL_16CUE_HOLD_20261120.md').read_text(encoding='utf-8')
        self.assertIn(POLICY, s)
        self.assertIn('별도 사용자 명령', s)


if __name__ == '__main__':
    unittest.main()