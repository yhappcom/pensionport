"""V37 deterministic synthetic-only custody tests, never semantic accuracy gold."""
import copy
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from ire.v6.source_window_host_screen_v37 import audit_full_source_firstpass_v37
from ire.v6.errors import InvalidInput
from ire.v6.codec import sha256

class V37FirstPassScreenTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'private.zip'
        self.vid='ABCDEFGHIJK'; self.raw=b'1\n00:00:00,000 --> 00:00:01,000\nThis is an example sentence.\n\n2\n00:00:01,000 --> 00:00:02,000\nWe can discuss outcomes.\n\n3\n00:00:02,000 --> 00:00:03,000\nOK\n'
        with zipfile.ZipFile(self.path,'w') as z:z.writestr('1-70/youtube-transcript-'+self.vid+'.srt',self.raw)
        self.archive_sha256=sha256(self.path.read_bytes())
        self.sources=[{'video_no':1,'video_id':self.vid,'original_srt_sha256':sha256(self.raw),'cue_count':3}]
        self.claims=[{'video_no':1,'video_id':self.vid,'claim_id':'C00001','window_id':'W00001','cues':[1,2],
            'source_text':'This is an example sentence. | We can discuss outcomes.',
            'source_text_sha256':sha256(b'This is an example sentence. | We can discuss outcomes.'),
            'risk_tax':False,'risk_market':False,'qualifier':False,'numeric_tokens':0,
            'review_priority':0,'question_mark':False}]
        self.notes=[{'video_no':1,'window_no':1,'themes':['Sample dialogue in synthetic source'],
                     'financial_risks':['Do not invent an investment conclusion'],
                     'source_speech_roles':['Non-financial statement example'],
                     'current_evidence':['No official finance claim is certified'],
                     'evidence_state':'CHAT_CONTEXT_REVIEWED_NOT_CERTIFIED',
                     'full_atomic_claims_certified':False}]
        self.kw={'archive_sha256':self.archive_sha256,'sources':self.sources,
                 'candidate_registry':self.claims,'host_window_notes':self.notes,
                 'externally_unverified_case_ids':['a'*64]}
    def tearDown(self):self.tmp.cleanup()
    def audit(self,**kw):
        d={**self.kw,**kw};return audit_full_source_firstpass_v37(self.path,**d)
    def test_source_bound_screen_pass_not_semantic_gold(self):
        x=self.audit();self.assertEqual(x['totals']['source_windows'],1)
        self.assertEqual(x['totals']['provisional_utterances'],1)
        self.assertEqual(x['totals']['short_no_candidate_cues'],1)
        self.assertFalse(x['all_1603_utterances_semantically_atomized'])
        self.assertFalse(x['all_130_windows_financial_meaning_claims_certified'])
        self.assertFalse(x['p0_go'])
    def test_source_is_absent_from_public_receipt(self):
        x=str(self.audit());self.assertNotIn('This is an example sentence.',x)
        self.assertNotIn('Sample dialogue',x)
    def test_bad_zip_digest_fails(self):
        with self.assertRaisesRegex(InvalidInput,'V37_OWNER_ZIP_PIN_MISMATCH'):self.audit(archive_sha256='0'*64)
    def test_bad_srt_digest_fails(self):
        s=copy.deepcopy(self.sources);s[0]['original_srt_sha256']='0'*64
        with self.assertRaisesRegex(InvalidInput,'V37_OWNER_SRT_SHA_CHANGED'):self.audit(sources=s)
    def test_missing_window_review_fails(self):
        with self.assertRaisesRegex(InvalidInput,'V37_130_SOURCE_WINDOWS_MISSING_CHAT_NOTE'):self.audit(host_window_notes=[])
    def test_duplicate_window_review_fails(self):
        with self.assertRaisesRegex(InvalidInput,'V37_MISSING_OR_DUPLICATE_CHAT_WINDOW_NOTE'):self.audit(host_window_notes=self.notes*2)
    def test_forged_full_atomic_completion_fails(self):
        n=copy.deepcopy(self.notes);n[0]['full_atomic_claims_certified']=True
        with self.assertRaisesRegex(InvalidInput,'V37_FALSE_ATOMIC_COMPLETION_REVIEW_STATUS'):self.audit(host_window_notes=n)
    def test_unaudited_note_evidence_fails(self):
        n=copy.deepcopy(self.notes);n[0]['current_evidence']=[]
        with self.assertRaisesRegex(InvalidInput,'V37_CHAT_NOTE_EMPTY_OR_WEAK'):self.audit(host_window_notes=n)
    def test_candidate_quote_tampering_fails(self):
        c=copy.deepcopy(self.claims);c[0]['source_text']='altered'
        with self.assertRaisesRegex(InvalidInput,'V37_SOURCE_DRAFT_TEXT_HASH_MISMATCH'):self.audit(candidate_registry=c)
    def test_duplicate_cue_ownership_fails(self):
        c=copy.deepcopy(self.claims);clone=copy.deepcopy(c[0]);clone['claim_id']='C00002';c.append(clone)
        with self.assertRaisesRegex(InvalidInput,'V37_ORIGINAL_CUE_DUPLICATE_UTTERANCE_OWNERSHIP'):self.audit(candidate_registry=c)
    def test_numeric_source_token_must_match(self):
        c=copy.deepcopy(self.claims);c[0]['numeric_tokens']=1
        with self.assertRaisesRegex(InvalidInput,'V37_NUMERIC_OR_QUESTION_SOURCE_SCOPE_MISMATCH'):self.audit(candidate_registry=c)
    def test_open_evidence_docket_id_must_be_sha256(self):
        with self.assertRaisesRegex(InvalidInput,'V37_EXTERNAL_EVIDENCE_ID_SCHEMA_INVALID'):
            self.audit(externally_unverified_case_ids=['historic CMA 2.85 percent'])
    def test_expected_source_census_mismatch_fails(self):
        with self.assertRaisesRegex(InvalidInput,'V37_EXACT_PRIVATE_COHORT_CENSUS_DRIFT'):
            self.audit(expected_counts={'original_cues':5129})
    def test_realistically_numeric_no_candidate_is_not_silently_ignored(self):
        # The existing short ack becomes a numeric original cue in synthetic ZIP
        other=self.raw.replace(b'OK\n',b'5%\n')
        path=Path(self.tmp.name)/'private2.zip'
        with zipfile.ZipFile(path,'w') as z:z.writestr('1-70/youtube-transcript-'+self.vid+'.srt',other)
        with self.assertRaisesRegex(InvalidInput,'V37_NUMERIC_OR_HIGH_RISK_CUE_DROPPED_AS_FILLER'):
            audit_full_source_firstpass_v37(path,archive_sha256=sha256(path.read_bytes()),
              sources=[{**self.sources[0],'original_srt_sha256':sha256(other)}],
              candidate_registry=self.claims,host_window_notes=self.notes,
              externally_unverified_case_ids=[])
if __name__=='__main__':unittest.main()
