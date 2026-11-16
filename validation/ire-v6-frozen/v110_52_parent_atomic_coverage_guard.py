"""V110 source-first audit of all 52 V109 parents (no owner source in public repo).

Coverage of original transcript cues is an auditable structural property;
semantic completeness and independent gold are NOT established by this gate.
Verifies role provenance, numeric surface forms, cross-parent scope, and
explicit OPEN states. Same ChatGPT host authored the private decompositions.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from hashlib import sha256
import json, re

SCHEMA='V110_CHAT_52_PARENT_SOURCE_UNIT_DECOMPOSITION_NO_GOLD_V1'
ROLES={'FACT_CANDIDATE','OPINION','HYPOTHESIS','CONDITION','EXCEPTION','REBUTTAL','QUESTION','RESPONSE','UNCERTAIN_AUDIO','NONFINANCIAL','OPEN_FRAGMENT'}
EDGE_TYPES={'CONTEXT_DEPENDS_ON','FOLLOWS','CONTRASTS_WITH','QUALIFIES','REVIEWER_NUMERIC_INCONSISTENCY','SPEAKER_SELF_REVISION','REVIEWER_LAW_COUNTEREVIDENCE'}
SHA=re.compile(r'^[0-9a-f]{64}$')
NUM=re.compile(r'(?<![0-9A-Za-z])\d[0-9,.]*(?:%|세|년|개월|원|만|억)?')
CONTRAST=re.compile(r'다만|하지만|그런데|근데')
POLARITY=re.compile(r'다만|하지만|그런데|근데|아니|안(?=\s)|못|없|않')

def require(ok,code):
    if not ok: raise ValueError('V110_'+code)

def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(x):return sha256(x if isinstance(x,bytes) else x.encode('utf-8')).hexdigest()
def digest(x):return sha(canon(x))

def audit(*,packet,old_pass_a,old_atoms,old_counterexamples,decomposition,source_zip_sha,
          expected_cues=160,expected_parents=52,expected_units=None,expected_gaps=2,expected_counterexamples=None):
    require(type(packet)==dict and type(old_pass_a)==dict and type(old_atoms)==dict and type(old_counterexamples)==dict and type(decomposition)==dict,'INPUT_TYPES')
    require(type(source_zip_sha)==str and SHA.fullmatch(source_zip_sha) is not None,'ARCHIVE_SHA_FORMAT')
    require(all(x.get('source_archive_sha256')==source_zip_sha for x in (packet,old_pass_a,old_atoms,old_counterexamples)),'ARCHIVE_LINEAGE')
    require(decomposition.get('schema')==SCHEMA and decomposition.get('source_archive_sha256')==source_zip_sha,'NEW_SOURCE_SCHEMA')
    require(packet.get('prediction_disclosed') is False and packet.get('independent_gold') is False,'SEALED_NOT_GOLD')
    cues=packet.get('owner_private_cues');require(type(cues)==list and len(cues)==expected_cues,'SOURCE_CUES')
    cue_map={};groups=defaultdict(list)
    for c in cues:
        require(type(c)==dict and type(c.get('video_id')) is str and type(c.get('window_id')) is str and type(c.get('cue_index')) is int,'CUE_ID')
        key=(c['video_id'],c['cue_index']);require(key not in cue_map,'DUP_SOURCE_CUE')
        require(type(c.get('text_private')) is str and c.get('cue_sha256')==sha(c['text_private']),'CUE_SHA')
        cue_map[key]=c;groups[(c['video_id'],c['window_id'])].append(c)
    for key,rows in groups.items():
        require(len({c['cue_index'] for c in rows})==len(rows) and [c['cue_index'] for c in rows]==list(range(rows[0]['cue_index'],rows[-1]['cue_index']+1)),'WINDOW_ORDER')
    require(type(old_pass_a.get('parents'))==list and len(old_pass_a['parents'])==expected_parents,'OLD_PARENT_SET')
    old={}
    for p in old_pass_a['parents']:
        key=(p['video_id'],p['draft_parent_id']);require(key not in old,'OLD_PARENT_DUP')
        require(type(p.get('source_cue_indices')) is list and bool(p['source_cue_indices']),'OLD_PARENT_SOURCE')
        old[key]=p
    require(len(old)==expected_parents,'OLD_PARENT_IDENTITY')
    assert_lineage=decomposition.get('v109_pass_a_digest_sha256')
    require(assert_lineage==digest(old_pass_a),'OLD_PASS_A_CHANGED')
    require(decomposition.get('v109_28_atoms_digest_sha256')==digest(old_atoms),'OLD_ATOM_CHANGED')
    require(decomposition.get('v109_19_counterexamples_digest_sha256')==digest(old_counterexamples),'OLD_COUNTEREXAMPLES_CHANGED')
    parents=decomposition.get('parents');require(type(parents)==list and len(parents)==expected_parents,'PARENT_CENSUS')
    seen=set();units_seen=set();units_count=0;unit_roles=Counter();parent_covered=set();all_new_covered=set();numbers=0;polarity_mentions=0;source_contrast_mentions=0;condition_units=0;source_exception_units=0;speaker_rebuttal_units=0;review_open_units=0
    parent_key_by_id={}
    for p in parents:
        require(type(p)==dict,'NEW_PARENT_TYPE')
        key=(p.get('video_id'),p.get('draft_parent_id'));require(key in old and key not in seen,'PARENT_MISSING_DUP_EXTRA');seen.add(key);parent_key_by_id[key]=p
        oldrow=old[key];v,win=key[0],p.get('window_id')
        require(win==oldrow['window_id'] and p.get('source_parent_sha256')==oldrow['source_parent_sha256'],'PARENT_ORIGINAL_SHA')
        ids=p.get('source_cue_indices');require(ids==oldrow['source_cue_indices'],'PARENT_CUE_DRIFT')
        for idx in ids:require((v,idx) in cue_map and cue_map[(v,idx)]['window_id']==win,'PARENT_SOURCE_SCOPE')
        require(sha(' | '.join(cue_map[(v,i)]['text_private'] for i in ids))==p['source_parent_sha256'],'PARENT_TEXT_DRIFT')
        units=p.get('units');require(type(units)==list and bool(units),'PARENT_UNDECOMPOSED')
        local_cover=set()
        for u in units:
            require(type(u)==dict,'UNIT_TYPE')
            uid=u.get('unit_id');require(type(uid)==str and uid and uid not in units_seen,'UNIT_DUP');units_seen.add(uid)
            role=u.get('role');require(role in ROLES,'UNIT_ROLE')
            ix=u.get('source_cue_indices');require(type(ix)==list and bool(ix) and len(ix)==len(set(ix)) and all(type(i)==int for i in ix),'UNIT_INDICES')
            require(set(ix)<=set(ids),'CROSS_PARENT_UNIT')
            src=[cue_map[(v,i)] for i in ix];require(u.get('source_cues_digest_sha256')==sha(''.join(c['cue_sha256'] for c in src)),'UNIT_CUE_SHA')
            require(type(u.get('meaning_private')) is str and len(u['meaning_private'].strip())>=8,'UNIT_MEANING_MISSING')
            for field in ('contextual_conditions_private','spoken_exceptions','spoken_rebuttal','reviewer_limits','open_reason'):
                require(type(u.get(field)) is str,'UNIT_SCOPE_FIELD')
            if role=='CONDITION':require(bool(u['contextual_conditions_private']),'CONDITION_NOT_PRESERVED')
            if role=='REBUTTAL':require(bool(u['spoken_rebuttal']),'REBUTTAL_NOT_PRESERVED')
            if role in ('UNCERTAIN_AUDIO','OPEN_FRAGMENT'):require(bool(u['open_reason']),'OPEN_NOT_RECORDED')
            require(u.get('approved_financial_fact') is False and u.get('independent_gold') is False and u.get('personal_advice_approved') is False,'FALSE_UNIT_APPROVAL')
            raw=[n for c in src for n in NUM.findall(c['text_private'])]
            polarity=[n for c in src for n in POLARITY.findall(c['text_private'])]
            contrast=[n for c in src for n in CONTRAST.findall(c['text_private'])]
            require(u.get('numeric_surface_forms')==raw,'NUMERIC_SCOPE_LOST')
            require(u.get('source_polarity_surface_forms')==polarity,'POLARITY_SURFACE_LOST')
            if contrast: require(bool(u['spoken_exceptions']) or bool(u['spoken_rebuttal']),'SOURCE_CONTRAST_UNACCOUNTED')
            local_cover.update(ix);all_new_covered.update((v,i) for i in ix)
            units_count+=1;unit_roles[role]+=1;numbers+=len(raw);polarity_mentions+=len(polarity);source_contrast_mentions+=len(contrast)
            condition_units+=bool(u['contextual_conditions_private']);source_exception_units+=bool(u['spoken_exceptions']);speaker_rebuttal_units+=bool(u['spoken_rebuttal']);review_open_units+=bool(u['open_reason'])
        require(local_cover==set(ids),'PARENT_HAS_UNACCOUNTED_CUES')
        parent_covered.add(key)
    require(seen==set(old),'PARENT_SET_CHANGED')
    if expected_units is not None:require(units_count==expected_units,'UNIT_CENSUS')
    original_parent_cues={(v,i) for (v,_),p in old.items() for i in p['source_cue_indices']}
    gaps=decomposition.get('unassigned_cues');require(type(gaps)==list and len(gaps)==expected_gaps,'GAP_COUNT')
    gap_keys=set()
    for g in gaps:
        require(type(g)==dict,'GAP_ROW')
        key=(g.get('video_id'),g.get('cue_index'))
        require(key in cue_map and key not in original_parent_cues and key not in gap_keys,'GAP_WRONG_SCOPE_DUP');gap_keys.add(key)
        require(g.get('window_id')==cue_map[key]['window_id'] and g.get('cue_sha256')==cue_map[key]['cue_sha256'],'GAP_SHA')
        require(type(g.get('role_private')) is str and len(g['role_private'])>=8,'GAP_MISSING_ROLE')
        require(g.get('independent_gold') is False and g.get('claim_absence_certified') is False,'GAP_FALSE_APPROVAL')
    require(all_new_covered==original_parent_cues,'CUED_PARENT_CONSERVATION')
    require(all_new_covered|gap_keys==set(cue_map) and not (all_new_covered&gap_keys),'SOURCE_CUE_CONSERVATION')
    issues=old_counterexamples.get('issues')
    require(type(issues)==list,'PRIOR_ISSUES')
    if expected_counterexamples is not None:require(len(issues)==expected_counterexamples,'PRIOR_ISSUE_COUNT')
    issue_ids=set();prior_counterexample_links=0
    for issue in issues:
        require(type(issue)==dict and type(issue.get('issue_id'))==str and issue['issue_id'] not in issue_ids,'PRIOR_ISSUE_DUP')
        issue_ids.add(issue['issue_id'])
        v,w,a,b=issue.get('video_id'),issue.get('window_id'),issue.get('first_cue'),issue.get('last_cue')
        require(type(a)==int and type(b)==int and a<=b and all((v,i) in cue_map and cue_map[(v,i)]['window_id']==w for i in range(a,b+1)),'PRIOR_ISSUE_SOURCE_SPAN')
        require(issue.get('source_span_sha256')==sha(''.join(cue_map[(v,i)]['cue_sha256'] for i in range(a,b+1))),'PRIOR_ISSUE_SHA')
        links=issue.get('linked_v33_parent_ids')
        require(type(links)==list and bool(links) and len(links)==len(set(links)),'PRIOR_ISSUE_LINKS')
        for cid in links:
            key=(v,cid);require(key in parent_key_by_id,'PRIOR_ISSUE_UNKNOWN_PARENT')
            require(any(bool(set(u['source_cue_indices'])&set(range(a,b+1))) for u in parent_key_by_id[key]['units']),'PRIOR_ISSUE_NOT_REPRESENTED')
        prior_counterexample_links+=1
    old_atoms_list=old_atoms.get('source_atoms_provisional');require(type(old_atoms_list)==list and len(old_atoms_list)>0,'OLD_ATOMS')
    old_cov=set()
    for a in old_atoms_list:
        v=a['video_id'];idx=a['source_cue_indices'];require(type(idx)==list and bool(idx),'OLD_ATOM_SPAN')
        require(all((v,i) in cue_map for i in idx),'OLD_ATOM_CUE_MISSING')
        require(a['source_cues_digest_sha256']==sha(''.join(cue_map[(v,i)]['cue_sha256'] for i in idx)),'OLD_ATOM_DRIFT')
        old_cov.update((v,i) for i in idx)
    old_any=sum(any((p['video_id'],i) in old_cov for i in p['source_cue_indices']) for p in old.values())
    old_full=sum(all((p['video_id'],i) in old_cov for i in p['source_cue_indices']) for p in old.values())
    edges=decomposition.get('cross_parent_edges');require(type(edges)==list,'EDGES')
    kinds=Counter();uniq=set()
    for e in edges:
        require(type(e)==dict and e.get('type') in EDGE_TYPES,'EDGE_TYPE')
        v=e.get('video_id');src=(v,e.get('source_parent_id'));dest=(v,e.get('target_parent_id'))
        require(src in old and dest in old and src!=dest,'EDGE_SCOPE')
        k=(src,dest,e['type']);require(k not in uniq,'EDGE_DUP');uniq.add(k)
        require(type(e.get('reason_private')) is str and len(e['reason_private'])>=10,'EDGE_REASON')
        kinds[e['type']]+=1
    for flag in ('all_financial_atomic_claims_certified','independent_gold','p0_go','personal_advice_approved','financial_law_application_certified'):
        require(decomposition.get(flag) is False,'FALSE_GO_'+flag)
    require(decomposition.get('new_financial_knowledge_approved')==0,'FALSE_APPROVAL_COUNT')
    result={'schema':'V110_SOURCE_CUE_PARENT_AND_SPEECH_ACT_COVERAGE_SHA_ONLY_NOT_SEMANTIC_GOLD_V1',
            'source_zip_sha256':source_zip_sha,'original_cues':len(cue_map),'original_windows':len(groups),
            'parent_candidates':len(old),'unassigned_cues':len(gap_keys),
            'v109_atomic_parts':len(old_atoms_list),'v109_counterexample_spans_preserved':prior_counterexample_links,'v109_cues_linked_to_atoms':len(old_cov),
            'v109_cues_not_linked_to_atoms':len(cue_map)-len(old_cov),
            'v109_parents_with_any_atom_cue':old_any,'v109_parents_all_cues_in_atoms':old_full,
            'v110_speech_act_units':units_count,'v110_parent_cue_links_covered':len(all_new_covered),
            'v110_source_cues_accounted_including_gaps':len(all_new_covered|gap_keys),
            'v110_parents_all_cues_classified':len(parent_covered),'v110_unit_roles':dict(sorted(unit_roles.items())),
            'source_condition_units':condition_units,'source_exception_or_contrast_units':source_exception_units,
            'source_self_rebuttal_units':speaker_rebuttal_units,'provisional_open_units':review_open_units,
            'number_surface_forms_source_preserved':numbers,'source_polarity_mentions_preserved':polarity_mentions,
            'source_contrast_mentions_preserved':source_contrast_mentions,'cross_parent_scope_edges':len(edges),
            'edge_type_counts':dict(sorted(kinds.items())),
            'source_cue_identity_digest_sha256':digest([[v,i,c['cue_sha256']] for (v,i),c in sorted(cue_map.items())]),
            'private_parent_unit_digest_sha256':digest([[p['video_id'],p['draft_parent_id'],[(u['unit_id'],u['source_cues_digest_sha256'],sha(u['meaning_private']),sha(u['reviewer_limits'])) for u in p['units']]] for p in parents]),
            'private_edge_digest_sha256':digest([[e['video_id'],e['source_parent_id'],e['target_parent_id'],e['type'],sha(e['reason_private'])] for e in edges]),
            'structural_source_coverage_complete':True,'semantic_claim_recall_certified':False,
            'all_financial_atomic_claims_certified':False,'certified_precision':None,'certified_recall':None,
            'current_financial_law_application_certified':False,'independent_gold':False,
            'p0_go':False,'personal_advice_approved':False,'new_financial_knowledge_approved':0}
    return result

def check_public_receipt(receipt,computed):
    require(type(receipt)==dict and type(computed)==dict,'RECEIPT_TYPES')
    require(receipt==computed,'RECEIPT_DRIFT')
    for k in ('independent_gold','p0_go','personal_advice_approved','all_financial_atomic_claims_certified','semantic_claim_recall_certified','current_financial_law_application_certified'):
        require(receipt.get(k) is False,'RECEIPT_FALSE_GO')
    require(receipt.get('certified_precision') is None and receipt.get('certified_recall') is None,'RECEIPT_FAKE_SCORE')
    require(not any(k in receipt for k in ('parent_records_private','raw_cues','private_notes')),'RECEIPT_PRIVATE_LEAK')
    return True