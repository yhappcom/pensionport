"""Public synthetic regression: NO owner-private SRT or private notes."""
import copy, hashlib, json, unittest
from pathlib import Path
import v121_source_atomic_repair_guard as g


def fixture_cues(n):
    def fmt(ms):
        h,rem=divmod(ms,3_600_000);m,rem=divmod(rem,60_000);s,mm=divmod(rem,1000)
        return f'{h:02d}:{m:02d}:{s:02d},{mm:03d}'
    return '\n\n'.join(f'{i}\n{fmt(i*800)} --> {fmt(i*800+700)}\nsynthetic cue number {i} never an actual investment quote' for i in range(1,n+1)).encode('utf-8')

def syn173():
    raw=fixture_cues(173);c=g.cues_of_srt(raw)
    ids=[f'R{i:03}' for i in range(1,59) if i not in (11,20,35)] + ['R011a','R011b','R020a','R020b']
    assert len(ids)==59
    ref=[]
    for i,refid in enumerate(ids):
        ix=([38,39] if refid=='R011a' else [40,41] if refid=='R011b' else
            [135,136] if refid=='R045' else [137,138] if refid=='R046' else [i+1])
        risk='HIGH' if i<23 else 'MEDIUM'
        ref.append({'id':refid,'cue_indices':ix,'speaker_stance':'AFFIRMED',
                    'risk':risk,'statement':'test canonical source proposition',
                    'source_text_sha256':g.source_sha(c,ix)})
    # high-risk must be 23 and 14 of the *matched* 35. Select explicitly.
    original={r['id']:r for r in ref}
    canon=[r for r in ref if r['id'] not in ('R011b','R046')]
    highids=[r['id'] for r in canon][:23]
    for r in ref:r['risk']='HIGH' if r['id'] in highids else 'MEDIUM'
    canon=[r for r in ref if r['id'] not in ('R011b','R046')]
    for alias,lead in [('R011b','R011a'),('R046','R045')]:
        nd=next(x for x in canon if x['id']==lead)
        idx=sorted(set(nd['cue_indices']+original[alias]['cue_indices']))
        nd['cue_indices']=idx;nd['source_text_sha256']=g.source_sha(c,idx)
    # choose 14 HIGH and 21 MEDIUM TP; alias not included
    highcanon=[r['id'] for r in canon if r['risk']=='HIGH']
    lowcanon=[r['id'] for r in canon if r['risk']!='HIGH']
    matches=highcanon[:14]+lowcanon[:21]
    assert len(matches)==35
    predictions=[];verdicts=[]
    for i in range(46):
        aid=f'A{i+1:03}'
        ix=[i+1,i+2]
        predictions.append({'atom_id':aid,'cue_indices':ix,'proposition_private':'not real source',
                            'source_span_sha256':g.source_sha(c,ix)})
        verdicts.append({'prediction_id':aid,'reference_id':matches[i] if i<35 else None,
                         'verdict':'TP' if i<35 else 'FP'})
    graph={'srt_sha256':g.sha(raw),'atoms':predictions}
    B={'original_source_sha256':g.sha(raw),'reference_claims':ref}
    score={'predicted_atom_verdicts':verdicts}
    rec={'source_sha256':g.sha(raw),'frozen_v120_reference_digest':g.digest(B),
         'frozen_v120_score_digest':g.digest(score),'canonical_references':canon,
         'merged_aliases':{'R011b':'R011a','R046':'R045'},
         'merge_evidence':{
         'R011b':{'canonical':'R011a','reason':'DUPLICATE_MEANING_NOT_INDEPENDENT_FINANCIAL_CLAIM'},
         'R046':{'canonical':'R045','reason':'DUPLICATE_MEANING_NOT_INDEPENDENT_FINANCIAL_CLAIM'}},
         'context_analogy_retained_as_discourse':'R034',
         'speaker_self_correction_retained':['R055','R056'],
         'posthoc_rescored_counts':{'tp':35,'fp':11,'fn':22,'reference_candidates':57,
            'baseline_predictions':46,'high_risk_total':23,'high_risk_matched':14},
         'score_type':'CHAT_INTERNAL_DEVELOPMENT_POSTHOC_NOT_UNSEEN',
         'independent_gold':False,'fact_approved':False,'p0_go':False,
         'certified_precision':None,'certified_recall':None,'certified_high_risk_recall':None}
    return raw,graph,B,score,rec


