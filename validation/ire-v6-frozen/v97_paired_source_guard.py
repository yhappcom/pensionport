"""V97 source-first paired V91 vs V96 shadow comparator (NO independent gold).

The private source stays outside GitHub. Verifies evidence identities, candidate
census, cue-risk alert fingerprints and single-host issue span arithmetic.
It does not certify finance truth, independent precision/recall, or P0 GO.
"""
from __future__ import annotations
import hashlib,json
from collections import Counter
WINDOWS=(('6VEfKF7BzZU','W00026',13,5),
         ('qtluAViPpsQ','W00018',19,4),
         ('4CQ4FjGT2gA','W00117',12,9),
         ('4CQ4FjGT2gA','W00053',17,3),
         ('4CQ4FjGT2gA','W00096',16,0))
V91='732efc8c2dffcd64828de5188168a694f0133ce6'
V96='6825d90fefcea3645dbad60e3c2051d3f41475b4'
SOURCE_ARCHIVE='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
NO_GO_FIELDS=('independent_gold','p0_go','automatic_personal_advice_approved','certified_financial_accuracy')

def require(c,code):
    if not c:raise ValueError('V97_'+code)
def sha(s):return hashlib.sha256(s.encode('utf-8') if isinstance(s,str) else s).hexdigest()
def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def source_first_paired_check(source_cues,parents,flags,internal_issues,*,original_archive_sha,prior_windows):
    require(original_archive_sha==SOURCE_ARCHIVE,'OWNER_ARCHIVE_SHA')
    require(type(source_cues)==list and len(source_cues)==200,'SOURCE_200')
    require(type(parents)==list and len(parents)==77,'PARENT_77')
    require(type(flags)==list and len(flags)==21,'FLAG_21')
    require(type(internal_issues)==list and len(internal_issues)==20,'SINGLE_HOST_ISSUE_20')
    require(type(prior_windows)==set,'PRIOR_TYPE')
    scopes={(v,w):(nparents,nflags) for v,w,nparents,nflags in WINDOWS}
    require(len(scopes)==5,'SCOPE_DUP')
    cue_map={};per_win=Counter()
    for row in source_cues:
        require(type(row)==dict,'CUE_ROW')
        key=(row.get('video_id'),row.get('window_id'))
        i=row.get('cue_index')
        require(key in scopes and type(i) is int,'WRONG_SCOPE')
        require(key not in prior_windows,'REVIEWED_WINDOW')
        require((int(key[1][1:])-1)*40<i<=int(key[1][1:])*40,'WINDOW_CUE_INDEX')
        require((key[0],i) not in cue_map,'CUE_DUP')
        require(type(row.get('text_private')) is str and row['text_private'],'CUE_TEXT')
        require(row.get('cue_sha256')==sha(row['text_private']),'CUE_SHA')
        cue_map[(key[0],i)]=row;per_win[key]+=1
    require(set(per_win)==set(scopes) and all(v==40 for v in per_win.values()),'WINDOW_NOT_40')
    parent_map={};assigned=set();pcount=Counter()
    for row in parents:
        key=(row.get('video_id'),row.get('window_id'))
        cid=row.get('claim_id')
        require(key in scopes and type(cid) is str and cid,'PARENT_SCOPE')
        pk=(*key,cid);require(pk not in parent_map,'PARENT_DUP');parent_map[pk]=row;pcount[key]+=1
        ids=row.get('cue_indices')
        require(type(ids) is list and ids and len(set(ids))==len(ids),'PARENT_CUES')
        actual=[]
        for i in ids:
            ci=(key[0],i)
            require(ci in cue_map and ci not in assigned,'PARENT_OVERLAP')
            assigned.add(ci);actual.append(cue_map[ci]['text_private'])
        require(row.get('source_text_sha256')==sha(' | '.join(actual)),'PARENT_SHA')
    require(all(pcount[k]==want[0] for k,want in scopes.items()),'PARENT_COUNT_DRIFT')
    seen_flags=set();fcount=Counter()
    for f in flags:
        key=(f.get('video_id'),f.get('window_id'))
        i=f.get('cue_index');kind=f.get('kind')
        require(key in scopes and type(kind) is str and kind,'FLAG_SCOPE')
        require((key[0],i) in cue_map,'FLAG_ORIGINAL_CUE')
        require(f.get('cue_sha256')==cue_map[(key[0],i)]['cue_sha256'],'FLAG_SHA')
        fk=(*key,i,kind);require(fk not in seen_flags,'DUP_FLAG');seen_flags.add(fk);fcount[key]+=1
    require(all(fcount[k]==want[1] for k,want in scopes.items()),'FLAG_COUNT_DRIFT')
    n_covered=0;unmatched=0;issue_cue_sets=[];issids=set()
    for i in internal_issues:
        require(type(i)==dict,'ISSUE_ROW')
        key=(i.get('video_id'),i.get('window_id'))
        a=i.get('first_cue');b=i.get('last_cue')
        require(key in scopes and type(a) is int and type(b) is int and a<=b,'ISSUE_RANGE')
        ik=(key,a,b);require(ik not in issids,'ISSUE_DUP');issids.add(ik)
        require(i.get('independent_gold') is False and i.get('actual_error_certified') is False,'FAKE_GOLD')
        txt=[cue_map[(key[0],k)]['cue_sha256'] for k in range(a,b+1) if (key[0],k) in cue_map]
        require(len(txt)==b-a+1,'ISSUE_SOURCE_GAP')
        require(i.get('source_span_sha256')==sha(''.join(txt)),'ISSUE_SHA')
        require(type(i.get('note_private')) is str and len(i['note_private'])>10,'ISSUE_CONTEXT_MISSING')
        issue_cue_sets.append({(key[0],k) for k in range(a,b+1)})
        if any((*key,k,kind) in seen_flags for k in range(a,b+1) for kind in ['QUALIFIER_REVIEW','ASR_REVIEW','COMPOUND_REVIEW','MULTINUMERIC_REVIEW']):n_covered+=1
    for f in flags:
        if not any((f['video_id'],f['cue_index']) in x for x in issue_cue_sets):unmatched+=1
    alarm_cues={(f['video_id'],f['cue_index']) for f in flags}
    envelope=set()
    for f in flags:
        first=(int(f['window_id'][1:])-1)*40+1;last=first+39
        for idx in range(max(first,f['cue_index']-7),min(last,f['cue_index']+7)+1):envelope.add((f['video_id'],idx))
    return {'cues':len(cue_map),'parents':len(parent_map),'assigned':len(assigned),
            'unassigned':len(cue_map)-len(assigned),'alerts':len(flags),'alerted_cues':len(alarm_cues),
            'internal_issues_not_gold':len(internal_issues),'internal_issue_spans_with_alert':n_covered,
            'internal_issue_spans_without_alert':len(internal_issues)-n_covered,
            'alert_events_outside_annotated_issue_spans':unmatched,
            'alert_context_unique_cues':len(envelope),'zero_alert_windows':sum(fcount[k]==0 for k in scopes),
            'p0_go':False,'independent_gold':False,'certified_financial_accuracy':False,
            'full_semantic_recall_certified':False,'can_replace_full_source_review':False}

