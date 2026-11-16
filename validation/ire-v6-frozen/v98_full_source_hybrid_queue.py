"""Generic V98 source-wide risk-first + compulsory fallback pending worklist.

All original 40-cue windows and every V33 draft parent are enumerated even
when there is *zero* lexical risk signal. A completed route is NOT a completed
semantic review. This code is safe for public synthetic tests (no owner text).
"""
from __future__ import annotations
from collections import Counter
from v98_hybrid_source_guard import sha,digest,require,ALERT_KINDS

PENDING={'PRIORITY_PARENT_PENDING','PRIORITY_UNASSIGNED_PENDING',
         'BASELINE_PARENT_PENDING','BASELINE_UNASSIGNED_PENDING'}

def full_source_hybrid(cues_byvid,registries_byvid,alerts_byvid,*,expected_source_sha,
                       source_archive_sha,radius=7,include_private_queue=False):
    require(expected_source_sha==source_archive_sha and len(expected_source_sha)==64,'SOURCE_ARCHIVE_PIN')
    require(type(radius) is int and radius==7,'RADIUS_7')
    require(type(include_private_queue) is bool,'PRIVATE_FLAG')
    require(type(cues_byvid) is dict and cues_byvid,'SOURCE_INPUT')
    require(set(cues_byvid)==set(registries_byvid)==set(alerts_byvid),'SOURCE_SCOPE_MATCH')
    route=[];parents=[];unassigned=[];per_video={};glob=Counter();zero_windows=0
    for vid in sorted(cues_byvid):
        cues=cues_byvid[vid];regs=registries_byvid[vid];a=alerts_byvid[vid]
        require(type(vid) is str and vid and type(cues) is list and cues,'VIDEO_INPUT')
        width=(len(cues)+39)//40
        require(type(regs) is dict and len(regs)==width,'REGISTRY_WINDOW_CENSUS')
        bycue={};laststart=-1
        for k,c in enumerate(cues,1):
            require(c.index==k and c.start_ms>=laststart and c.end_ms>=c.start_ms,'SOURCE_CUE_ORDER')
            laststart=c.start_ms
            require(type(c.text) is str and bool(c.text),'SOURCE_TEXT')
            bycue[k]=sha(c.text)
        assigned={};seenparents=set();per_parent=0
        for w in range(1,width+1):
            wid=f'W{w:05d}';require(wid in regs,'MISSING_WINDOW')
            first=(w-1)*40+1;last=min(w*40,len(cues))
            require(type(regs[wid]) is list,'REGISTRY_LIST')
            for p in regs[wid]:
                cid=p.get('claim_id')
                require(type(cid) is str and cid not in seenparents,'CLAIM_ID_DUP')
                seenparents.add(cid)
                indices=p.get('cue_indices')
                require(type(indices) is list and indices and len(indices)==len(set(indices)),'CLAIM_CUES')
                require(all(type(i) is int and first<=i<=last for i in indices),'CROSS_WINDOW_CLAIM')
                for i in indices:
                    require(i not in assigned,'OVERLAPPING_CLAIM');assigned[i]=cid
                expected=sha(' | '.join(cues[i-1].text for i in indices))
                require(p.get('source_text_sha256')==expected,'PARENT_TEXT_SHA')
                parents.append([vid,wid,cid,expected,False])
                per_parent+=1
        require(len(assigned)<=len(cues),'ASSIGNMENT_OVERFLOW')
        alertkeys=set();alert_positions=set();perw=Counter()
        for x in a:
            require(type(x) is dict and type(x.get('cue_index')) is int,'ALERT_TYPE')
            i=x['cue_index'];kind=x.get('kind')
            require(1<=i<=len(cues) and kind in ALERT_KINDS,'ALERT_INPUT')
            require(x.get('cue_sha256')==bycue[i],'ALERT_SOURCE_SHA')
            key=(i,kind);require(key not in alertkeys,'DUP_ALERT')
            alertkeys.add(key);alert_positions.add(i);perw[(i-1)//40+1]+=1
        priority=set()
        for i in alert_positions:
            first=(i-1)//40*40+1;last=min(first+39,len(cues))
            priority.update(range(max(first,i-radius),min(last,i+radius)+1))
        for w in range(1,width+1):
            if perw[w]==0:zero_windows+=1
        local=Counter()
        for i in range(1,len(cues)+1):
            w=f'W{((i-1)//40+1):05d}'
            pri=i in priority;has=i in assigned
            status=('PRIORITY_' if pri else 'BASELINE_')+('PARENT_PENDING' if has else 'UNASSIGNED_PENDING')
            require(status in PENDING,'STATUS_NOT_PENDING')
            row=[vid,w,i,bycue[i],assigned.get(i),status,False,False]
            route.append(row);local[status]+=1
            if not has:unassigned.append([vid,w,i,bycue[i],status])
        per_video[vid]={'cue_count':len(cues),'windows':width,'parents':per_parent,
            'alerts':len(alertkeys),'alerted_cues':len(alert_positions),
            'priority_cues':len(priority),'fallback_cues':len(cues)-len(priority),
            'unassigned_cues':len(cues)-len(assigned),
            'zero_alert_windows':sum(perw[w]==0 for w in range(1,width+1)),
            'route_counts':dict(sorted(local.items()))}
        glob.update(local)
    cue_count=sum(x['cue_count'] for x in per_video.values())
    require(len(route)==cue_count and len(route)==sum(glob.values()),'ROUTE_CONSERVATION')
    result={'schema':'V98_GENERIC_SOURCE_WIDE_ALL_CUE_PENDING_HYBRID_V1',
       'original_source_archive_sha256':expected_source_sha,
       'videos':len(per_video),'source_cues_routed':cue_count,
       'draft_parents_pending':len(parents),'original_windows':sum(x['windows'] for x in per_video.values()),
       'risk_events_prioritized':sum(x['alerts'] for x in per_video.values()),
       'priority_cues':sum(x['priority_cues'] for x in per_video.values()),
       'mandatory_fallback_cues':sum(x['fallback_cues'] for x in per_video.values()),
       'unassigned_cues_pending':len(unassigned),'zero_signal_windows':zero_windows,
       'route_counts':dict(sorted(glob.items())),'per_video':per_video,
       'cue_route_digest_sha256':digest(route),'parent_worklist_digest_sha256':digest(parents),
       'unassigned_worklist_digest_sha256':digest(unassigned),
       'source_first_all_cues_routed':True,'source_first_full_semantic_review_completed':False,
       'all_parents_atomized':False,'independent_gold':False,'certified_precision':None,
       'certified_recall':None,'new_knowledge_approved':0,
       'personalized_advice_approved':False,'p0_go':False}
    if include_private_queue:
        result['private_pending_cue_routes']=route
        result['private_pending_parent_rows']=parents
        result['private_pending_gap_rows']=unassigned
    return result

def check_full_source_public_receipt(receipt,actual):
    require(type(receipt) is dict and type(actual) is dict,'PUBLIC_RECEIPT_TYPES')
    for k in ('original_source_archive_sha256','videos','source_cues_routed','draft_parents_pending',
              'original_windows','risk_events_prioritized','priority_cues','mandatory_fallback_cues',
              'unassigned_cues_pending','zero_signal_windows','route_counts','per_video',
              'cue_route_digest_sha256','parent_worklist_digest_sha256','unassigned_worklist_digest_sha256'):
        require(receipt.get(k)==actual.get(k),'DRIFT_'+k)
    require(receipt.get('source_first_all_cues_routed') is True,'NOT_ROUTED')
    for k in ('source_first_full_semantic_review_completed','all_parents_atomized','independent_gold',
              'personalized_advice_approved','p0_go'):
        require(receipt.get(k) is False,'FALSE_GO_'+k)
    require(receipt.get('new_knowledge_approved')==0 and receipt.get('certified_precision') is None
            and receipt.get('certified_recall') is None,'FALSE_APPROVAL')
    require(not any(str(k).startswith('private_') for k in receipt),'PRIVATE_LEAK')
    return True