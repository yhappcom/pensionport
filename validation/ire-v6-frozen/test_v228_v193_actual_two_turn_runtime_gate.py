"""Public synthetic-only actual two-user-turn protocol tests, no owner data."""
import copy, json, os, tempfile, unittest, zipfile
from pathlib import Path
from ire.v6.errors import InvalidInput
from test_v227_e2_source_semantic_reconciliation import synthetic
from v228_v193_actual_two_turn_runtime_gate import (
    audit_study, research_first_turn_rows, freeze_turn1_private,
    verify_turn1_frozen,prepare_turn2_source_only_review,
    reject_final_approval_without_trusted_evidence,SCHEMA,digest)

USER1='정확히 명시하고 작업을 이어서 진행해 주세요'
USER2='이전에 동결한 원본을 최종 검토해 주세요'

def make_input(docs,tmp,**overrides):
    args={'source_raw':docs['srt'],'native_raw':docs['native'],
       'cue_raw':docs['source_triage'],'e3_raw':docs['canonical_e3'],
       'pairs_raw':docs['all_pairs'],
       'first_user_ref':'user:manual-message-1-not-host-authenticated',
       'first_user_text':USER1, 'private_zip':tmp/'first.zip','window_size':20}
    args.update(overrides);return args

def pins(r,p):return {'private_zip':p,'externally_pinned_zip_sha256':r['private_zip_sha256'],
    'externally_pinned_manifest_sha256':r['manifest_sha256'],
    'externally_pinned_first_head_sha256':r['owner_first_turn_head_sha256'],
    'externally_pinned_source_sha256':r['source_sha256']}

