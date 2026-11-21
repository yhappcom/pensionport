"""V222 source, 65-atom risk docket, and cue census coherence: synthetic only."""
from __future__ import annotations
import copy
import json
import unittest
from collections import Counter

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan
from test_v222_e2_source_nonclaim_filter_guard import fixture,encode
from v222_e2_source_nonclaim_filter_guard import audit_postfilter_native_risk_and_cue_census


def synthetic_sidecars():
    data=fixture();raw=data['source'];native=data['new_native']
    source,_=make_original_plan(raw,native['video_id'],expected_source_sha256=sha256(raw),window_size=2)
    a=native['atoms'][0]
    finance={
      'schema':'IRE_V219_PRIVATE_ALL_66_ATOMS_SEMANTIC_FINANCE_REVIEW_V1',
      'source_sha256':sha256(raw),'native_exchange_sha256':sha256(encode(native)),
      'original_audio_screen_available':False,'human_independent_gold_available':False,
      'external_independent_gold':False,'e2_final_pass':False,
      'knowledge_publication_authorized':False,'all_atoms_reviewed_source_claims':1,
      'risk_tagged_atom_count':1,'risk_tag_types':['SCOPE_RISK'],
      'atoms':[{'claim_id':a['claim_id'],'kind':a['kind'],
        'primary_cue_ids':[x['cue_index'] for x in a['source_refs']],
        'primary_original_text_sha256':[sha256(source.cues[x['cue_index']-1].text.encode()) for x in a['source_refs']],
        'context_cue_indices':a['context_cue_indices'],
        'numeric_source_token_cue_pairs':[], 'risk_tags':['SCOPE_RISK'],
        'risk_review_status':'HOLD_REQUIRES_OFFICIAL_OR_MEDIA_REVIEW',
        'speaker_verified':False,'stance_confirmed':False,
        'financial_truth_certified':False,'semantically_gold_verified':False,
        'claim_approved':False}],
    }
    bycue={i:[] for i in range(1,5)};ctx={i:[] for i in range(1,5)}
    for atom in native['atoms']:
      for r in atom['source_refs']:bycue[r['cue_index']].append(atom['claim_id'])
      for i in atom['context_cue_indices']:ctx[i].append(atom['claim_id'])
    rows=[]
    for i in range(1,5):
      media=i==3
      kind=('MEDIA_DEPENDENT_UNMAPPED_QUARANTINE' if media else
            'SOURCE_ANCHORED_NATIVE_UNAPPROVED' if bycue[i] else
            'SOURCE_CONTEXT_ONLY_UNAPPROVED' if ctx[i] else
            'DISCOURSE_OR_NONCLAIM_PROVISIONAL')
      original=source.cues[i-1].text
      rows.append({'cue_index':i,'cue_text_sha256':sha256(original.encode()),
        'source_quote':original,'source_anchor_claim_ids':sorted(bycue[i]),
        'context_claim_ids':sorted(ctx[i]),'classification':kind,
        'original_audio_or_screen_review_required':media,
        'independent_omission_review_complete':False,
        'classification_is_chatgpt_source_review_not_external_gold':True,
        'financial_fact_approved':False,'e2_final_pass':False})
    census={'schema':'IRE_V219_PRIVATE_SOURCE_FIRST_250_CUE_REVIEW_V1',
      'video_id':native['video_id'],'original_source_sha256':sha256(raw),
      'native_exchange_sha256':sha256(encode(native)),
      'cue_count':4,'distinct_primary_claim_ids':1,
      'classification_counts':dict(Counter(x['classification'] for x in rows)),
      'audio_screen_flagged_cue_count':1,
      'original_audio_screen_available':False,'independent_gold_available':False,
      'financial_fact_approved':False,'speaker_verified':False,'e2_final_pass':False,
      'rows':rows}
    return {'source':raw,'native':native,'finance':finance,'census':census}