def syn_repair(raw,graph):
    cues=g.cues_of_srt(raw)
    cases={i:'SPLIT' for i in ['A003','A008','A009','A012','A015','A021','A031','A044']}
    cases.update({'A016':'RESTORE_QUALIFIER','A020':'NARROW','A027':'DUPLICATE_EVIDENCE'})
    repairs={}
    for id,op in cases.items():
        atom=next(x for x in graph['atoms'] if x['atom_id']==id)
        if op=='DUPLICATE_EVIDENCE':
            repairs[id]={'operation':op,'children':[],'duplicate_of':'A024',
                         'repeat_cue_sha256':g.source_sha(cues,atom['cue_indices'])}
            continue
        children=[]
        for j in range(2 if op=='SPLIT' else 1):
            idx=[atom['cue_indices'][j]]
            children.append({'id':id+f'.{j+1}','cue_indices':idx,
                 'cue_span_sha256':g.source_sha(cues,idx),
                 'speaker_claim':'압도적 source proposition' if id=='A016' else 'source proposition sample',
                 'reviewer_qualification':'must distinguish reviewer counterevidence',
                 'finance_verification':'OPEN'})
        repairs[id]={'operation':op,'children':children}
        if id=='A044':repairs[id]['relation']='SPEAKER_SELF_STRENGTHENING_THEN_DERIVATIVE_EXCEPTION'
    return {'baseline_graph_sha256':g.digest(graph),
            'repair_ledger_kind':'DEVELOPMENT_PROPOSAL_REQUIRES_NEW_HOLDOUT',
            'retrospective_original_score_upgraded':False,'repairs':repairs}


def syn222():
    raw=fixture_cues(222);c=g.cues_of_srt(raw)
    breaks=[(1,18),(19,59),(60,77),(78,95),(96,114),(115,153),(154,173),(174,195),(196,216),(217,222)]
    parents=[{'first_cue':a,'last_cue':b,'source_sha256':g.source_sha(c,list(range(a,b+1)))} for a,b in breaks]
    units=[];risk={}
    must={9,26,35,37,42,55,57,58}
    highids=set(range(1,18))|must
    assert len(highids)==24
    for i in range(1,61):
        uid=f'U{i:03}';ix=[i];risk_label='HIGH' if i in highids else 'LOW'
        units.append({'unit_id':uid,'cue_indices':ix,'source_sha256':g.source_sha(c,ix),
              'type':'SPEAKER_FACT_CANDIDATE','risk':risk_label,
              'statement':'source-grounded only example proposition','review_status':'CHAT_SOURCE_FIRST_PROVISIONAL'})
        if risk_label=='HIGH':risk[uid]={'status':'OPEN'}
    study={'video_id':'k9O79HeMOp0','source_sha256':g.sha(raw),'source_cues':222,
           'baseline_or_prior_reference_seen':False,'engine_prediction_precommitted':False,
           'stage':'SOURCE_FIRST_NEW_VIDEO_NOT_SCORED','discourse_parents':parents,
           'source_first_units':units,'risk_open_ledger':risk,'internal_tp_fp_fn':None,
           'model_semantic_time_seconds':None,'financial_fact_approved':0,'knowledge_merge_count':0,
           'independent_gold':False,'p0_go':False}
    issues=[{'issue_id':f'B{pos:03}','unit_id':f'U{i:03}',
             'A_source_sha256':units[i-1]['source_sha256'],'speaker_claim':units[i-1]['statement'],
             'reviewer_qualification':'must check evidence original and scope',
             'status':'OPEN_REQUIRE_CURRENT_SCOPE_EVIDENCE',
             'official_source_http_bytes_sha256':None} for pos,i in enumerate(sorted(highids),1)]
    B={'schema':'V121_NEW_VIDEO_CHAT_B_ADVERSARIAL_CONTEXT_OPEN_V1','as_of':'2026-11-15',
       'source_sha256':g.sha(raw),'A_frozen_sha256':g.digest(study),
       'adversarial_issues':issues,'this_is_external_independent_gold':False,
       'model_prediction_accuracy_scored':False,'unseen_video_heldout_until_after_engine_patch':False}
    return raw,study,B


