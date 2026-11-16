"""Synthetic source-only V117 edge tests and SHA-only real public census.

All synthetic clauses are invented. NO owner-private subtitle or research memo.
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from v117_source_complete_atomic_guard import (
    V117SourceProofError,audit_private_original,guard_public_v117_receipt)
from v115_full_video_bridge import parse_exact_srt,sha

SRT=(
"1\n00:00:01,000 --> 00:00:02,000\nExample fund first premise.\n\n"
"2\n00:00:03,000 --> 00:00:04,000\nAssume a regulatory threshold.\n\n"
"3\n00:00:05,000 --> 00:00:06,000\nThis threshold has conditions.\n\n"
"4\n00:00:07,000 --> 00:00:08,000\nA specific exception applies.\n\n"
"5\n00:00:09,000 --> 00:00:10,000\nA different asset type is exempt.\n\n"
"6\n00:00:11,000 --> 00:00:12,000\nThe outcome is not guaranteed.\n\n"
"7\n00:00:13,000 --> 00:00:14,000\nThese are synthetic examples.\n\n"
"8\n00:00:15,000 --> 00:00:16,000\nThe advice is conditional.\n\n"
"9\n00:00:17,000 --> 00:00:18,000\nNot an investment recommendation.\n").encode()


def fixture():
    cues=parse_exact_srt(SRT);by={x['cue_index']:x for x in cues}
    ps=[]
    for i,(lo,hi) in enumerate(((1,4),(5,9)),1):
        ps.append({'parent_id':f'P{i:03d}','first_cue':lo,'last_cue':hi,
            'cue_indices':list(range(lo,hi+1)),
            'source_text_sha256':sha(' '.join(by[j]['text'] for j in range(lo,hi+1))),
            'speech_act':'EXAMPLE','speaker':'NARRATOR_PRESUMED_UNVERIFIED',
            'scope_source_verified':True})
    ats=[]
    spec=[(1,3,'FACT_CANDIDATE','AFFIRMED','HIGH','SIZE'),
          (4,6,'EXCEPTION','CONDITIONAL','HIGH','EXCEPTION'),
          (7,9,'OPINION','AFFIRMED','LOW','NONE')]
    for i,(lo,hi,kind,stance,risk,key) in enumerate(spec,1):
        ix=list(range(lo,hi+1))
        ats.append({'atom_id':f'A{i:03d}','cue_indices':ix,
          'cue_sha256':[by[j]['cue_sha256'] for j in ix],
          'source_span_sha256':sha(''.join(by[j]['cue_sha256'] for j in ix)),
          'proposition_private':f'Synthetic unverified proposition number {i}',
          'speech_act':kind,'stance':stance,'risk':risk,'evidence_key':key,
          'speaker':'NARRATOR_PRESUMED_UNVERIFIED',
          'related_parents':[p['parent_id'] for p in ps
                             if set(p['cue_indices']) & set(ix)],
          'independent_gold':False,'source_truth_certified':False,
          'official_evidence_verified':False,'financial_fact_approved':False,
          'personal_advice_approved':False})
    fs=[]
    for a in ats[:2]:
        fs.append({'atom_id':a['atom_id'],'cue_indices':a['cue_indices'],
            'as_of':'2026-11-14','rule_effective_date_verified':False,
            'official_source_body_pinned_sha256':None,
            'issuer_reference_urls':[{'issuer_category':'EXCHANGE_RULE',
                 'url':'https://law.krx.co.kr/las/LawBon.jsp?lawid=000015'}],
            'evidence_status':'OPEN_PRIMARY_BODY_AND_APPLICABILITY',
            'has_counterevidence_candidate':True,
            'personal_account_scope_verified':False,'approved':False})
    return {'schema':'V117_PRIVATE_REAL_SOURCE_ATOMIC_GRAPH_V1',
       'video_id':'SYNTHTEST01','srt_sha256':sha(SRT),'zip_sha256':'a'*64,
       'source_cues':9,'cue_hashes':[{'cue_index':x['cue_index'],
                                       'sha256':x['cue_sha256']} for x in cues],
       'parents':ps,'atoms':ats,
       'cross_parent_links':[{'from_atom':'A001','to_atom':'A002',
                              'relation':'ASSET_TYPE_EXCEPTION'}],
       'watch_source_obligations':[{'first_cue':1,'last_cue':4,
                                    'risk_label':'THRESHOLD_EXAMPLE','must_high_risk':True},
                                   {'first_cue':4,'last_cue':6,
                                    'risk_label':'EXCEPTION_EXAMPLE','must_high_risk':True}],
       'financial_docket':fs,
       'prior_relations':[{'atom_id':'A001','namespace':'MASTER116',
              'prior_id':'GOMHEE-C17','relation':'RELATED_ONLY_PENDING',
              'dedup_verified':False}],
       'legacy_master_git_blob_sha1':'ab5af7eea02e65d5e36174546a2a94f4cc642d92',
       'legacy_p4_git_blob_sha1':'bfb446ffb1dd40caa1ed03088d088c9a1ba7490f',
       'v75_gold_404_recovered':False,'historical_full_dedup_complete':False,
       'any_financial_fact_approved':False,'any_personal_advice_approved':False,
       'speaker_audio_verified':False,'original_video_verified':False,
       'independent_gold':False,'recall':None,'precision':None,'p0_go':False}

class SyntheticV117(unittest.TestCase):
    def setUp(self):self.g=fixture()
    def audit(self,graph=None,source=SRT):
        return audit_private_original(raw_srt=source,graph=graph or self.g,
                   expected_srt_sha256=sha(SRT),expected_archive_sha256='a'*64)
    def test_valid_synthetic_graph(self):
        r=self.audit()
        self.assertEqual(r['original_cues'],9)
        self.assertEqual(r['atomic_proposals'],3)
        self.assertEqual(r['official_pending_rows'],2)
        self.assertFalse(r['p0_go'])
        self.assertIsNone(r['model_semantic_wall_ns'])
    def test_source_still_not_model_accuracy(self):
        self.assertIsNone(self.audit()['recall'])
    def test_exception_crosses_parent(self):
        self.assertEqual(self.audit()['cross_parent_relationships'],1)
    def test_invalid_original_srt_byte(self):
        with self.assertRaises(V117SourceProofError):self.audit(source=SRT.replace(b'fund',b'plan'))

# Rejected mutations are isolated tests: CI reports precise failure categories.
def cases():
    yield 'archive_changed', lambda g:g.__setitem__('zip_sha256','b'*64)
    yield 'srt_digest_changed', lambda g:g.__setitem__('srt_sha256','c'*64)
    yield 'video_id_changed', lambda g:g.__setitem__('video_id','wrong')
    yield 'source_count_changed', lambda g:g.__setitem__('source_cues',10)
    yield 'missing_cue_census',lambda g:g['cue_hashes'].pop()
    yield 'cue_text_sha_changed',lambda g:g['cue_hashes'][0].__setitem__('sha256','c'*64)
    yield 'parent_range_gap',lambda g:g['parents'][1].__setitem__('first_cue',6)
    yield 'parent_duplicate',lambda g:g['parents'][1].__setitem__('parent_id','P001')
    yield 'parent_missing',lambda g:g['parents'].pop()
    yield 'parent_sha_forged',lambda g:g['parents'][0].__setitem__('source_text_sha256','e'*64)
    yield 'parent_audio_forged',lambda g:g['parents'][1].__setitem__('speaker','AUDIO_VERIFIED')
    yield 'atom_cue_missing',lambda g:g['atoms'][0]['cue_indices'].pop()
    yield 'atom_ref_unsorted',lambda g:g['atoms'][0].__setitem__('cue_indices',[3,1,2])
    yield 'atom_span_sha_forged',lambda g:g['atoms'][0].__setitem__('source_span_sha256','c'*64)
    yield 'atom_cue_sha_forged',lambda g:g['atoms'][0]['cue_sha256'][0].__class__ and g['atoms'][0]['cue_sha256'].__setitem__(0,'c'*64)
    yield 'atom_parent_wrong',lambda g:g['atoms'][0].__setitem__('related_parents',['P002'])
    yield 'atom_deleted',lambda g:g['atoms'].pop(1)
    yield 'atom_duplicate_id',lambda g:g['atoms'][1].__setitem__('atom_id','A001')
    yield 'no_atom_evidence_key',lambda g:g['atoms'][1].__setitem__('evidence_key','')
    yield 'fake_atom_finance_approved',lambda g:g['atoms'][0].__setitem__('financial_fact_approved',True)
    yield 'fake_atom_independent_gold',lambda g:g['atoms'][0].__setitem__('independent_gold',True)
    yield 'fake_atom_speaker_verified',lambda g:g['atoms'][0].__setitem__('speaker','NARRATOR_CONFIRMED')
    yield 'fake_global_gold',lambda g:g.__setitem__('independent_gold',True)
    yield 'fake_global_recall',lambda g:g.__setitem__('recall',1.0)
    yield 'fake_global_p0_go',lambda g:g.__setitem__('p0_go',True)
    yield 'fake_v75_recovery',lambda g:g.__setitem__('v75_gold_404_recovered',True)
    yield 'fake_historical_dedup',lambda g:g.__setitem__('historical_full_dedup_complete',True)
    yield 'forge_old_master_sha',lambda g:g.__setitem__('legacy_master_git_blob_sha1','a'*40)
    yield 'edge_missing_source_atom',lambda g:g['cross_parent_links'][0].__setitem__('to_atom','A900')
    yield 'edge_duplicate',lambda g:g['cross_parent_links'].append(copy.deepcopy(g['cross_parent_links'][0]))
    yield 'speaker_exception_removed',lambda g:g['cross_parent_links'].clear()
    yield 'watch_removed_all',lambda g:g.__setitem__('watch_source_obligations',[])
    yield 'watch_source_range_invalid',lambda g:g['watch_source_obligations'][0].__setitem__('first_cue',0)
    yield 'watch_high_risk_lost',lambda g:g['atoms'][0].__setitem__('risk','LOW')
    yield 'watch_covered_context_only',lambda g:g['watch_source_obligations'][0].__setitem__('first_cue',7)
    yield 'evidence_deleted',lambda g:g['financial_docket'].pop(0)
    yield 'evidence_misbound_atom',lambda g:g['financial_docket'][0].__setitem__('atom_id','A003')
    yield 'evidence_wrong_cue',lambda g:g['financial_docket'][0].__setitem__('cue_indices',[1])
    yield 'evidence_future_date',lambda g:g['financial_docket'][0].__setitem__('as_of','2027-01-01')
    yield 'evidence_fake_body_sha',lambda g:g['financial_docket'][0].__setitem__('official_source_body_pinned_sha256','f'*64)
    yield 'evidence_falsely_approved',lambda g:g['financial_docket'][0].__setitem__('approved',True)
    yield 'evidence_forge_account',lambda g:g['financial_docket'][0].__setitem__('personal_account_scope_verified',True)
    yield 'evidence_fake_counterevidence',lambda g:g['financial_docket'][0].__setitem__('has_counterevidence_candidate',False)
    yield 'phishing_domain',lambda g:g['financial_docket'][0]['issuer_reference_urls'][0].__setitem__('url','https://law.krx.co.kr.evil.example/las')
    yield 'http_downgrade',lambda g:g['financial_docket'][0]['issuer_reference_urls'][0].__setitem__('url','http://law.krx.co.kr')
    yield 'credentials_in_url',lambda g:g['financial_docket'][0]['issuer_reference_urls'][0].__setitem__('url','https://user:pw@law.krx.co.kr/')
    yield 'fragment_in_url',lambda g:g['financial_docket'][0]['issuer_reference_urls'][0].__setitem__('url','https://law.krx.co.kr/#access')
    yield 'prior_equivalence_forged',lambda g:g['prior_relations'][0].__setitem__('relation','SAME_APPROVED')
    yield 'prior_identity_invented',lambda g:g['prior_relations'][0].__setitem__('prior_id','GOMHEE-C404')
    yield 'prior_merge_forged',lambda g:g['prior_relations'][0].__setitem__('dedup_verified',True)
    yield 'prior_duplicate',lambda g:g['prior_relations'].append(copy.deepcopy(g['prior_relations'][0]))

for name,mutate in cases():
    def test(self,fn=mutate):
        fn(self.g)
        with self.assertRaises(V117SourceProofError):self.audit()
    setattr(SyntheticV117,'test_reject_'+name,test)

class V117PublicReceipt(unittest.TestCase):
    PATH=HERE/'V117_PUBLIC_SHA_ONLY.json'
    @classmethod
    def setUpClass(cls):
        if not cls.PATH.is_file():
            raise AssertionError('V117_PUBLIC_RECEIPT_REQUIRED_IN_GITHUB_CI')
    def test_actual_private_pilot_public_digest(self):
        self.assertTrue(guard_public_v117_receipt(json.loads(self.PATH.read_text()))['structural_custody_pass'])
    def test_false_model_latency_refused(self):
        r=json.loads(self.PATH.read_text());r['model_semantic_wall_ns']=1
        with self.assertRaises(V117SourceProofError):guard_public_v117_receipt(r)
    def test_false_high_risk_recall_refused(self):
        r=json.loads(self.PATH.read_text());r['high_risk_recall']=1.0
        with self.assertRaises(V117SourceProofError):guard_public_v117_receipt(r)
    def test_false_count_refused(self):
        r=json.loads(self.PATH.read_text());r['official_pending_rows']=40
        with self.assertRaises(V117SourceProofError):guard_public_v117_receipt(r)
    def test_false_p0_go_refused(self):
        r=json.loads(self.PATH.read_text());r['p0_go']=True
        with self.assertRaises(V117SourceProofError):guard_public_v117_receipt(r)

if __name__=='__main__':unittest.main()
