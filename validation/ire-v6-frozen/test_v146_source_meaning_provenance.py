"""V146 synthetic semantic provenance guard regression, not owner-video final approval."""
from __future__ import annotations
import copy
import unittest
from pathlib import Path
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.tests import test_host_batch as host_fixture
from v146_source_meaning_provenance import (audit_source_meaning_provenance,
                                           _source_anchor_hash,SCHEMA)


def sh(x): return sha256(x.encode('utf-8'))

class TestV146UnknownSpeakerSafety(unittest.TestCase):
    def setUp(self):
        self.base=host_fixture.HostBatchTests('test_one_command_commits_all_models_and_proofs_atomically')
        self.base.setUp()
        self.addCleanup(self.base.doCleanups)
        self.source=self.base.fx.source
        self.exchange=copy.deepcopy(self.base.fx.exchange)
        self.exchange['atoms'][0]['speaker']='UNKNOWN'
        self.exchange['atoms'][0]['stance']='UNRESOLVED'
        self.claim=self.exchange['atoms'][0]
        self.rows=[{'claim_id':a['claim_id'],'status':'ACCEPT_FOR_RESEARCH'} for a in self.exchange['atoms']]
        self.review={'atom_verdicts':self.rows}

    def signed(self):
        atom=self.claim
        indices=sorted(set(atom['context_cue_indices']))
        return {'schema':SCHEMA,'source_sha256':self.source.source_sha256,
                'manifest_sha256':self.source.manifest_sha256,
                'review_executor':'CHATGPT_IN_CHAT',
                'private_chat_source_meaning_sha256':sh('synthetic bounded reviewer note'),
                'atom_rows':[{'claim_id':atom['claim_id'],'atom_sha256':json_digest(atom),
                    'source_cue_indices':indices,
                    'source_context_sha256':_source_anchor_hash(self.source,indices),
                    'resolved_speaker_role':'UNATTRIBUTED_VIDEO_SPEAKER',
                    'resolved_speech_act':'ASSERTION','speaker_identity_not_inferred':True,
                    'source_condition_exception_checked':True,
                    'private_review_note_sha256':sh('synthetic source claim note')}]}

    def test_01_cannot_accept_unknown_without_pinned_meaning_note(self):
        with self.assertRaisesRegex(InvalidInput,'LEDGER_REQUIRED_FOR_ACCEPTED_UNKNOWN'):
            audit_source_meaning_provenance(self.source,self.exchange,self.review)

    def test_02_explicit_source_bound_unnamed_voice_not_factual_authentication(self):
        self.review['source_meaning_provenance']=self.signed()
        r=audit_source_meaning_provenance(self.source,self.exchange,self.review)
        self.assertEqual(r['source_identity_unresolved_claims_reviewed'],1)
        self.assertFalse(r['external_source_authenticity_certified'])
        self.assertFalse(r['independent_semantic_accuracy_certified'])

    def test_03_forged_owner_srt_or_manifest_digest_fails(self):
        for field in ('source_sha256','manifest_sha256'):
            q=self.signed();q[field]='0'*64
            with self.subTest(field=field),self.assertRaises(InvalidInput):
                audit_source_meaning_provenance(self.source,self.exchange,
                    {'atom_verdicts':self.rows,'source_meaning_provenance':q})

    def test_04_forged_atom_digest_fails(self):
        q=self.signed();q['atom_rows'][0]['atom_sha256']='1'*64
        with self.assertRaises(InvalidInput):
            audit_source_meaning_provenance(self.source,self.exchange,
                {'atom_verdicts':self.rows,'source_meaning_provenance':q})

    def test_05_partial_source_cues_are_not_accepted(self):
        q=self.signed();q['atom_rows'][0]['source_cue_indices']=[]
        with self.assertRaises(InvalidInput):
            audit_source_meaning_provenance(self.source,self.exchange,
                {'atom_verdicts':self.rows,'source_meaning_provenance':q})

    def test_06_changing_original_cue_sha_fails(self):
        q=self.signed();q['atom_rows'][0]['source_context_sha256']='0'*64
        with self.assertRaises(InvalidInput):
            audit_source_meaning_provenance(self.source,self.exchange,
                {'atom_verdicts':self.rows,'source_meaning_provenance':q})

    def test_07_bogus_book_quote_role_and_question_fails(self):
        q=self.signed();q['atom_rows'][0].update(
            resolved_speaker_role='SOURCE_BOOK_QUOTE',resolved_speech_act='QUESTION')
        with self.assertRaises(InvalidInput):
            audit_source_meaning_provenance(self.source,self.exchange,
                {'atom_verdicts':self.rows,'source_meaning_provenance':q})

    def test_08_source_first_context_and_no_invented_identity_required(self):
        for field in ('speaker_identity_not_inferred','source_condition_exception_checked'):
            q=self.signed();q['atom_rows'][0][field]=False
            with self.subTest(field=field),self.assertRaises(InvalidInput):
                audit_source_meaning_provenance(self.source,self.exchange,
                    {'atom_verdicts':self.rows,'source_meaning_provenance':q})

    def test_09_exact_accepted_unresolved_claim_census(self):
        q=self.signed();self.rows[0]['status']='OPEN'
        with self.assertRaises(InvalidInput):
            audit_source_meaning_provenance(self.source,self.exchange,
                {'atom_verdicts':self.rows,'source_meaning_provenance':q})
        # After OPEN, no optional ledger needed and no source claim is accepted.
        self.assertIsNone(audit_source_meaning_provenance(self.source,self.exchange,self.review))

    def test_10_legacy_fully_resolved_synthetic_fixture_remains_compatible(self):
        original=self.base.fx.exchange
        r=audit_source_meaning_provenance(self.source,original,
            {'atom_verdicts':[{'claim_id':a['claim_id'],'status':'ACCEPT_FOR_RESEARCH'}
                              for a in original['atoms']]})
        self.assertIsNone(r)

    def test_11_gate_integration_import_and_call_present(self):
        f=(Path(__file__).parent/'v123_chat_final_gate.py')
        self.assertTrue(f.exists())
        txt=f.read_text(encoding='utf-8')
        self.assertIn('audit_source_meaning_provenance(source, exchange, chat_review)',txt)
        self.assertIn('source_unknown_speaker_stance_accepted_claims_checked',txt)

if __name__=='__main__': unittest.main(verbosity=2)