def syn_generic():
    raw=fixture_cues(4); cues=g.cues_of_srt(raw)
    p=[{'id':f'X{i}','cue_indices':[i],
        'source_sha256':g.source_sha(cues,[i]),'speaker_assertion':'synthetic source'} for i in range(1,5)]
    # allow split to reuse the same cue for 2 independent assertions in utterance
    spl=[{'id':'X1.1','cue_indices':[1],'source_sha256':g.source_sha(cues,[1]),
          'speaker_assertion':'premise one','reviewer_qualification':'unverified','speaker_scope_is_source_literal':True,
          'approval_status':'PENDING_REVIEW'},
         {'id':'X1.2','cue_indices':[1],'source_sha256':g.source_sha(cues,[1]),
          'speaker_assertion':'premise two','reviewer_qualification':'unverified','speaker_scope_is_source_literal':True,
          'approval_status':'PENDING_REVIEW'}]
    ops=[{'source_id':'X1','operation':'SPLIT','children':spl},
         {'source_id':'X4','operation':'REPEAT_AS_EVIDENCE','duplicate_of':'X2',
          'repeat_source_sha256':g.source_sha(cues,[4])}]
    return raw,p,ops

class ActualReceipts(unittest.TestCase):
    def test_public_receipt_not_gold(self):
        p=Path(__file__).resolve().parent/'V121_PUBLIC_SHA_ONLY.json'
        r=json.loads(p.read_text(encoding='utf-8'))
        self.assertIs(r['independent_gold'],False)
        self.assertIs(r['p0_go'],False)
        self.assertEqual(r['new_video_cues'],222)
        self.assertIsNone(r['unseen_new_engine_precision'])
    def test_public_receipt_study_counts(self):
        r=json.loads((Path(__file__).resolve().parent/'V121_PUBLIC_SHA_ONLY.json').read_text(encoding='utf-8'))
        self.assertEqual((r['development_reference_before'],r['development_reference_after']), (59,57))
        self.assertEqual((r['development_initial_predictions'],r['development_proposed_repaired_candidates']), (46,53))
        self.assertEqual((r['new_source_first_units'],r['new_financial_risk_open']), (60,24))

