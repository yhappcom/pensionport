"""V219 complete E2 path is tested on synthetic SRT only in public CI."""
from __future__ import annotations
import copy
import json
import unittest
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
import test_v218_e2_private_dependency_join_guard as v218_test
RAW=v218_test.RAW
from v219_e2_integrated_source_claim_quality_guard import (
    audit_exact_source_cue_taxonomy,audit_semantic_native_delta,
    audit_financial_and_legacy_hold,run_integrated_e2_source_gate,
    require_gold_before_approval,SCHEMA_CENSUS,SCHEMA_FINANCE,SCHEMA_LEGACY,SCHEMA_PATCH,
)

class TestV219IntegratedE2SourceHold(unittest.TestCase):
    @staticmethod
    def dumps(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    def setUp(self):
        fx=v218_test.TestV218PrivateDependencyJoinGuard();fx.setUp()
        self.source=fx.exchange['source_sha256'];self.fx=fx
        self.old=fx.exchange;self.new=copy.deepcopy(self.old)
        self.new['atoms'][0]['proposition']+=' (외부 검증 미완료)'
        self.graph=fx.run_guard()
        src=fx.coverage['cues']
        rows=[]
        for i,c in enumerate(src,1):
            prim={1:['C00001'],3:['C00002']}.get(i,[])
            ctx={1:['C00001'],2:['C00001'],3:['C00002']}.get(i,[])
            state=('PRIMARY_UNAPPROVED' if prim else
                   'CONTEXT_UNAPPROVED_NEEDS_CLAIM_OMISSION_REVIEW' if ctx else
                   'MEDIA_DEPENDENT_UNMAPPED_QUARANTINE')
            row={'cue_index':i,'cue_text_sha256':c['cue_text_sha256'],
                 'source_quote':c['original_text'],'classification':state,
                 'source_anchor_claim_ids':prim,'context_claim_ids':ctx,
                 'original_audio_or_screen_review_required':i==4,
                 'independent_omission_review_complete':False,
                 'classification_is_chatgpt_source_review_not_external_gold':True,
                 'financial_fact_approved':False,'e2_final_pass':False}
            if i==4:row['visual_claim_requires_original_frames']=True
            rows.append(row)
        self.census={'schema':SCHEMA_CENSUS,'video_id':self.new['video_id'],
            'original_source_sha256':sha256(RAW),
            'native_exchange_sha256':sha256(self.dumps(self.new)),
            'cue_count':4,'classification_counts':{
              'PRIMARY_UNAPPROVED':2,
              'CONTEXT_UNAPPROVED_NEEDS_CLAIM_OMISSION_REVIEW':1,
              'MEDIA_DEPENDENT_UNMAPPED_QUARANTINE':1},
            'audio_screen_flagged_cue_count':1,'distinct_primary_claim_ids':2,
            'original_audio_screen_available':False,'independent_gold_available':False,
            'speaker_verified':False,'e2_final_pass':False,'financial_fact_approved':False,
            'rows':rows}
        finance=[]
        for i,a in enumerate(self.new['atoms']):
            cues=[ref['cue_index'] for ref in a['source_refs']]
            tags=['SYNTHETIC_UNVERIFIED'] if i==0 else []
            finance.append({'claim_id':a['claim_id'],'kind':a['kind'],
                 'primary_cue_ids':cues,
                 'primary_original_text_sha256':[
                    sha256(fx.coverage['cues'][x-1]['original_text'].encode('utf8'))
                    for x in cues],
                 'context_cue_indices':a['context_cue_indices'],
                 'numeric_source_token_cue_pairs':[],
                 'risk_tags':tags,'risk_review_status':(
                    'HOLD_REQUIRES_OFFICIAL_OR_MEDIA_REVIEW' if tags else
                    'SOURCE_ANCHORED_BUT_NOT_INDEPENDENT_GOLD'),
                 'speaker_verified':False,'stance_confirmed':False,
                 'financial_truth_certified':False,
                 'semantically_gold_verified':False,'claim_approved':False})
        self.finance={'schema':SCHEMA_FINANCE,'video_id':self.new['video_id'],
            'source_sha256':sha256(RAW),'native_exchange_sha256':sha256(self.dumps(self.new)),
            'original_audio_screen_available':False,
            'human_independent_gold_available':False,
            'external_independent_gold':False,'precision_measured':False,
            'recall_measured':False,'high_risk_miss_zero_certified':False,
            'e2_final_pass':False,'knowledge_publication_authorized':False,
            'all_atoms_reviewed_source_claims':2,'risk_tagged_atom_count':1,
            'risk_tag_types':['SYNTHETIC_UNVERIFIED'],'atoms':finance}
        txt=fx.coverage['cues'][1]['original_text']
        self.old_open={'rows':[{'cue_index':2,'source_quote':txt,
            'source_text_sha256':sha256(txt.encode('utf8')),
            'historical_v182_open_type':'SYNTHETIC_ASR_AUDIO'}]}
        self.legacy={'schema':SCHEMA_LEGACY,'source_sha256':sha256(RAW),
            'native_exchange_sha256':sha256(self.dumps(self.new)),
            'historical_recovered_owner_sqlite':False,
            'historical_v176_claim61_69_71_verified':False,
            'historical_cases_resolved':0,'e2_final_pass':False,
            'source_only_legacy_risk_rows_verified':1,
            'rows':[{'cue_index':2,'open_type':'SYNTHETIC_ASR_AUDIO',
                'cue_text_sha256':sha256(txt.encode('utf8')),
                'linked_native_unapproved_primary_ids':[],
                'linked_native_unapproved_context_ids':['C00001'],
                'historical_open_still_unresolved':True,
                'owner_sqlite_source_event_chain_verified':False,
                'independent_gold_verified':False,'financial_fact_approved':False}]}
        a=self.old['atoms'][0]
        self.patch={'schema':SCHEMA_PATCH,
            'previous_native_sha256':sha256(self.dumps(self.old)),
            'corrected_native_sha256':sha256(self.dumps(self.new)),
            'source_sha256':sha256(RAW),
            'atom_count_before':2,'atom_count_after':2,
            'speaker_diarization_verified':False,'e2_final_pass':False,
            'changed_claim_ids':['C00001'],'changed_fields_count':1,
            'changes':[{'claim_id':'C00001','field':'proposition',
                 'previous_value':a['proposition'],
                 'corrected_value':self.new['atoms'][0]['proposition'],
                 'original_primary_cue':1,
                 'source_cue_text_sha256':sha256(fx.coverage['cues'][0]['original_text'].encode('utf8')),
                 'financial_fact_approved':False}]}

    def call(self, raw=RAW, override=None, expected=None):
        objs={'old_native':self.old,'new_native':self.new,
              'census':self.census,'finance':self.finance,
              'legacy':self.legacy,'old_open':self.old_open,
              'patch':self.patch,'prior_graph':self.graph}
        if override:objs.update(override)
        data={k:self.dumps(v) for k,v in objs.items()}
        digests={k:sha256(v) for k,v in {'source':RAW,**data}.items()}
        if expected:digests.update(expected)
        return run_integrated_e2_source_gate(raw,objs['old_native'],data['old_native'],
            objs['new_native'],data['new_native'],objs['census'],data['census'],
            objs['finance'],data['finance'],objs['legacy'],data['legacy'],
            objs['old_open'],data['old_open'],objs['patch'],data['patch'],
            objs['prior_graph'],data['prior_graph'],expected_hashes=digests,window_size=2)

    def fails(self,field,mutate,code,raw=RAW):
        d=copy.deepcopy(getattr(self,field));mutate(d)
        with self.assertRaisesRegex(InvalidInput,code):
            self.call(raw=raw,override={field:d})

    def test_01_synthetic_comprehensive_source_gate_pass_hold(self):
        r=self.call()
        self.assertEqual((r['original_cues_verified'],r['native_unapproved_atoms'],
             r['native_correction_field_count'],r['historical_v182_source_open_cases_unresolved']),
             (4,2,1,1))
        self.assertEqual((r['source_grounded_v218_cross_atom_relations_retained'],
                          r['unverified_media_graph_relations_retained']),(1,1))
        self.assertFalse(r['precision_recall_validly_computable'])
        self.assertFalse(r['e2_final_pass'])
        self.assertNotIn('ETF는 펀드',str(r))

    def test_02_repeated_clean_restart_reproducible(self):
        self.assertEqual(self.call(),self.call())

    def test_03_source_byte_drift_blocked(self):
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SIDECAR_BYTE_HASH_MISMATCH'):
            self.call(raw=RAW+b' ')

    def test_04_native_hash_tamper_blocked(self):
        with self.assertRaisesRegex(InvalidInput,'SOURCE_SIDECAR_BYTE_HASH_MISMATCH'):
            self.call(expected={'new_native':'f'*64})

    def test_05_all_synthetic_categories_counted(self):
        r=self.call()
        self.assertEqual(r['all_cue_review_state_counts']['MEDIA_DEPENDENT_UNMAPPED_QUARANTINE'],1)

    def test_06_cue_quote_substituted_blocked(self):
        self.fails('census',lambda d:d['rows'][1].update(source_quote='원금보장'),
                   'CUE_OR_QUOTE_NOT_ORIGINAL')

    def test_07_source_index_malformed_type_blocked(self):
        self.fails('census',lambda d:d['rows'][1].update(cue_index=[]),
                   'CUE_OR_QUOTE_NOT_ORIGINAL')

    def test_08_context_claim_forged_blocked(self):
        self.fails('census',lambda d:d['rows'][1].update(context_claim_ids=['C00002']),
                   'CUE_NATIVE_LINK_OR_PREMATURE_OMISSION_GOLD')

    def test_09_nonprimary_marked_gold_blocked(self):
        self.fails('census',lambda d:d['rows'][1].update(independent_omission_review_complete=True),
                   'CUE_NATIVE_LINK_OR_PREMATURE_OMISSION_GOLD')

    def test_10_unmapped_visual_without_audio_flag_blocked(self):
        self.fails('census',lambda d:d['rows'][3].update(original_audio_or_screen_review_required=False),
                   'VIDEO_HOLD_DROPPED')

    def test_11_media_risk_demoted_nonclaim_blocked(self):
        self.fails('census',lambda d:d['rows'][3].update(classification='DISCOURSE_OR_NONCLAIM_PROVISIONAL'),
                   'MISCLASSIFIED_SOURCE_CUE')

    def test_12_cue_class_total_forged_blocked(self):
        self.fails('census',lambda d:d['classification_counts'].update(PRIMARY_UNAPPROVED=4),
                   'FAKE_CUE_CLASS_TOTALS')

    def test_13_speaker_gold_true_at_top_rejected(self):
        self.fails('census',lambda d:d.update(speaker_verified=True),
                   'CUE_CENSUS_HEADER_OR_FALSE_GOLD')

    def test_14_native_proposition_edit_without_log_blocked(self):
        # The actual integrated call requires companion patch/census/finance SHA
        d=copy.deepcopy(self.new);d['atoms'][0]['proposition']='ETF는 원금보장상품이다'
        with self.assertRaises(InvalidInput):self.call(override={'new_native':d})

    def test_15_native_owner_cue_changed_rejected(self):
        d=copy.deepcopy(self.new);d['atoms'][0]['owner_window_id']='W00099'
        with self.assertRaises(InvalidInput):self.call(override={'new_native':d})

    def test_16_financial_tag_downgraded_without_docket_rejected(self):
        d=copy.deepcopy(self.finance);d['atoms'][0]['risk_tags']=[]
        with self.assertRaisesRegex(InvalidInput,'FINANCE_RISK_BYPASS_OR_FALSE_APPROVAL'):
            self.call(override={'finance':d})

    def test_17_financial_claim_true_forged_rejected(self):
        self.fails('finance',lambda d:d['atoms'][0].update(claim_approved=True),
                   'FINANCE_RISK_BYPASS_OR_FALSE_APPROVAL')

    def test_18_precision_fabrication_rejected(self):
        self.fails('finance',lambda d:d.update(precision_measured=True),
                   'FINANCE_FALSE_CERTIFICATION_OR_CENSUS')

    def test_19_independent_gold_fabrication_rejected(self):
        self.fails('finance',lambda d:d.update(external_independent_gold=True),
                   'FINANCE_FALSE_CERTIFICATION_OR_CENSUS')

    def test_20_missing_finance_atom_blocked(self):
        self.fails('finance',lambda d:d['atoms'].pop(),
                   'FINANCE_FALSE_CERTIFICATION_OR_CENSUS')

    def test_21_numeric_source_reference_forged_blocked(self):
        self.fails('finance',lambda d:d['atoms'][0].update(numeric_source_token_cue_pairs=[{'cue_index':1,'source_token':'100%'}]),
                   'FINANCIAL_TOKEN_OR_SOURCE_MISATTRIBUTION')

    def test_22_legacy_owner_recovery_falsified_blocked(self):
        self.fails('legacy',lambda d:d.update(historical_recovered_owner_sqlite=True),
                   'HISTORICAL_OWNER_FORGED_OR_OPEN_DROPPED')

    def test_23_historical_open_status_forged_rejected(self):
        self.fails('legacy',lambda d:d['rows'][0].update(historical_open_still_unresolved=False),
                   'V182_OPEN_CASE_CHANGED_OR_FALSE_RECOVERY')

    def test_24_legacy_cue_source_hash_forged_rejected(self):
        self.fails('legacy',lambda d:d['rows'][0].update(cue_text_sha256='f'*64),
                   'V182_OPEN_CASE_CHANGED_OR_FALSE_RECOVERY')

    def test_25_full_source_claim_custody_strict_gate(self):
        with self.assertRaisesRegex(InvalidInput,'INDEPENDENT_GOLD_OWNER_AND_MEDIA_NOT_CERTIFIED'):
            require_gold_before_approval(self.call())

    def test_26_prior_graph_false_approved_blocked(self):
        d=copy.deepcopy(self.graph);d['financial_facts_approved']=True
        with self.assertRaisesRegex(InvalidInput,'PREVIOUS_GRAPH_OR_SOURCE_CUSTODY_INVALID'):
            self.call(override={'prior_graph':d})

    def test_27_cross_atom_edge_forged_native_blocked(self):
        d=copy.deepcopy(self.graph);d['cross_atom_edges'][0]['from_atom_id']='C00999'
        with self.assertRaisesRegex(InvalidInput,'INHERITED_GRAPH_EDGE_BROKEN'):
            self.call(override={'prior_graph':d})

    def test_28_cross_atom_relation_dropped_rejected(self):
        d=copy.deepcopy(self.graph);d['cross_atom_edges'].clear()
        with self.assertRaisesRegex(InvalidInput,'GRAPH_RELATION_ROWS_INCOMPLETE'):
            self.call(override={'prior_graph':d})

    def test_29_media_graph_quarantine_removed_rejected(self):
        d=copy.deepcopy(self.graph);d['evidence_quarantines'].clear()
        with self.assertRaisesRegex(InvalidInput,'GRAPH_RELATION_ROWS_INCOMPLETE'):
            self.call(override={'prior_graph':d})

    def test_30_media_graph_false_completed_rejected(self):
        d=copy.deepcopy(self.graph);d['evidence_quarantines'][0]['financial_claim_approved']=True
        with self.assertRaisesRegex(InvalidInput,'INHERITED_GRAPH_MEDIA_HOLD_DROPPED'):
            self.call(override={'prior_graph':d})

if __name__=='__main__':unittest.main()