class TestV228ActualTwoUserTurn(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.d=Path(self.tmp.name);self.docs,*_=synthetic()
        self.args=make_input(self.docs,self.d)
        self.frozen=freeze_turn1_private(**self.args)
        self.pins=pins(self.frozen,self.args['private_zip'])

    def verify(self,**changes):
        return verify_turn1_frozen(**dict(self.pins,**changes))

    def test_01_first_turn_phase_is_frozen_and_second_not_started(self):
        self.assertEqual(self.frozen['status'],'TURN1_FROZEN_AWAIT_DISTINCT_USER_TURN2')
        self.assertEqual(self.frozen['original_cues'],8)
        self.assertEqual(self.frozen['native_drafts'],3)
        self.assertEqual(self.frozen['chat_turns_completed'],1)
        self.assertFalse(self.frozen['platform_message_provenance_verified'])
        self.assertFalse(self.frozen['e3_final_approved'])

    def test_02_frozen_owner_zip_reopens_only_if_pins_match(self):
        r=self.verify();self.assertEqual(r['audit']['source_claim_pairs'],3)
        self.assertEqual(r['phase'],'AWAIT_SEPARATE_USER_VERIFICATION_COMMAND')

    def test_03_manual_first_user_ref_does_not_claim_host_authority(self):
        x=self.verify()['turn1_receipt'];self.assertTrue(x['research_frozen'])
        self.assertTrue(x['user_message_ref'].startswith('user:'))
        self.assertFalse(self.verify()['study']['host_message_id_verified'])

    def test_04_turn2_same_message_ref_rejected(self):
        with self.assertRaises(InvalidInput):self.start(second_user_ref=self.args['first_user_ref'])

    def test_05_turn2_not_observed_by_chat_host_rejected(self):
        with self.assertRaises(InvalidInput):self.start(current_actual_user_message_observed=False)

    def test_06_separate_user_message_opens_source_only_not_gold(self):
        x=self.start();self.assertEqual(len(x['source_only_cues']),8)
        self.assertFalse(x['host_two_turns_verified'])
        self.assertFalse(x['prior_candidate_propositions_visible_to_reviewer'])
        self.assertFalse(x['independent_gold_certified'])
        self.assertFalse(x['final_e3_approved'])

    def test_07_turn2_new_command_with_same_text_can_still_be_distinct(self):
        x=self.start(second_user_text=USER1)
        self.assertNotEqual(x['turn1_manual_user_ref'],x['turn2_manual_user_ref'])

    def test_08_first_turn_freeze_cannot_be_overwritten(self):
        with self.assertRaises(InvalidInput):freeze_turn1_private(**self.args)

    def test_09_wrong_zip_digest_fails_closed(self):
        with self.assertRaises(InvalidInput):self.verify(externally_pinned_zip_sha256='0'*64)

    def test_10_wrong_manifest_digest_fails_closed(self):
        with self.assertRaises(InvalidInput):self.verify(externally_pinned_manifest_sha256='0'*64)

    def test_11_wrong_head_digest_fails_closed(self):
        with self.assertRaises(InvalidInput):self.verify(externally_pinned_first_head_sha256='0'*64)

    def test_12_wrong_source_digest_fails_closed(self):
        with self.assertRaises(InvalidInput):self.verify(externally_pinned_source_sha256='0'*64)

    def test_13_missing_archive_does_not_create_new_research(self):
        with self.assertRaises(InvalidInput):self.verify(private_zip=self.d/'missing.zip')

    def test_14_archive_tamper_rejected(self):
        p=self.args['private_zip'];p.write_bytes(p.read_bytes()+b'malicious')
        with self.assertRaises(InvalidInput):self.verify()

    def test_15_archive_permissions_open_to_other_users_rejected(self):
        p=self.args['private_zip'];p.chmod(0o644)
        with self.assertRaises(InvalidInput):self.verify()

    def test_16_fake_host_verified_cannot_be_accepted(self):
        self.assertFalse(self.verify()['manifest']['two_user_turns_host_verified'])
        with self.assertRaises(InvalidInput):reject_final_approval_without_trusted_evidence(e3_final_approved=True)

    def test_17_e4_emergency_override_forbidden(self):
        with self.assertRaises(InvalidInput):reject_final_approval_without_trusted_evidence(e4_approved=True)

    def test_18_e5_direct_publishing_forbidden(self):
        with self.assertRaises(InvalidInput):reject_final_approval_without_trusted_evidence(e5_published=True)

    def test_19_first_user_bad_ref_rejected(self):
        args=make_input(self.docs,self.d,first_user_ref='batch:fake',private_zip=self.d/'bad.zip')
        with self.assertRaises(InvalidInput):freeze_turn1_private(**args)

    def test_20_false_native_financial_truth_rejected(self):
        native=json.loads(self.docs['native']);native['atoms'][0]['proposition']='가짜 바뀐 원자'
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],json.dumps(native).encode(),
            self.docs['source_triage'],self.docs['canonical_e3'],self.docs['all_pairs'])

    def test_21_false_e3_claim_finance_approval_rejected(self):
        e3=json.loads(self.docs['canonical_e3']);e3['task_rows'][0]['financial_fact_approved']=True
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],self.docs['native'],
            self.docs['source_triage'],json.dumps(e3).encode(),self.docs['all_pairs'])

    def test_22_false_gold_pairwise_rejected(self):
        pairs=json.loads(self.docs['all_pairs']);pairs['rows'][0]['independently_verified_exact_equivalence']=True
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],self.docs['native'],
            self.docs['source_triage'],self.docs['canonical_e3'],json.dumps(pairs).encode())

    def test_23_cue_quote_tamper_rejected(self):
        cues=json.loads(self.docs['source_triage']);cues['rows'][0]['source_quote']='허위'
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],self.docs['native'],
             json.dumps(cues).encode(),self.docs['canonical_e3'],self.docs['all_pairs'])

    def test_24_media_task_context_not_list_rejected(self):
        e3=json.loads(self.docs['canonical_e3']);e3['task_rows'][2]['source_context']={'bad':'object'}
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],self.docs['native'],
            self.docs['source_triage'],json.dumps(e3).encode(),self.docs['all_pairs'])

    def test_25_bad_window_manifest_rejected(self):
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],self.docs['native'],
            self.docs['source_triage'],self.docs['canonical_e3'],self.docs['all_pairs'],window_size=1)

    def test_26_missing_pair_record_rejected(self):
        pairs=json.loads(self.docs['all_pairs']);pairs['rows'].pop()
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],self.docs['native'],
            self.docs['source_triage'],self.docs['canonical_e3'],json.dumps(pairs).encode())

    def test_27_duplicate_cue_class_in_ledger_rejected(self):
        cues=json.loads(self.docs['source_triage']);cues['rows'].append(cues['rows'][0])
        with self.assertRaises(InvalidInput):audit_study(self.docs['srt'],self.docs['native'],
             json.dumps(cues).encode(),self.docs['canonical_e3'],self.docs['all_pairs'])

    def test_28_declared_first_turn_source_is_not_independent_gold(self):
        r=research_first_turn_rows(self.docs['srt'],self.docs['native'],
                self.docs['source_triage'],self.docs['canonical_e3'],self.docs['all_pairs'],
                first_user_ref='user:manual1',first_user_text=USER1)
        self.assertTrue(r['old_v227_candidates_supplied_as_context'])
        self.assertFalse(r['all_source_claims_independently_measured'])
        self.assertFalse(r['e3_review_run_in_this_turn'])

    def test_29_review_only_e3_gate_is_still_hold(self):
        self.assertEqual(reject_final_approval_without_trusted_evidence(),
            {'e3_final_approved':False,'e4_approved':False,'e5_published':False})

    def start(self,**changes):
        args=dict(self.pins,second_user_ref='user:manually-observed-message-2',
            second_user_text=USER2,current_actual_user_message_observed=True)
        args.update(changes)
        return prepare_turn2_source_only_review(**args)

if __name__=='__main__':unittest.main()