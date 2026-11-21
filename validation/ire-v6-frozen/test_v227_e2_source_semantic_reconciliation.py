"""Public synthetic-only tests: all labels/phrases are invented, NOT owner data."""
import copy
import json
import unittest
from hashlib import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange, NUMBER
from v176_chat_engine_loop import make_original_plan
from v227_e2_source_semantic_reconciliation import (
    audit_v227_exact_replay, prepare_v227_records, canonical_bytes, sha,
)


def synthetic():
    texts=[
      '이 상품은 가상의 ETF라고 설명합니다.',
      '장내에서 가격이 표시된다고 덧붙입니다.',
      'ETF 비교할 때 조건을 확인하라고 조언합니다.',
      '유동성은 보장되지 않는다고 주의를 줍니다.',
      '가상의 화면을 하나 보여드리겠습니다.',
      '화면에서 두 가지 추세선이 있다고 말합니다.',
      '오늘 안내는 여기까지입니다.',
      '다음 편에서 뵙겠습니다.',
    ]
    raw='\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},900\n{t}' for i,t in enumerate(texts,1)).encode('utf-8')
    source,_=make_original_plan(raw,'SYNTHET0001',expected_source_sha256=sha(raw),window_size=20)
    def atom(cid,idx,prop,kind,ctx):
        return {'claim_id':cid,'owner_window_id':source.owner(idx),
        'proposition':prop,'kind':kind,'stance':'UNRESOLVED','speaker':'UNKNOWN',
        'source_refs':[{'cue_index':idx,'quote':texts[idx-1]}],
        'context_cue_indices':ctx,'condition_cue_indices':[],
        'exception_cue_indices':[],'numeric_references':[],'as_of':None}
    atoms=[atom('C00001',1,'화자가 ETF를 가상의 상품으로 소개함','HYPOTHETICAL',[1,2]),
           atom('C00002',3,'ETF 선택 시 조건을 검토하라는 조언','RECOMMENDATION',[3,4]),
           atom('C00003',6,'가상의 화면에 추세선이 존재한다고 말했다는 설명(영상 미확인)','HYPOTHETICAL',[5,6])]
    rows=[]
    for i,t in enumerate(texts,1):
        cid={1:'C00001',3:'C00002',6:'C00003'}.get(i)
        rows.append({'cue_index':i,'cue_text_sha256':sha(t.encode('utf-8')),
            'disposition':'CANDIDATES' if cid else ('NO_ATOM' if i==8 else 'UNRESOLVED'),
            'claim_ids':[cid] if cid else [],'numeric_tokens':NUMBER.findall(t),
            'note':'합성 발언 후보' if cid else '모의 문맥 또는 비주장'})
    native={'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':source.video_id,
       'source_sha256':source.source_sha256,'manifest_sha256':source.manifest_sha256,
       'cue_dispositions':rows,'atoms':atoms}
    audit_host_atomic_exchange(source,native)
    cls=['SOURCE_ANCHORED_NATIVE_UNAPPROVED','SOURCE_CONTEXT_ONLY_UNAPPROVED',
      'SOURCE_ANCHORED_NATIVE_UNAPPROVED','SOURCE_CONTEXT_ONLY_UNAPPROVED',
      'MEDIA_SPEECH_CONTEXT_STILL_VISUAL_HOLD','MEDIA_SPEECH_SOURCE_ANCHORED_BUT_VISUAL_HOLD',
      'DISCOURSE_OR_NONCLAIM_PROVISIONAL','DISCOURSE_OR_NONCLAIM_PROVISIONAL']
    cues=[]
    for i,t in enumerate(texts,1):
        a=[cid for cid,at in {a['claim_id']:a for a in atoms}.items() if i in [x['cue_index'] for x in at['source_refs']]]
        context={'C00001' if i==2 else 'C00002' if i==4 else 'C00003' if i in (5,6) else ''}
        context_ids=list(context-{''}) if i in (2,4) else []
        cues.append({'cue_index':i,'cue_text_sha256':sha(t.encode('utf-8')),
           'source_quote':t,'classification':cls[i-1],
           'source_anchor_claim_ids':a,'context_claim_ids':context_ids,
           'original_audio_or_screen_review_required':i in (5,6)})
    census={'original_source_sha256':sha(raw),'native_exchange_sha256':sha(canonical_bytes(native)),'rows':cues}
    tasks=[]
    for j,a in enumerate(atoms):
        if j==2:
            sc={'source_refs':a['source_refs'],'source_context_cue_indices':a['context_cue_indices']}
        else:
            sc=[{'cue_index':i,'quote':texts[i-1],'quote_sha256':sha(texts[i-1].encode('utf-8'))}
                for i in a['context_cue_indices']]
        tasks.append({'claim_id':a['claim_id'],'proposition':a['proposition'],
           'source_context':sc,'financial_fact_approved':False,'e3_final_approved':False,
           'v226_independent_gold_verified':False})
    e3={'schema':'SYNTHETIC_E3','native_sha256':sha(canonical_bytes(native)),'source_sha256':sha(raw),
        'task_rows':tasks,'e3_final_approved':False,'e4_approved':False,'e5_published':False}
    reasons={7:'이번 모의 수업이 끝났다는 안내 문구이며 별도 ETF 금융사실 원자가 완성되지는 않음',
             8:'다음 편에서 다시 만나자는 수업 인사로 별도 투자결정의 증명이나 권고가 아님'}
    reviews={'C00001|C00002':{'status':'RELATED_DISTINCT',
      'source_grounded_reason':'ETF를 가상으로 소개한 설정과 해당 상품의 비교조건을 검토하라는 조언은 서로 다른 발화 기능을 가진다'}}
    tri,e3n,pair=prepare_v227_records(source,native,census,e3,
                                     manual_nonclaim_reasons=reasons,manual_pair_review=reviews)
    docs={'srt':raw,'native':canonical_bytes(native),'census':canonical_bytes(census),
          'old_e3':canonical_bytes(e3),'source_triage':canonical_bytes(tri),
          'canonical_e3':canonical_bytes(e3n),'all_pairs':canonical_bytes(pair)}
    return docs,reasons,reviews