def check_public_receipt(receipt,scope):
    require(type(scope)==dict and type(receipt)==dict,'INPUT_TYPES')
    require(scope.get('v91_baseline_commit')==V91 and scope.get('v96_comparison_commit')==V96,'COMMIT_PIN')
    require(scope.get('owner_archive_sha256')==SOURCE_ARCHIVE and receipt.get('source_archive_sha256')==SOURCE_ARCHIVE,'SOURCE_PIN')
    require(scope.get('independent_gold') is False and receipt.get('gold_independent') is False,'FALSE_INDEPENDENT_GOLD')
    require(scope.get('p0_go') is False and receipt.get('p0_go') is False,'FALSE_P0_GO')
    require(receipt.get('original_cues')==200 and receipt.get('v91_provisional_draft_parents')==77,'CENSUS')
    require(receipt.get('v96_cue_risk_signal_events')==21,'ALERT_COUNT')
    require(receipt.get('internal_source_first_issue_spans_not_gold')==20,'ISSUES')
    require(receipt.get('v96_internal_issue_spans_any_alert')+receipt.get('v96_internal_issue_spans_no_alert')==20,'ISSUE_CONSERVATION')
    require(receipt.get('certified_financial_precision') is None and receipt.get('certified_financial_recall') is None,'FALSE_PRECISION_RECALL')
    require(receipt.get('model_semantic_token_time_measured') is False and receipt.get('human_review_time_measured') is False,'FALSE_LATENCY')
    require(receipt.get('v96_unique_cues_within_7_neighbor_envelopes')<=200,'ENVELOPE_OVERFLOW')
    require(receipt.get('v96_internal_issue_spans_no_alert')>0,'FALSE_FULL_DETECTION')
    return {'structure_checked':True,'performance_not_financial_quality':True,'p0_go':False}