class ReconcileGate(unittest.TestCase):
    def setUp(self):self.raw,self.graph,self.B,self.score,self.rec=syn173()
    def ok(self):return g.audit_reconciliation(self.graph,self.B,self.score,self.rec,self.raw)
    def reject(self,f):
        f()
        with self.assertRaises(g.UnsafeV121):self.ok()
    def test_01_normal(self):self.assertEqual(self.ok()['fn'],22)
    def test_02_recalc_precision(self):self.assertAlmostEqual(self.ok()['precision'],35/46)
    def test_03_recalc_recall(self):self.assertAlmostEqual(self.ok()['recall'],35/57)
    def test_04_original_source_sha(self):self.reject(lambda:self.graph.update(srt_sha256='0'*64))
    def test_05_changed_original_srt(self):
        self.raw=self.raw.replace(b'number 13',b'number 9999');self.assertRaises(g.UnsafeV121,self.ok)
    def test_06_reference_digest_tamper(self):self.reject(lambda:self.rec.update(frozen_v120_reference_digest='f'*64))
    def test_07_score_digest_tamper(self):self.reject(lambda:self.rec.update(frozen_v120_score_digest='f'*64))
    def test_08_canonical_missing(self):self.reject(lambda:self.rec['canonical_references'].pop())
    def test_09_canonical_duplicate(self):self.reject(lambda:self.rec['canonical_references'][1].update(id=self.rec['canonical_references'][0]['id']))
    def test_10_wrong_alias(self):self.reject(lambda:self.rec['merged_aliases'].update(R011b='R045'))
    def test_11_lost_original_provenance(self):self.reject(lambda:self.rec['canonical_references'][0].update(cue_indices=[173]))
    def test_12_changed_source_sha(self):self.reject(lambda:self.rec['canonical_references'][0].update(source_text_sha256='a'*64))
    def test_13_stance_forge(self):self.reject(lambda:self.rec['canonical_references'][0].update(speaker_stance='REBUTTED'))
    def test_14_risk_forge(self):self.reject(lambda:self.rec['canonical_references'][0].update(risk='CRITICAL'))
    def test_15_merge_reason_missing(self):self.reject(lambda:self.rec['merge_evidence']['R046'].update(reason='SAME_TOPIC_ONLY'))
    def test_16_polarity_self_correction_lost(self):self.reject(lambda:self.rec.update(speaker_self_correction_retained=['R055']))
    def test_17_context_analogy_erased(self):self.reject(lambda:self.rec.update(context_analogy_retained_as_discourse=None))
    def test_18_fake_gold(self):self.reject(lambda:self.rec.update(independent_gold=True))
    def test_19_fake_approved(self):self.reject(lambda:self.rec.update(fact_approved=True))
    def test_20_fake_go(self):self.reject(lambda:self.rec.update(p0_go=True))
    def test_21_fake_precision(self):self.reject(lambda:self.rec.update(certified_precision=0.99))
    def test_22_false_lift(self):self.reject(lambda:self.rec.update(score_type='MODEL_HOLDOUT_IMPROVEMENT'))
    def test_23_wrong_fn(self):self.reject(lambda:self.rec['posthoc_rescored_counts'].update(fn=20))
    def test_24_bad_prediction_id(self):self.reject(lambda:self.score['predicted_atom_verdicts'][0].update(prediction_id='FAKE'))

class RepairGate(unittest.TestCase):
    def setUp(self):
        self.raw,self.graph,_,_,_=syn173();self.repair=syn_repair(self.raw,self.graph)
    def ok(self):return g.audit_repair(self.graph,self.repair,self.raw)
    def reject(self,fn):
        fn()
        with self.assertRaises(g.UnsafeV121):self.ok()
    def test_01_normal(self):self.assertEqual(self.ok()['proposed_repaired_children'],18)
    def test_02_unseen_upgraded(self):self.reject(lambda:self.repair.update(retrospective_original_score_upgraded=True))
    def test_03_graph_hash_tamper(self):self.reject(lambda:self.repair.update(baseline_graph_sha256='0'*64))
    def test_04_drop_complex_case(self):self.reject(lambda:self.repair['repairs'].pop('A003'))
    def test_05_unknown_parent(self):self.reject(lambda:self.repair['repairs'].update(A000=self.repair['repairs']['A003']))
    def test_06_drop_atomic_child(self):self.reject(lambda:self.repair['repairs']['A003']['children'].pop())
    def test_07_invented_child_source(self):self.reject(lambda:self.repair['repairs']['A003']['children'][0].update(cue_indices=[173]))
    def test_08_wrong_child_sha(self):self.reject(lambda:self.repair['repairs']['A003']['children'][0].update(cue_span_sha256='a'*64))
    def test_09_false_finance_approval(self):self.reject(lambda:self.repair['repairs']['A003']['children'][0].update(finance_verification='APPROVED'))
    def test_10_missing_reviewer_caveat(self):self.reject(lambda:self.repair['repairs']['A003']['children'][0].update(reviewer_qualification=''))
    def test_11_original_superlative_lost(self):self.reject(lambda:self.repair['repairs']['A016']['children'][0].update(speaker_claim='important'))
    def test_12_self_correction_erased(self):self.reject(lambda:self.repair['repairs']['A044'].update(relation='NONE'))
    def test_13_repeat_reclassified_as_fact(self):self.reject(lambda:self.repair['repairs']['A027'].update(operation='NARROW'))
    def test_14_repeat_hash_corrupt(self):self.reject(lambda:self.repair['repairs']['A027'].update(repeat_cue_sha256='b'*64))
    def test_15_materialize_no_fake_prediction_score(self):
        out=g.materialize_development_repair(self.graph,self.repair,self.raw)
        self.assertEqual(len(out['revised_candidates']),53)
        self.assertEqual(len(out['repeat_source_evidence']),1)
        self.assertIs(out['can_be_used_as_unseen_score'],False)

