"""V102 owner-side source-locked V98 pending->CHAT shadow overlay for V101+V102.

Never mutates V98 baseline, historical V92, V40, P4, Master116, or main.
Public synthetic tests only; private source text supplied by owner outside GitHub.
CHAT-context review is not an independent gold or financial fact approval.
"""
from __future__ import annotations
import hashlib,json
from collections import Counter
SOURCE_ARCHIVE_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V98_ARCHIVE_SHA='e55d58b931cde6261fb76c79c7df011256a565f6e08ce5236894aa077c4edabd'
V101_ARCHIVE_SHA='02b6409fed1595c1cd89c6b18fb1e8439953ccd6165a43831c4e613fd6031b2c'
V101_HEAD='1bc2e4120759c2c94188bb7dfd446eba622171cd'
NEW_SCOPE=(('sz5N9WJS310','W00009',1,12,39),('4CQ4FjGT2gA','W00033',7,16,0))
ALLOWED_V96_PRIOR_CUE_CROSSREFERENCE={('sz5N9WJS310','W00009',332)}
NEW_SPLITS={('sz5N9WJS310','W00009','C00105'),('4CQ4FjGT2gA','W00033','C00504'),('4CQ4FjGT2gA','W00033','C00506'),('4CQ4FjGT2gA','W00033','C00512')}
REVIEWED='CHAT_CONTEXT_REVIEWED_SHADOW_NOT_INDEPENDENT_GOLD'
FALSE=('independent_gold','financial_fact_approved','personal_advice_approved','p0_go','formal_master_merged','atomic_recall_certified','current_law_certified','audio_verified')

def require(ok,code):
    if not ok:raise ValueError('V102_'+code)
def sha(x):return hashlib.sha256(x.encode('utf-8') if isinstance(x,str) else x).hexdigest()
def digest(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False))

