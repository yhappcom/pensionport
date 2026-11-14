"""V121 chat-native source/prediction lineage and conservative development refactoring.

This gate checks owner-original cue bytes, de-duplicated reference lineage,
source-literal atom refinements, and a previously unseen source-only study.
It cannot independently interpret Korean financial text, certify accuracy,
automatically run ChatGPT, or approve a financial/knowledge assertion.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path

class UnsafeV121(ValueError):
    pass


def require(ok, label):
    if not ok:raise UnsafeV121('V121_'+label)


def sha(x):
    return hashlib.sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()


def digest(x):
    return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))


def cues_of_srt(raw):
    require(type(raw) is bytes and 0<len(raw)<5_000_000,'SOURCE_BYTES')
    try: s=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n').strip()
    except UnicodeDecodeError as ex:raise UnsafeV121('V121_SOURCE_ENCODING') from ex
    cues=[]; previous_start=-1
    def parse_time(clock):
        m=re.fullmatch(r'(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})',clock.strip())
        require(m is not None,'SOURCE_TIME_FORMAT')
        h,minute,sec,ms=map(int,m.groups())
        require(minute<60 and sec<60,'SOURCE_TIME_RANGE')
        return ((h*60+minute)*60+sec)*1000+ms
    for i,block in enumerate(re.split(r'\n\s*\n',s),1):
        z=block.splitlines()
        require(len(z)>2 and z[0].strip().isdigit() and int(z[0])==i,'SOURCE_INDEX')
        clock_parts=re.split(r'\s*-->\s*',z[1])
        require(len(clock_parts)==2,'SOURCE_TIME_ARROW')
        start,end=map(parse_time,clock_parts)
        require(previous_start<=start<=end,'SOURCE_TIME_ORDER')
        previous_start=start
        t=' '.join(line.strip() for line in z[2:] if line.strip())
        require(bool(t),'SOURCE_NO_TEXT')
        cues.append(t)
    return cues


def source_sha(cues,ix):
    require(isinstance(ix,list) and bool(ix),'CUE_SET')
    require(all(type(n) is int and 1<=n<=len(cues) for n in ix),'CUE_RANGE')
    require(sorted(set(ix))==ix,'CUE_ORDER_DUPLICATE')
    return sha(' | '.join(cues[n-1] for n in ix))


def audit_reconciliation(baseline, original_ref, scored, reconciliation, raw):
    source=cues_of_srt(raw)
    require(len(source)==173,'ORIGINAL_173')
    require(sha(raw)==baseline['srt_sha256']==original_ref['original_source_sha256'],'ORIGINAL_SOURCE_DRIFT')
    require(reconciliation['source_sha256']==sha(raw),'REF_SOURCE_DRIFT')
    require(reconciliation['frozen_v120_reference_digest']==digest(original_ref),'REF_FROZEN_DIGEST')
    require(reconciliation['frozen_v120_score_digest']==digest(scored),'SCORE_FROZEN_DIGEST')
    old=original_ref['reference_claims']; ids=[r['id'] for r in old]
    require(len(ids)==59 and len(set(ids))==59,'REF_59_UNIQUE')
    require(len(reconciliation['canonical_references'])==57,'REF_57')
    canonical={r['id']:r for r in reconciliation['canonical_references']}
    require(len(canonical)==57,'REF_DUPLICATE_ID')
    required_merged={'R011b':'R011a','R046':'R045'}
    require(reconciliation['merged_aliases']==required_merged,'ONLY_TWO_SEMANTIC_DUPLICATES')
    require(set(ids)==set(canonical)|set(required_merged),'CANONICAL_LINEAGE_PARTITION')
    orig={r['id']:r for r in old}
    for key,node in canonical.items():
        require(key in orig,'UNKNOWN_CANONICAL')
        require(node['speaker_stance']==orig[key]['speaker_stance'] and node['risk']==orig[key]['risk'],'REF_SCOPE_RISK_DRIFT')
        require(node['cue_indices']==sorted(set(node['cue_indices'])),'REF_CUE_LIST')
        require(node['source_text_sha256']==source_sha(source,node['cue_indices']),'REF_SOURCE_SHA')
        require(set(orig[key]['cue_indices']).issubset(node['cue_indices']),'CANONICAL_ORIGINAL_PROVENANCE')
    for alias,lead in required_merged.items():
        require(set(orig[alias]['cue_indices']).issubset(canonical[lead]['cue_indices']),'MERGED_SOURCE_PROVENANCE')
        require(reconciliation['merge_evidence'][alias]['canonical']==lead,'MERGE_EVIDENCE')
        require(reconciliation['merge_evidence'][alias]['reason']=='DUPLICATE_MEANING_NOT_INDEPENDENT_FINANCIAL_CLAIM','MERGE_REASON')
    require(reconciliation['context_analogy_retained_as_discourse']=='R034','CONTEXT_NOT_ERASED')
    require(reconciliation['speaker_self_correction_retained']==['R055','R056'],'SPEAKER_CORRECTION_PRESERVED')
    verdicts=scored['predicted_atom_verdicts']; require(len(verdicts)==46,'SCORE_BASELINE_46')
    predids={a['atom_id'] for a in baseline['atoms']}
    require({x['prediction_id'] for x in verdicts}==predids,'BASELINE_PRED_IDS')
    matched=[v['reference_id'] for v in verdicts if v['verdict']=='TP']
    require(len(matched)==35 and len(set(matched))==35,'MAPPING_TP_35')
    require(set(matched).issubset(canonical),'MAPPING_REFS_GONE')
    require(all(v['reference_id'] is None for v in verdicts if v['verdict']=='FP'),'MAPPING_FP_REFERENCE')
    require(sum(v['verdict']=='FP' for v in verdicts)==11,'MAPPING_FP_11')
    rc=[v for v in canonical.values() if v['risk'] in ('HIGH','CRITICAL')]
    htp=sum(canonical[r]['risk'] in ('HIGH','CRITICAL') for r in matched)
    require(len(rc)==23 and htp==14,'HIGH_RISK_COUNTS')
    expected={'tp':35,'fp':11,'fn':22,'reference_candidates':57,'baseline_predictions':46,'high_risk_total':23,'high_risk_matched':14}
    require(reconciliation['posthoc_rescored_counts']==expected,'SCORE_RECOUNT')
    require(reconciliation['score_type']=='CHAT_INTERNAL_DEVELOPMENT_POSTHOC_NOT_UNSEEN','SCORE_LABEL')
    for s in ['independent_gold','fact_approved','p0_go']:
        require(reconciliation[s] is False,'NO_FALSE_GO_'+s)
    for s in ['certified_precision','certified_recall','certified_high_risk_recall']:
        require(reconciliation[s] is None,'NO_FALSE_CERTIFICATION_'+s)
    return {'source_cues':173,**expected,'precision':35/46,'recall':35/57,'high_risk_recall':14/23}


def audit_repair(baseline, repair, raw):
    cues=cues_of_srt(raw)
    require(len(cues)==173 and sha(raw)==baseline['srt_sha256'],'REPAIR_ORIGINAL_SOURCE')
    require(repair['baseline_graph_sha256']==digest(baseline),'REPAIR_GRAPH_HASH')
    atoms={a['atom_id']:a for a in baseline['atoms']}
    require(set(repair['repairs'])==set(['A003','A008','A009','A012','A015','A016','A020','A021','A027','A031','A044']),'REPAIR_KNOWN_TOUCHED_IDS')
    allnew=[]
    for pid,entry in repair['repairs'].items():
        base=atoms[pid]
        require(entry['operation'] in ('SPLIT','NARROW','RESTORE_QUALIFIER','DUPLICATE_EVIDENCE'),'REPAIR_OP')
        if entry['operation']=='DUPLICATE_EVIDENCE':
            require(pid=='A027' and entry['duplicate_of']=='A024' and not entry['children'],'NO_INVENTED_ADDITIONAL_CLAIM')
            require(entry['repeat_cue_sha256']==source_sha(cues,base['cue_indices']),'REPEAT_CUE_SHA')
            continue
        children=entry['children']; require(isinstance(children,list) and len(children)>=1,'REPAIR_CHILDREN')
        require((len(children)>=2)==(entry['operation']=='SPLIT'),'SPLIT_REQUIRES_TWO')
        for child in children:
            require(child['id'].startswith(pid+'.') and child['id'] not in allnew,'REPAIR_CHILD_ID')
            allnew.append(child['id'])
            idx=child['cue_indices']
            require(child['cue_span_sha256']==source_sha(cues,idx),'REPAIR_CHILD_SHA')
            require(bool(child['speaker_claim']) and bool(child['reviewer_qualification']),'REPAIR_DISTINGUISH_SPEAKER_REVIEWER')
            require(child['finance_verification']=='OPEN','REPAIR_FINANCE_NOT_APPROVED')
            require(set(idx).intersection(base['cue_indices']),'REPAIR_NO_ANCHOR')
            require(all(min(base['cue_indices'])-1<=i<=max(base['cue_indices'])+1 for i in idx),'REPAIR_SOURCE_BOUNDS')
        if pid=='A044':
            require(entry['relation']=='SPEAKER_SELF_STRENGTHENING_THEN_DERIVATIVE_EXCEPTION','REPAIR_SELF_CORRECTION')
            require(len(children)==2,'SELF_CORRECTION_UNITS')
        if pid=='A016':
            require(entry['operation']=='RESTORE_QUALIFIER' and '압도적' in children[0]['speaker_claim'],'SUPERLATIVE_PRESERVED')
    require(repair['repair_ledger_kind']=='DEVELOPMENT_PROPOSAL_REQUIRES_NEW_HOLDOUT','NOT_INDEPENDENT_UPLIFT')
    require(repair['retrospective_original_score_upgraded'] is False,'NO_TRAIN_ON_TEST')
    return {'baseline_atoms':46,'edited_source_atoms':len(repair['repairs']),'proposed_repaired_children':len(allnew),'baseline_untouched':46-len(repair['repairs'])}


def audit_new_source(study,raw):
    cues=cues_of_srt(raw)
    require(len(cues)==222,'NEW_VIDEO_222')
    require(study['video_id']=='k9O79HeMOp0' and study['source_sha256']==sha(raw),'NEW_SOURCE_PIN')
    require(study['baseline_or_prior_reference_seen'] is False,'NEW_COACHING_LEAK')
    require(study['stage']=='SOURCE_FIRST_NEW_VIDEO_NOT_SCORED','NO_FAKE_HOLDOUT_SCORE')
    parents=study['discourse_parents']; pos=[]
    for p in parents:
        indices=list(range(p['first_cue'],p['last_cue']+1))
        require(p['source_sha256']==source_sha(cues,indices),'NEW_PARENT_SHA')
        pos.extend(indices)
    require(pos==list(range(1,223)),'NEW_CUE_PARTITION')
    ids=set();need_finance=[]
    for a in study['source_first_units']:
        require(a['unit_id'] not in ids,'NEW_DUPLICATE_ID')
        ids.add(a['unit_id'])
        require(a['source_sha256']==source_sha(cues,a['cue_indices']),'NEW_ATOM_SOURCE')
        require(a['type'] in ('SPEAKER_FACT_CANDIDATE','RECOMMENDATION','SUBJECTIVE','QUESTION','ANALOGY','CONTEXT'),'NEW_ATOM_KIND')
        require(a['risk'] in ('LOW','MEDIUM','HIGH','CRITICAL'),'NEW_ATOM_RISK')
        require(bool(a['statement']) and len(a['statement'])>=6,'NEW_ATOM_TEXT')
        require(a['review_status']=='CHAT_SOURCE_FIRST_PROVISIONAL','NEW_ATOM_UNVERIFIED')
        if a['risk'] in ('HIGH','CRITICAL'):
            require(a['unit_id'] in study['risk_open_ledger'],'NEW_RISK_MISSING')
            need_finance.append(a['unit_id'])
    require(len(ids)>=55,'NEW_COVERAGE_TOO_SMALL')
    require(set(need_finance)==set(study['risk_open_ledger']),'RISK_LEDGER_EXACT')
    require(study['engine_prediction_precommitted'] is False,'NEW_NO_PREDICTION')
    require(study['internal_tp_fp_fn'] is None,'NEW_NO_FAKE_METRIC')
    require(study['model_semantic_time_seconds'] is None,'NEW_MODEL_TIME_UNMEASURED')
    require(study['financial_fact_approved']==0 and study['knowledge_merge_count']==0,'NEW_NO_APPROVAL')
    require(study['independent_gold'] is False and study['p0_go'] is False,'NEW_NO_GO')
    return {'new_video_cues':len(cues),'discourse_parents':len(parents),'source_first_units':len(ids),'financial_risk_open':len(need_finance),'unattributed_cues':0}


def materialize_development_repair(baseline, repair, raw):
    """Returns source-linked *proposals*, never a scored model prediction."""
    audit_repair(baseline, repair, raw)
    revised=[];repeat=[]
    for atom in baseline['atoms']:
        old_id=atom['atom_id'];event=repair['repairs'].get(old_id)
        if event is None:
            revised.append({'candidate_id':old_id,'source_atom_id':old_id,'kind':'UNTOUCHED_PREVIOUS_PREDICTION',
                            'cue_indices':atom['cue_indices'],'speaker_assertion':atom['proposition_private'],
                            'reviewer_qualification':None,'finance_verification':'OPEN'})
        elif event['operation']=='DUPLICATE_EVIDENCE':
            repeat.append({'source_atom_id':old_id,'duplicate_of':event['duplicate_of'],
                           'repeat_source_span_sha256':event['repeat_cue_sha256']})
        else:
            for child in event['children']:
                revised.append({'candidate_id':child['id'],'source_atom_id':old_id,'kind':'CHAT_PROPOSED_REFINEMENT_NOT_NEW_MODEL_PREDICTION',
                                'cue_indices':child['cue_indices'],'speaker_assertion':child['speaker_claim'],
                                'reviewer_qualification':child['reviewer_qualification'],
                                'finance_verification':child['finance_verification']})
    require(len(revised)==53 and len(repeat)==1,'REPAIRED_CANDIDATE_CENSUS')
    require(len({v['candidate_id'] for v in revised})==53,'REPAIRED_CANDIDATE_UNIQUE')
    return {'schema':'V121_DEVELOPMENT_ATOM_REFINEMENT_NOT_EVALUATION_V1',
            'old_prediction_count':46,'candidate_after_revision_count':53,
            'revised_candidates':revised,'repeat_source_evidence':repeat,
            'can_be_used_as_unseen_score':False,'independent_gold':False,'p0_go':False}


def audit_new_adversarial_pass(study,b_pass,raw):
    audit_new_source(study,raw)
    require(b_pass['schema']=='V121_NEW_VIDEO_CHAT_B_ADVERSARIAL_CONTEXT_OPEN_V1','B_SCHEMA')
    require(b_pass['source_sha256']==study['source_sha256'],'B_SOURCE_LOCK')
    require(b_pass['A_frozen_sha256']==digest(study),'B_A_LOCK')
    require(b_pass['as_of']=='2026-11-15','B_ASOF')
    issues=b_pass['adversarial_issues']
    require(len(issues)>=18,'B_ISSUE_COVERAGE')
    ids={x['unit_id'] for x in study['source_first_units']}
    risks=set(study['risk_open_ledger'])
    seen=set()
    for x in issues:
        require(x['issue_id'] not in seen,'B_DUPLICATE_ISSUE')
        seen.add(x['issue_id'])
        require(x['unit_id'] in ids and x['unit_id'] in risks,'B_UNKNOWN_OR_LOW_RISK')
        node=next(y for y in study['source_first_units'] if y['unit_id']==x['unit_id'])
        require(x['A_source_sha256']==node['source_sha256'],'B_A_SOURCE_ORIGINAL')
        require(x['status']=='OPEN_REQUIRE_CURRENT_SCOPE_EVIDENCE','B_NO_FALSE_FACT_ACCEPTANCE')
        require(bool(x['reviewer_qualification']) and x['speaker_claim']==node['statement'],'B_STANCE_SEPARATION')
        require(x['official_source_http_bytes_sha256'] is None,'B_NO_FALSE_HTTP_PIN')
    require({'U009','U026','U035','U037','U042','U055','U057','U058'}.issubset({z['unit_id'] for z in issues}),'B_KEY_FINANCE_CASES')
    require({z['unit_id'] for z in issues}==risks,'B_ALL_HIGH_RISK_REVIEWED')
    require(b_pass['this_is_external_independent_gold'] is False,'B_NO_EXTERNAL_GOLD')
    require(b_pass['model_prediction_accuracy_scored'] is False,'B_NO_FAKE_ACCURACY')
    require(b_pass['unseen_video_heldout_until_after_engine_patch'] is False,'B_NOT_STILL_HELDOUT')
    return {'B_adversarial_issues':len(issues),'source_first_units':len(study['source_first_units']),
            'new_video_source_cues':study['source_cues'],'independent_gold':False}


def apply_host_reviewed_atomic_patch(source_raw, proposals, operations):
    """Generic source-locked proposal repair for any complete SRT.

    ChatGPT supplies semantics; this deterministic function can only check
    provenance, shape and isolation. A reviewer's counterevidence stays separate
    from speaker claims; all generated candidates are PENDING, not approved.
    """
    cues=cues_of_srt(source_raw)
    require(isinstance(proposals,list) and bool(proposals),'GENERIC_INPUT')
    require(isinstance(operations,list),'GENERIC_PATCH_LIST')
    byid={}
    for p in proposals:
        k=p['id']
        require(type(k) is str and bool(k) and k not in byid,'GENERIC_SOURCE_ID')
        require(p['source_sha256']==source_sha(cues,p['cue_indices']),'GENERIC_INPUT_SHA')
        require(bool(p['speaker_assertion']),'GENERIC_INPUT_TEXT')
        byid[k]=p
    opmap={}
    for o in operations:
        k=o['source_id']
        require(k in byid and k not in opmap,'GENERIC_OP_TARGET')
        require(o['operation'] in ('SPLIT','NARROW','REWRITE_WITH_SPEAKER_SCOPE','REPEAT_AS_EVIDENCE'),'GENERIC_OP_KIND')
        opmap[k]=o
    out=[]; repeats=[]
    for old,p in byid.items():
        o=opmap.get(old)
        if o is None:
            out.append({'id':old,'source_parent_id':old,'cue_indices':p['cue_indices'],
                        'source_sha256':p['source_sha256'],'speaker_assertion':p['speaker_assertion'],
                        'reviewer_qualification':None,'approval_status':'PENDING_REVIEW',
                        'transformation':'PRESERVE'})
            continue
        if o['operation']=='REPEAT_AS_EVIDENCE':
            require(not o.get('children'),'GENERIC_REPEAT_NOT_ATOM')
            other=o.get('duplicate_of')
            require(other in byid and other!=old,'GENERIC_REPEAT_TARGET')
            require(o.get('repeat_source_sha256')==p['source_sha256'],'GENERIC_REPEAT_HASH')
            repeats.append({'id':old,'canonical':other,'source_sha256':p['source_sha256']})
            continue
        children=o.get('children')
        require(isinstance(children,list) and bool(children),'GENERIC_CHILD_REQUIRED')
        require((len(children)>=2)==(o['operation']=='SPLIT'),'GENERIC_CHILD_COUNT')
        for child in children:
            idx=child['cue_indices']
            require(set(idx).intersection(p['cue_indices']),'GENERIC_CHILD_SOURCE_INTERSECTION')
            require(all(min(p['cue_indices'])-1<=i<=max(p['cue_indices'])+1 for i in idx),'GENERIC_CHILD_BEYOND_PARENT')
            require(child['source_sha256']==source_sha(cues,idx),'GENERIC_CHILD_SOURCE_SHA')
            require(type(child['speaker_assertion']) is str and bool(child['speaker_assertion'].strip()),'GENERIC_CHILD_ASSERTION')
            require(type(child['reviewer_qualification']) is str and bool(child['reviewer_qualification'].strip()),'GENERIC_REVIEWER_ISOLATION')
            require(child['speaker_scope_is_source_literal'] is True,'GENERIC_REVIEWER_NOT_SPEAKER')
            require(child['approval_status']=='PENDING_REVIEW','GENERIC_NO_FACT_APPROVAL')
            out.append({'id':child['id'],'source_parent_id':old,'cue_indices':idx,
                        'source_sha256':child['source_sha256'],'speaker_assertion':child['speaker_assertion'],
                        'reviewer_qualification':child['reviewer_qualification'],'approval_status':'PENDING_REVIEW',
                        'transformation':o['operation']})
    require(len(out)==len({r['id'] for r in out}),'GENERIC_OUTPUT_DUPLICATE_ID')
    require(all(r['id'] not in byid or r['transformation']=='PRESERVE' for r in out),'GENERIC_OUTPUT_ID_COLLISION')
    return {'schema':'V121_HOST_REVIEWED_ATOMIC_PATCH_NOT_MODEL_PREDICTION_V1',
            'source_sha256':sha(source_raw),'source_cues':len(cues),
            'original_count':len(proposals),'after_patch_count':len(out),
            'source_evidence_repeats':repeats,'candidates':out,
            'approved_finance_facts':0,'certified_independent_accuracy':False,
            'model_called_automatically':False}