class NewSourceGate(unittest.TestCase):
    def setUp(self):self.raw,self.study,self.b=syn222()
    def ok(self):return g.audit_new_source(self.study,self.raw)
    def reject(self,fn):
        fn()
        with self.assertRaises(g.UnsafeV121):self.ok()
    def test_01_normal(self):self.assertEqual(self.ok()['new_video_cues'],222)
    def test_02_60_claims(self):self.assertEqual(self.ok()['source_first_units'],60)
    def test_03_24_open(self):self.assertEqual(self.ok()['financial_risk_open'],24)
    def test_04_source_tamper(self):self.reject(lambda:self.study.update(source_sha256='0'*64))
    def test_05_partial_cue_partition(self):self.reject(lambda:self.study['discourse_parents'][0].update(last_cue=17))
    def test_06_parent_sha(self):self.reject(lambda:self.study['discourse_parents'][0].update(source_sha256='0'*64))
    def test_07_atom_sha(self):self.reject(lambda:self.study['source_first_units'][0].update(source_sha256='0'*64))
    def test_08_duplicate_atom_id(self):self.reject(lambda:self.study['source_first_units'][1].update(unit_id='U001'))
    def test_09_lose_high_risk(self):self.reject(lambda:self.study['risk_open_ledger'].pop('U001'))
    def test_10_fake_engine_prediction(self):self.reject(lambda:self.study.update(engine_prediction_precommitted=True))
    def test_11_fake_score(self):self.reject(lambda:self.study.update(internal_tp_fp_fn={'tp':59}))
    def test_12_model_time_forged(self):self.reject(lambda:self.study.update(model_semantic_time_seconds=0))
    def test_13_fake_fact_approval(self):self.reject(lambda:self.study.update(financial_fact_approved=1))
    def test_14_false_gold(self):self.reject(lambda:self.study.update(independent_gold=True))
    def test_15_false_go(self):self.reject(lambda:self.study.update(p0_go=True))
    def test_16_unknown_unit_type(self):self.reject(lambda:self.study['source_first_units'][0].update(type='APPROVED_FACT'))
    def test_17_source_cue_range(self):self.reject(lambda:self.study['source_first_units'][0].update(cue_indices=[223]))
    def test_18_source_is_not_173(self):
        s,_,_,_,_=syn173()
        with self.assertRaises(g.UnsafeV121):g.audit_new_source(self.study,s)
    def test_19_low_risk_forge(self):self.reject(lambda:self.study['source_first_units'][0].update(risk='LOW'))