def reconcile(baseline, v101_selected, v101_receipt, new_selected, new_parents,
              new_gaps, new_splits, cues_by_video, registries, *,
              source_zip_sha, v98_zip_sha, v101_zip_sha,
              prior_shadow_parent_keys, v96_reviewed_cue_keys, v97_windows):
    require((source_zip_sha,v98_zip_sha,v101_zip_sha)==(SOURCE_ARCHIVE_SHA,V98_ARCHIVE_SHA,V101_ARCHIVE_SHA),'PIN_SHA')
    require(type(prior_shadow_parent_keys) is set and type(v96_reviewed_cue_keys) is set and type(v97_windows) is set,'PRIOR_TYPE')
    require(type(baseline) is list and len(baseline)==15857,'V98_COUNT')
    base={};base_status=Counter()
    for raw in baseline:
        require(type(raw) is list and len(raw)==8,'V98_ROW')
        v,w,i,h,parent,route,reviewed,gold=raw
        k=(v,w,i);require(k not in base and isinstance(i,int) and isinstance(h,str) and len(h)==64,'V98_KEY_DUP')
        require(route in {'PRIORITY_PARENT_PENDING','BASELINE_PARENT_PENDING','PRIORITY_UNASSIGNED_PENDING','BASELINE_UNASSIGNED_PENDING'},'V98_ROUTE')
        require(reviewed is False and gold is False,'V98_FALSE_COMPLETION')
        require(('UNASSIGNED' in route)==(parent is None),'V98_PARENT_ROUTE')
        base[k]=raw;base_status[route]+=1
    require(len(base)==15857,'V98_DUP');require(sum(base_status.values())==15857,'V98_STATUS_CONSERVATION')
    require(type(v101_selected) is list and len(v101_selected)==240,'V101_240')
    require(type(v101_receipt) is dict and v101_receipt.get('source_bound_cues_context_reviewed_chat')==240
      and v101_receipt.get('source_bound_parent_draft_readings_chat')==81
      and v101_receipt.get('source_bound_gap_speech_acts_chat')==7
      and v101_receipt.get('independent_gold') is False and v101_receipt.get('p0_go') is False,'V101_INTEGRITY')
    prior_ids=set();v101_digest=[]
    for r in v101_selected:
        k=(r['video_id'],r['window_id'],r['cue_index'])
        require(k in base and k not in prior_ids,'V101_DUP_OR_MISSING')
        require(r['cue_sha256']==base[k][3] and r['parent_id']==base[k][4],'V101_ROUTE_DRIFT')
        require(r['context_sha256']==digest(r['context_private']),'V101_CONTEXT_SHA')
        require(r['source_text_private']==cues_by_video[k[0]][k[2]-1].text,'V101_SOURCE_TEXT')
        require(sha(r['source_text_private'])==r['cue_sha256'],'V101_SOURCE_SHA')
        prior_ids.add(k);v101_digest.append([*k,r['cue_sha256'],r['context_sha256']])
    require(digest(sorted(v101_digest))==v101_receipt.get('source_receipt_sha256'),'V101_RECEIPT_DIGEST')
    require(type(new_selected) is list and len(new_selected)==80,'NEW_80')
    require(type(new_parents) is list and len(new_parents)==28,'NEW_28')
    require(type(new_gaps) is list and len(new_gaps)==1,'NEW_1_GAP')
    require(type(new_splits) is list and len(new_splits)==4,'NEW_4_SPLITS')
    newkeys=set();bywin=Counter();priority=Counter();src_custody=[]
    scopes={(v,w):(no,pc,q) for v,w,no,pc,q in NEW_SCOPE};require(len(scopes)==2,'NEW_SCOPE_DUP')
    for r in new_selected:
        k=(r.get('video_id'),r.get('window_id'),r.get('cue_index'));v,w,i=k
        require((v,w) in scopes and type(i) is int and k in base and k not in prior_ids and k not in newkeys,'NEW_SOURCE_DUP')
        require((v,w) not in v97_windows,'PRIOR_V97_WINDOW_COLLISION')
        if (v,i) in v96_reviewed_cue_keys:
            require(k in ALLOWED_V96_PRIOR_CUE_CROSSREFERENCE,'UNEXPECTED_V96_CUE_COLLISION')
        first=(int(w[1:])-1)*40+1;require(first<=i<first+40,'NEW_CUE_WINDOW')
        c=cues_by_video[v][i-1]
        require((r.get('start_ms'),r.get('end_ms'),r.get('source_text_private'))==(c.start_ms,c.end_ms,c.text),'NEW_ORIGINAL_CUE')
        require(r.get('cue_sha256')==sha(c.text)==base[k][3],'NEW_SOURCE_SHA')
        context=[{'cue_index':j,'text_private':cues_by_video[v][j-1].text}
           for j in range(max(1,i-2),min(len(cues_by_video[v]),i+2)+1)]
        require(r.get('context_private')==context and r.get('context_sha256')==digest(context),'NEW_CONTEXT')
        require(r.get('parent_id')==base[k][4],'NEW_ROUTE_PARENT')
        newkeys.add(k);bywin[(v,w)]+=1;src_custody.append([*k,r['cue_sha256'],r['context_sha256']])
        if base[k][5].startswith('PRIORITY_'):priority[(v,w)]+=1
    require(all(bywin[(v,w)]==40 and priority[(v,w)]==q for (v,w),(no,pc,q) in scopes.items()),'NEW_WINDOW_PRIORITY')
    expectedparents={};assigned=set();pcount=Counter()
    for v,w,no,pc,q in NEW_SCOPE:
        reg=registries[v][w];require(len(reg)==pc,'NEW_REGISTRY_COUNT')
        for p in reg:
            key=(v,w,p['claim_id']);require(key not in prior_shadow_parent_keys and key not in expectedparents,'PARENT_OLD_OR_DUP')
            ix=p['cue_indices'];require(type(ix) is list and ix and len(set(ix))==len(ix),'PARENT_CUES')
            for i in ix:
                k=(v,w,i);require(k in newkeys and k not in assigned and base[k][4]==p['claim_id'],'PARENT_ASSIGNMENT')
                assigned.add(k)
            require(p['source_text_sha256']==sha(' | '.join(cues_by_video[v][i-1].text for i in ix)),'PARENT_HASH')
            expectedparents[key]=p;pcount[(v,w)]+=1
    readings={};parent_receipts=[]
    for r in new_parents:
        key=(r.get('video_id'),r.get('window_id'),r.get('parent_id'))
        require(key in expectedparents and key not in readings,'READING_DUP_OR_MISSING')
        p=expectedparents[key]
        require(r.get('cue_indices')==p['cue_indices'] and r.get('parent_sha256')==p['source_text_sha256'],'READING_SOURCE_ID')
        require(r.get('source_text_private')==' | '.join(cues_by_video[key[0]][i-1].text for i in p['cue_indices']),'READING_SOURCE_TEXT')
        require(type(r.get('semantic_kind')) is str and r['semantic_kind'],'READING_KIND')
        require(all(type(r.get(f)) is str and len(r[f])>=20 for f in ('speaker_meaning_private','reviewer_scope_caution_private')),'READING_MEANING')
        require(r.get('review_status')==REVIEWED and all(r.get(f) is False for f in FALSE),'READING_FALSE_GO')
        readings[key]=r;parent_receipts.append([*key,r['parent_sha256'],r['semantic_kind'],sha(r['speaker_meaning_private']),sha(r['reviewer_scope_caution_private'])])
    require(set(readings)==set(expectedparents),'PARENT_REVIEW_NOT_COMPLETE')
    gapkeys=newkeys-assigned
    require(len(gapkeys)==1 and gapkeys=={('4CQ4FjGT2gA','W00033',1281)},'NEW_GAP_CENSUS')
    got=set();gap_receipts=[]
    for g in new_gaps:
        k=(g.get('video_id'),g.get('window_id'),g.get('cue_index'));require(k in gapkeys and k not in got,'GAP_SOURCE')
        require(g.get('source_text_private')==cues_by_video[k[0]][k[2]-1].text and g.get('cue_sha256')==base[k][3],'GAP_SOURCE_SHA')
        require(g.get('speech_act') in {'ASSENT','INTERJECTION','LAUGHTER','FRAGMENT'},'GAP_KIND')
        require(type(g.get('reason_private')) is str and len(g['reason_private'])>=20,'GAP_REASON')
        require(g.get('review_status')==REVIEWED and g.get('negative_gold') is False and all(g.get(f) is False for f in FALSE),'GAP_FALSE_NEGATIVE')
        got.add(k);gap_receipts.append([*k,g['cue_sha256'],g['speech_act'],sha(g['reason_private'])])
    require(got==gapkeys,'GAP_MISSING')
    gotsp=set();split_receipts=[]
    for sp in new_splits:
        key=(sp.get('video_id'),sp.get('window_id'),sp.get('parent_id'))
        require(key in NEW_SPLITS and key not in gotsp,'SPLIT_DUP_OR_SCOPE')
        require(sp.get('review_status')==REVIEWED and all(sp.get(f) is False for f in FALSE),'SPLIT_FALSE_GO')
        ix=set(expectedparents[key]['cue_indices']);seen=set();parts=sp.get('parts')
        require(type(parts) is list and len(parts)==2,'SPLIT_PART_COUNT')
        chunks=[]
        for a in parts:
            sub=a.get('cue_indices');require(type(sub) is list and sub and len(sub)==len(set(sub)),'SPLIT_DUP_CUE')
            require(set(sub)<=ix and not set(sub)&seen,'SPLIT_OVERLAP')
            require(type(a.get('meaning_private')) is str and len(a['meaning_private'])>=12 and a.get('gold') is False,'SPLIT_NOT_GOLD')
            seen.update(sub);chunks.append([sub,sha(a['meaning_private'])])
        require(seen==ix,'SPLIT_UNCOVERED')
        gotsp.add(key);split_receipts.append([*key,chunks])
    require(gotsp==NEW_SPLITS,'SPLIT_MISSING')
    require(len(prior_ids|newkeys)==320 and not prior_ids.intersection(newkeys),'OVERLAY_UNION')
    prior_v96_overlap={k for k in newkeys if (k[0],k[2]) in v96_reviewed_cue_keys}
    require(prior_v96_overlap==ALLOWED_V96_PRIOR_CUE_CROSSREFERENCE,'V96_CROSSREFERENCE_CENSUS')
    overlay=[];reviewed_status=Counter();remain_status=Counter(base_status)
    for k in sorted(prior_ids|newkeys):
        raw=base[k]
        remain_status[raw[5]]-=1;reviewed_status[raw[5]]+=1
        overlay.append({'video_id':k[0],'window_id':k[1],'cue_index':k[2],
             'original_cue_sha256':raw[3],'original_parent_id':raw[4],
             'original_pending_route':raw[5],'shadow_review_state':REVIEWED,
             'independent_gold':False,'fact_approved':False,'personalized_advice_approved':False,
             'official_knowledge_merged':False})
    require(sum(remain_status.values())==15537 and all(v>=0 for v in remain_status.values()),'PENDING_CONSERVATION')
    require(sum(reviewed_status.values())==320 and sum(v for k,v in reviewed_status.items() if k.startswith('PRIORITY_'))==172,'REVIEW_ROUTE_CONSERVATION')
    result={'schema':'V102_V98_PENDING_NONMUTATING_V101_240_PLUS_V102_80_REVIEW_SHADOW_OVERLAY_V1',
      'v98_baseline_cues':15857,'v98_baseline_parents':4944,'v98_baseline_gaps':290,
      'previous_v101_cues':240,'new_v102_cues_in_overlay':80,
      'new_v102_cues_not_previously_v96_adjudicated':79,'v96_existing_cue_crossreferences_not_double_counted':1,
      'v96_cue_crossreference_source_sha256':digest(sorted([(*k,base[k][3]) for k in prior_v96_overlap])),
      'cumulative_shadow_reviewed_cues':320,
      'still_pending_cues':15537,'cumulative_shadow_reviewed_parents':109,
      'cumulative_shadow_reviewed_gaps':8,'v102_new_parents':28,'v102_new_gaps':1,
      'v102_new_splits':4,'new_source_receipt_sha256':digest(sorted(src_custody)),
      'new_parent_meaning_receipt_sha256':digest(sorted(parent_receipts)),
      'new_gap_meaning_receipt_sha256':digest(sorted(gap_receipts)),
      'new_split_meaning_receipt_sha256':digest(sorted(split_receipts)),
      'overlay_digest_sha256':digest(overlay),
      'v101_source_receipt_sha256':v101_receipt['source_receipt_sha256'],
      'new_windows':[[v,w] for v,w,_,_,_ in NEW_SCOPE],
      'v102_priority_cues':39,'v102_fallback_cues':41,
      'cumulative_priority_reviewed':172,'cumulative_fallback_reviewed':148,
      'reviewed_route_counts':dict(sorted(reviewed_status.items())),
      'pending_route_counts':dict(sorted(remain_status.items())),
      'v98_baseline_mutated':False,'v101_original_archive_mutated':False,
      'v75_historical_identity_verified':False,'current_financial_law_verified':False,
      'true_atomic_claim_recall_certified':False,'independent_gold':False,
      'certified_precision':None,'certified_recall':None,
      'new_approved_knowledge':0,'p4_master116_merged':False,
      'personal_advice_approved':False,'p0_go':False}
    return result,overlay