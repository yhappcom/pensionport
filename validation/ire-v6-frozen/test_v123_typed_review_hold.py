"""Synthetic regression of the V123 common checker and typed HOLD ceiling.

Private real store/official capture replay is tested separately, not part of CI.
"""
import copy
import unittest
from ire.v6.codec import json_digest,sha256
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.errors import InvalidInput
from ire.v6.host_quarantine_preflight import audit_host_quarantine_preflight
from ire.v6.tests.test_host_typed_premise_staging import fixture
from v123_chat_final_gate import (_assess_chat_review, _audit_typed_review_notes,
    assess_typed_chat_final_gate, _is_finance, SCHEMA)


class TypedReviewHoldTests(unittest.TestCase):
    def setUp(self):
        self.s,self.e,self.l=fixture()
        self.pin=audit_host_quarantine_preflight(self.s,self.e,self.l)
        self.audit=audit_host_atomic_exchange(self.s,self.e)
        self.host={'event_sha256':'a'*64,'bundle_sha256':'b'*64,
                   'host_source_prequarantine_pin':self.pin}
        self.notes={'scope_note':'Synthetic test only.',
                    'source_cues':[{'cue_index':c.index,'cue_text_sha256':sha256(c.text.encode()),'status':'REVIEWED','note':'source inspected'} for c in self.s.cues],
                    'atom_verdicts':[{'claim_id':a['claim_id'],'atom_sha256':json_digest(a),'status':'OPEN','note':'pending'} for a in self.e['atoms']]}
        self.review=dict(schema=SCHEMA,review_executor='CHATGPT_IN_CHAT',as_of='2026-11-26',
            source_sha256=self.s.source_sha256,manifest_sha256=self.s.manifest_sha256,
            host_event_sha256=self.host['event_sha256'],host_bundle_sha256=self.host['bundle_sha256'],
            atom_candidate_digest=self.audit['atom_candidate_digest'],cue_disposition_digest=self.audit['cue_disposition_digest'],
            blindness='PRIOR_EXPOSED',source_first_pass_completed=True,counterexample_pass_completed=False,
            disagreements_adjudicated=False,unresolved_high_risk_omissions=0,unresolved_audio_visual=0,
            external_independent_certified=False,personalized_advice_approved=False,p0_go=False,
            review_private_evidence_sha256=json_digest(self.notes),
            source_cues=[{'cue_index':c.index,'cue_text_sha256':sha256(c.text.encode()),'status':'REVIEWED',
                          'review_note_sha256':json_digest(n)} for c,n in zip(self.s.cues,self.notes['source_cues'])],
            atom_verdicts=[])
        for a,n in zip(self.e['atoms'],self.notes['atom_verdicts']):
            f=_is_finance(a,self.s)
            self.review['atom_verdicts'].append(dict(claim_id=a['claim_id'],atom_sha256=json_digest(a),
                status='OPEN',speaker_stance_checked=False,conditions_exceptions_checked=False,
                numeric_period_checked=False,counterexample_checked=False,high_risk=True,financial_claim=f,
                finance_evidence_status='OPEN' if f else 'NOT_APPLICABLE',official_body_sha256=None,
                official_effective_as_of=None,financial_scope_checked=False,private_review_note_sha256=json_digest(n)))

    def assess(self):
        return _assess_chat_review(self.s,self.e,self.audit,self.host,self.review,{},typed_pin=self.pin)

    def test_support_retained_as_reviewed_no_export(self):
        r=self.assess()
        self.assertEqual(r['status'],'CHAT_FINAL_HOLD_TYPED_TRANSITION')
        self.assertEqual((r['cues_reviewed'],r['atoms_open']),(2,1))
        self.assertFalse(r['research_candidate_export_allowed'])
        self.assertFalse(r['p0_go'])
        _audit_typed_review_notes(self.review,self.notes)

    def test_missing_atom(self):
        self.review['atom_verdicts']=[]
        with self.assertRaisesRegex(InvalidInput,'CHAT_ATOM_CENSUS'): self.assess()

    def test_changed_host(self):
        self.review['host_event_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'WRONG_FROZEN_SOURCE_OR_HOST'): self.assess()

    def test_typed_cannot_accept(self):
        self.review['atom_verdicts'][0].update(status='ACCEPT_FOR_RESEARCH',speaker_stance_checked=True,
            conditions_exceptions_checked=True,numeric_period_checked=True,counterexample_checked=True)
        with self.assertRaisesRegex(InvalidInput,'TYPED_REVIEW_NOT_RELEASE_OR_EXCLUSION'): self.assess()

    def test_typed_cannot_exclude(self):
        self.review['atom_verdicts'][0]['status']='EXCLUDE_FROM_RESEARCH'
        with self.assertRaisesRegex(InvalidInput,'TYPED_REVIEW_NOT_RELEASE_OR_EXCLUSION'): self.assess()

    def test_quarantine_cannot_be_released(self):
        self.pin['quarantined_cue_indices']=[1]
        with self.assertRaisesRegex(InvalidInput,'TYPED_REVIEW_QUARANTINE_CANNOT_RESOLVE'): self.assess()

    def test_typed_cannot_self_promote_finance(self):
        self.review['atom_verdicts'][0].update(financial_claim=True,finance_evidence_status='PRIMARY_BODY_AND_DATE_CHAT_CHECKED',
                official_body_sha256='a'*64,official_effective_as_of='2026-11-26',financial_scope_checked=True)
        with self.assertRaisesRegex(InvalidInput,'TYPED_REVIEW_FINANCE_CANNOT_SELF_PROMOTE'): self.assess()

    def test_note_body_required_and_bound(self):
        self.notes['scope_note']='changed'
        with self.assertRaisesRegex(InvalidInput,'TYPED_REVIEW_PRIVATE_NOTES_DRIFT'):
            _audit_typed_review_notes(self.review,self.notes)
        self.review['review_private_evidence_sha256']=json_digest(self.notes)
        self.notes['source_cues'][0]['note']='changed'
        self.review['review_private_evidence_sha256']=json_digest(self.notes)
        with self.assertRaisesRegex(InvalidInput,'TYPED_REVIEW_NOTE_ROW_DRIFT'):
            _audit_typed_review_notes(self.review,self.notes)

    def test_fake_store_not_accepted(self):
        with self.assertRaisesRegex(InvalidInput,'TYPED_REVIEW_NATIVE_STORE_REQUIRED'):
            assess_typed_chat_final_gate(object(),scope_id='scope',run_id='run',expected_head='a'*64,
                raw=b'',manifest={},inventory_bytes=b'',expected_inventory_sha256='a'*64,
                chat_review=self.review,review_notes=self.notes)