def run(docs,reasons,reviews,**kw):
    hashes={k:sha(v) for k,v in docs.items()}
    return audit_v227_exact_replay(docs,expected_sha256=hashes,nonclaim_reasons=reasons,
                                  manual_pairs=reviews,**kw)


def change_doc(docs,name,change):
    docs=copy.deepcopy(docs)
    j=json.loads(docs[name]);change(j)
    docs[name]=canonical_bytes(j)
    return docs


class TestV227SourceFirstCoverage(unittest.TestCase):
    def setUp(self):
        self.docs,self.reasons,self.reviews=synthetic()

    def test_01_complete_source_unapproved(self):
        got=run(self.docs,self.reasons,self.reviews)
        self.assertEqual(got['original_cues_replayed'],8)
        self.assertEqual(got['native_unapproved_atoms'],3)
        self.assertEqual(got['frozen_v6_unresolved_cue_count'],4)
        self.assertEqual(got['reconciled_review_class_counts']['SOURCE_CONTEXT_LINKED_NOT_PRIMARY'],2)
        self.assertEqual(got['legacy_dict_source_context_fields_fixed'],1)
        self.assertEqual(got['full_native_pairwise_lexical_pairs_checked'],3)
        self.assertFalse(got['e2_final_pass'])

    def test_02_e3_all_task_contexts_list(self):
        d=json.loads(self.docs['canonical_e3'])
        self.assertTrue(all(type(x['source_context']) is list for x in d['task_rows']))
        self.assertEqual(d['v227_original_media_task_ids_normalized'],['C00003'])
        self.assertEqual(d['v227_final_e3_grants'],0)

    def test_03_separate_structural_unresolved_and_high_priority(self):
        d=json.loads(self.docs['source_triage']);self.assertEqual(len(d['outstanding_direct_audio_or_nonclaim_review_cues']),3)
        self.assertTrue(all(x['no_claim_absence_certified'] is False for x in d['rows']))

    def test_04_all_pairs_complete_and_not_gold(self):
        d=json.loads(self.docs['all_pairs'])
        self.assertEqual(d['pair_count'],3)
        self.assertEqual(d['remaining_pairs_have_only_lexical_screen_not_semantic_ground_truth'],2)
        self.assertEqual(d['independently_approved_equivalent_pairs'],0)

    def test_05_bad_original_source_digest(self):
        docs=copy.deepcopy(self.docs);docs['srt']=docs['srt']+b'X'
        with self.assertRaises(InvalidInput):
            audit_v227_exact_replay(docs,expected_sha256={k:sha(v) for k,v in self.docs.items()},
                nonclaim_reasons=self.reasons,manual_pairs=self.reviews)

    def test_06_bad_srt_even_with_new_hash(self):
        docs=copy.deepcopy(self.docs);docs['srt']=docs['srt']+b'\n'
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_07_corrupted_census_quote(self):
        docs=change_doc(self.docs,'census',lambda d:d['rows'][1].update(source_quote='조작된 원문'))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_08_corrupted_census_hash(self):
        docs=change_doc(self.docs,'census',lambda d:d['rows'][1].update(cue_text_sha256='0'*64))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_09_missing_context_claim(self):
        docs=change_doc(self.docs,'census',lambda d:d['rows'][1].update(context_claim_ids=[]))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_10_nonexistent_context_claim(self):
        docs=change_doc(self.docs,'census',lambda d:d['rows'][1].update(context_claim_ids=['C99999']))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_11_wrong_primary_claim_id(self):
        docs=change_doc(self.docs,'census',lambda d:d['rows'][0].update(source_anchor_claim_ids=['C00002']))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_12_lost_media_hold(self):
        docs=change_doc(self.docs,'census',lambda d:d['rows'][4].update(original_audio_or_screen_review_required=False))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_13_media_classification_promoted(self):
        docs=change_doc(self.docs,'census',lambda d:d['rows'][5].update(classification='SOURCE_ANCHORED_NATIVE_UNAPPROVED'))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_14_discard_media_context(self):
        docs=change_doc(self.docs,'native',lambda d:d['atoms'][2].update(context_cue_indices=[6]))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_15_approval_in_e3_prior(self):
        docs=change_doc(self.docs,'old_e3',lambda d:d['task_rows'][1].update(e3_final_approved=True))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_16_fake_gold_on_cue(self):
        docs=change_doc(self.docs,'source_triage',lambda d:d['rows'][2].update(no_claim_absence_certified=True))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_17_fake_gold_precision(self):
        docs=change_doc(self.docs,'source_triage',lambda d:d.update(independent_gold_precision=1))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_18_missing_source_cue(self):
        docs=change_doc(self.docs,'source_triage',lambda d:d['rows'].pop())
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_19_missing_e3_task(self):
        docs=change_doc(self.docs,'canonical_e3',lambda d:d['task_rows'].pop())
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_20_e3_mutate_original_meaning(self):
        docs=change_doc(self.docs,'canonical_e3',lambda d:d['task_rows'][0].update(proposition='잘못된 새 사실'))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_21_e3_wrong_new_quote_hash(self):
        docs=change_doc(self.docs,'canonical_e3',lambda d:d['task_rows'][2]['source_context'][0].update(quote_sha256='X'*64))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_22_e3_dict_reintroduced(self):
        docs=change_doc(self.docs,'canonical_e3',lambda d:d['task_rows'][2].update(source_context={'bad':'shape'}))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_23_e3_fake_release(self):
        docs=change_doc(self.docs,'canonical_e3',lambda d:d.update(e5_published=True))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_24_missing_one_pair(self):
        docs=change_doc(self.docs,'all_pairs',lambda d:d['rows'].pop())
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_25_wrong_pair_similarity(self):
        docs=change_doc(self.docs,'all_pairs',lambda d:d['rows'][0].update(lexical_similarity=1.0))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_26_falsely_assert_exact_semantic_equivalence(self):
        docs=change_doc(self.docs,'all_pairs',lambda d:d['rows'][0].update(independently_verified_exact_equivalence=True))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_27_false_automatic_merge(self):
        docs=change_doc(self.docs,'all_pairs',lambda d:d['rows'][0].update(automatically_merged=True))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_28_review_pairs_missing_signed_reason(self):
        bad=copy.deepcopy(self.reviews);bad['C00001|C00002']['source_grounded_reason']='short'
        with self.assertRaises(InvalidInput):run(self.docs,self.reasons,bad)

    def test_29_wrong_nonclaim_reason(self):
        bad=copy.deepcopy(self.reasons);del bad[7]
        with self.assertRaises(InvalidInput):run(self.docs,bad,self.reviews)

    def test_30_wrong_nonclaim_label(self):
        bad=copy.deepcopy(self.reasons);bad[8]='short'
        with self.assertRaises(InvalidInput):run(self.docs,bad,self.reviews)

    def test_31_nonclaim_detail_ref_hash_matches_native(self):
        docs=change_doc(self.docs,'native',lambda d:d['atoms'][0]['source_refs'][0].update(quote='바뀐 문장'))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_32_wrong_json_blob_type(self):
        docs=copy.deepcopy(self.docs);docs['source_triage']=b'[]'
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_33_invalid_window_size_string(self):
        with self.assertRaises(InvalidInput):run(self.docs,self.reasons,self.reviews,window_size='20')

    def test_34_invalid_window_size_zero(self):
        with self.assertRaises(InvalidInput):run(self.docs,self.reasons,self.reviews,window_size=0)

    def test_35_correct_window_size_20(self):
        self.assertEqual(run(self.docs,self.reasons,self.reviews,window_size=20)['original_cues_replayed'],8)

    def test_36_no_groundtruth_accuracy_claim(self):
        d=json.loads(self.docs['source_triage'])
        self.assertIsNone(d['true_source_semantic_omission_count'])
        self.assertIsNone(d['independent_high_risk_false_negatives'])

    def test_37_malformed_e3_task_missing_context_fail_closed(self):
        docs=change_doc(self.docs,'old_e3',lambda d:d['task_rows'][0].pop('source_context'))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_38_malformed_native_claim_id_schema_fail_closed(self):
        docs=change_doc(self.docs,'native',lambda d:d['atoms'][0].pop('claim_id'))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_39_existing_primary_e3_context_missing_fail_closed(self):
        docs=change_doc(self.docs,'old_e3',lambda d:d['task_rows'][0].update(source_context=[]))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_40_source_triage_number_of_semantic_completions_never_asserted(self):
        docs=change_doc(self.docs,'source_triage',lambda d:d.update(true_source_semantic_omission_count=0))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_41_existing_financial_risk_is_not_silently_granted(self):
        docs=change_doc(self.docs,'canonical_e3',lambda d:d['task_rows'][1].update(financial_fact_approved=True))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)

    def test_42_stale_native_with_only_new_sha_must_not_pass(self):
        docs=change_doc(self.docs,'native',lambda d:d['atoms'][0].update(proposition='신규 문맥에서 몰래 바뀐 의미'))
        with self.assertRaises(InvalidInput):run(docs,self.reasons,self.reviews)


if __name__=='__main__':unittest.main()