class TestV222PostfilterSidecars(unittest.TestCase):
    def setUp(self):self.x=synthetic_sidecars()

    def audit(self,override=None):
      d={k:(v if k=='source' else encode(v)) for k,v in self.x.items()}
      h={k:sha256(v) for k,v in d.items()}
      if override:h.update(override)
      return audit_postfilter_native_risk_and_cue_census(
          self.x['source'],self.x['native'],d['native'],
          self.x['finance'],d['finance'],self.x['census'],d['census'],
          expected_hashes=h,window_size=2)

    def test_01_pass_and_no_promotion(self):
      r=self.audit();self.assertEqual(r['native_atoms_checked'],1)
      self.assertEqual(r['cues_checked'],4)
      self.assertEqual(r['finance_risk_tagged_atoms'],1)
      self.assertFalse(r['e2_final_pass'])

    def test_02_source_bytes_tampered(self):
      before=sha256(self.x['source']);self.x['source']+=b' '
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_SOURCE_SHA_CHANGED'):
        self.audit({'source':before})

    def test_03_native_atom_old_sha_mismatch(self):
      self.x['finance']['native_exchange_sha256']='f'*64
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_CUSTODY_OR_FALSE_APPROVAL'):self.audit()

    def test_04_cue_census_old_native_sha_mismatch(self):
      self.x['census']['native_exchange_sha256']='f'*64
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_CUSTODY_OR_FALSE_APPROVAL'):self.audit()

    def test_05_risk_row_id_missing(self):
      self.x['finance']['atoms'][0]['claim_id']='C99999'
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_FINANCE_ATOM_ID_MISSING_OR_DUPLICATE'):self.audit()

    def test_06_primary_quote_sha_wrong(self):
      self.x['finance']['atoms'][0]['primary_original_text_sha256']=['f'*64]
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_FINANCE_RISK_SOURCE_OR_FALSE_GOLD'):self.audit()

    def test_07_numeric_source_contamination(self):
      self.x['finance']['atoms'][0]['numeric_source_token_cue_pairs']=[{'cue_index':4,'source_token':'100%'}]
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_FINANCE_RISK_SOURCE_OR_FALSE_GOLD'):self.audit()

    def test_08_risk_census_drift(self):
      self.x['finance']['risk_tagged_atom_count']=0
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_FINANCE_RISK_COUNT_DRIFT'):self.audit()

    def test_09_cue_primary_misaligned(self):
      self.x['census']['rows'][1]['source_anchor_claim_ids']=[]
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_CUE_SOURCE_OR_ID_MISMATCH'):self.audit()

    def test_10_nonclaim_fake_confirmed_source_type(self):
      self.x['census']['rows'][0]['classification']='SOURCE_ANCHORED_NATIVE_UNAPPROVED'
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_CUE_CLASSIFICATION_DRIFT'):self.audit()

    def test_11_media_hold_dropped(self):
      self.x['census']['rows'][2]['classification']='DISCOURSE_OR_NONCLAIM_PROVISIONAL'
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_CUE_CLASS_COUNT_OR_MEDIA_FLAG_DRIFT'):self.audit()

    def test_12_media_flag_falsely_cleared(self):
      self.x['census']['rows'][2]['original_audio_or_screen_review_required']=False
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_MEDIA_UNRESOLVED_WAS_SILENCED'):self.audit()

    def test_13_false_financial_truth_pass(self):
      self.x['finance']['atoms'][0]['financial_truth_certified']=True
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_FINANCE_RISK_SOURCE_OR_FALSE_GOLD'):self.audit()

    def test_14_missing_original_cue_row(self):
      self.x['census']['rows'].pop()
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_CUE_CENSUS_INCOMPLETE'):self.audit()

    def test_15_unchanged_deterministic_replay(self):
      self.assertEqual(self.audit(),self.audit())

    def test_16_provisional_nonclaim_cannot_be_gold(self):
      self.x['census']['rows'][0]['independent_omission_review_complete']=True
      with self.assertRaisesRegex(InvalidInput,'SIDECAR_CUE_SOURCE_OR_ID_MISMATCH'):self.audit()


if __name__=='__main__':unittest.main()