class AdversarialGate(unittest.TestCase):
    def setUp(self):self.raw,self.study,self.b=syn222()
    def ok(self):return g.audit_new_adversarial_pass(self.study,self.b,self.raw)
    def reject(self,fn):
        fn()
        with self.assertRaises(g.UnsafeV121):self.ok()
    def test_01_normal(self):self.assertEqual(self.ok()['B_adversarial_issues'],24)
    def test_02_A_digest_tamper(self):self.reject(lambda:self.b.update(A_frozen_sha256='0'*64))
    def test_03_fewer_issues(self):self.reject(lambda:self.b.update(adversarial_issues=self.b['adversarial_issues'][:17]))
    def test_04_missing_risk_specific(self):self.reject(lambda:self.b['adversarial_issues'][8].update(unit_id='U025'))
    def test_05_B_no_official_pin(self):self.reject(lambda:self.b['adversarial_issues'][0].update(official_source_http_bytes_sha256='0'*64))
    def test_06_B_not_fact_approved(self):self.reject(lambda:self.b['adversarial_issues'][0].update(status='APPROVED'))
    def test_07_B_qualifier_required(self):self.reject(lambda:self.b['adversarial_issues'][0].update(reviewer_qualification=''))
    def test_08_B_speaker_unchanged(self):self.reject(lambda:self.b['adversarial_issues'][0].update(speaker_claim='reviewer thought not speaker'))
    def test_09_B_no_external_gold(self):self.reject(lambda:self.b.update(this_is_external_independent_gold=True))
    def test_10_B_no_score(self):self.reject(lambda:self.b.update(model_prediction_accuracy_scored=True))
    def test_11_B_no_fake_new_holdout(self):self.reject(lambda:self.b.update(unseen_video_heldout_until_after_engine_patch=True))
    def test_12_B_wrong_asof(self):self.reject(lambda:self.b.update(as_of='2026-10-01'))
    def test_13_B_wrong_source(self):self.reject(lambda:self.b['adversarial_issues'][0].update(A_source_sha256='0'*64))
    def test_14_B_duplicate_issue_id(self):self.reject(lambda:self.b['adversarial_issues'][1].update(issue_id='B001'))

class GenericEngineGate(unittest.TestCase):
    def setUp(self):self.raw,self.proposals,self.ops=syn_generic()
    def ok(self):return g.apply_host_reviewed_atomic_patch(self.raw,self.proposals,self.ops)
    def reject(self,fn):
        fn()
        with self.assertRaises(g.UnsafeV121):self.ok()
    def test_01_operational(self):
        out=self.ok();self.assertEqual((out['original_count'],out['after_patch_count']), (4,4))
        self.assertIs(out['model_called_automatically'],False)
    def test_02_mutated_source(self):self.reject(lambda:self.proposals[0].update(source_sha256='a'*64))
    def test_03_mutated_child_sha(self):self.reject(lambda:self.ops[0]['children'][0].update(source_sha256='a'*64))
    def test_04_change_speaker_to_review(self):self.reject(lambda:self.ops[0]['children'][0].update(speaker_scope_is_source_literal=False))
    def test_05_false_fact_acceptance(self):self.reject(lambda:self.ops[0]['children'][0].update(approval_status='APPROVED'))
    def test_06_duplicate_op(self):self.reject(lambda:self.ops.append(copy.deepcopy(self.ops[0])))
    def test_07_child_id_duplicate(self):self.reject(lambda:self.ops[0]['children'][1].update(id='X1.1'))
    def test_08_repeat_not_approved(self):self.reject(lambda:self.ops[1].update(repeat_source_sha256='0'*64))
    def test_09_empty_children(self):self.reject(lambda:self.ops[0].update(children=[]))
    def test_10_unknown_source_parent(self):self.reject(lambda:self.ops[0].update(source_id='NO_SOURCE'))
    def test_11_unknown_operation(self):self.reject(lambda:self.ops[0].update(operation='MODEL_AUTO_CORRECTED'))
    def test_12_removal_without_canonical(self):self.reject(lambda:self.ops[1].update(duplicate_of='FAKE'))
    def test_13_source_distance(self):self.reject(lambda:self.ops[0]['children'][0].update(cue_indices=[4]))
    def test_14_invalid_time_format(self):
        self.raw=self.raw.replace(b'00:00:00,800 -->',b'00:00:99,800 -->')
        with self.assertRaises(g.UnsafeV121):self.ok()
    def test_15_nonmonotone_source_times(self):
        self.raw=self.raw.replace(b'00:00:01,600 -->',b'00:00:00,600 -->')
        with self.assertRaises(g.UnsafeV121):self.ok()

if __name__=='__main__':unittest.main()
