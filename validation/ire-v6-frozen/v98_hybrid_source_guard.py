"""V98 fail-closed cue-first hybrid routing; source-verified PENDING != reviewed.

Public source contains no private SRT or personalized advice. A risk classifier
may prioritize original cues but may NEVER remove the complement or unassigned
cues. Independent blind gold, financial law approval and P0 GO stay false.
"""
from __future__ import annotations
import hashlib,json,re
from collections import Counter

SCOPE=(('6VEfKF7BzZU','W00026',13,5),
       ('qtluAViPpsQ','W00018',19,4),
       ('4CQ4FjGT2gA','W00117',12,9),
       ('4CQ4FjGT2gA','W00053',17,3),
       ('4CQ4FjGT2gA','W00096',16,0))
SOURCE_SHA='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
V97_BASE='c57f0611d809e6c9cc9d2446835184b73d3f6bde'
ALERT_KINDS={'ASR_REVIEW','QUALIFIER_REVIEW','COMPOUND_REVIEW','MULTINUMERIC_REVIEW',
             'UNCAPTURED_FINANCE_CUE','UNCAPTURED_NUMERIC_CUE','OVERLAPPING_CANDIDATE_REVIEW'}
ROUTE_KINDS={'PRIORITY_PARENT_PENDING','BASELINE_PARENT_PENDING',
             'PRIORITY_UNASSIGNED_PENDING','BASELINE_UNASSIGNED_PENDING'}

def require(ok,why):
    if not ok:raise ValueError('V98_'+why)
def sha(x):return hashlib.sha256(x.encode('utf-8') if isinstance(x,str) else x).hexdigest()
def digest(x):return sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))

def hybrid_route(source_rows,parents,alerts,*,archive_sha=SOURCE_SHA,radius=7):
    require(archive_sha==SOURCE_SHA,'ARCHIVE_PIN')
    require(type(radius) is int and radius==7,'PINNED_RADIUS')
    require(type(source_rows) is list and len(source_rows)==200,'SOURCE200')
    require(type(parents) is list and len(parents)==77,'PARENTS77')
    require(type(alerts) is list and len(alerts)==21,'ALERTS21')
    expected={(v,w):(np,nf) for v,w,np,nf in SCOPE}
    rows={};by_window=Counter()
    for c in source_rows:
        require(type(c) is dict,'CUE_TYPE')
        v,w,i=c.get('video_id'),c.get('window_id'),c.get('cue_index')
        require((v,w) in expected and type(i) is int,'CUE_SCOPE')
        first=(int(w[1:])-1)*40+1
        require(first<=i<first+40,'CUE_BOUNDS')
        key=(v,w,i);require(key not in rows,'DUP_CUE')
        t=c.get('source_text_private')
        require(type(t) is str and bool(t),'CUE_TEXT')
        require(c.get('source_sha256')==sha(t),'SOURCE_CUE_SHA')
        require(type(c.get('start_ms')) is int and type(c.get('end_ms')) is int
                and c['start_ms']>=0 and c['end_ms']>=c['start_ms'],'SOURCE_TIME')
        require(type(c.get('parent_ids')) is list and len(c['parent_ids'])==len(set(c['parent_ids'])),'CUE_PARENT_IDS')
        rows[key]=c;by_window[(v,w)]+=1
    require(set(by_window)==set(expected) and all(by_window[x]==40 for x in expected),'NO_40_CENSUS')
    grouped={};claimed={};pcount=Counter()
    for p in parents:
        require(type(p) is dict,'PARENT_TYPE')
        v,w,cid=p.get('video_id'),p.get('window_id'),p.get('claim_id')
        require((v,w) in expected and type(cid) is str and bool(cid),'PARENT_SCOPE')
        pkey=(v,w,cid);require(pkey not in grouped,'DUP_PARENT')
        indices=p.get('cue_indices')
        require(type(indices) is list and indices and len(set(indices))==len(indices),'PARENT_CUES')
        for i in indices:
            k=(v,w,i);require(k in rows,'PARENT_OUTSIDE_WINDOW')
            require(k not in claimed,'OVERLAP_PARENT')
            claimed[k]=cid
        expected_text=' | '.join(rows[(v,w,i)]['source_text_private'] for i in indices)
        require(p.get('source_text_sha256')==sha(expected_text),'PARENT_TEXT_SHA')
        grouped[pkey]=p;pcount[(v,w)]+=1
    require(all(pcount[(v,w)]==np for v,w,np,nf in SCOPE),'PARENT_CENSUS')
    for key,c in rows.items():
        assigned=[] if key not in claimed else [claimed[key]]
        require(c['parent_ids']==assigned,'CUE_PARENT_DIVERGENCE')
    alert_keys=set();alert_cues=set();flagcount=Counter()
    for a in alerts:
        v,w,i=a.get('video_id'),a.get('window_id'),a.get('cue_index')
        kind=a.get('kind')
        require((v,w) in expected and (v,w,i) in rows and kind in ALERT_KINDS,'ALERT_SCOPE')
        require(a.get('cue_sha256')==rows[(v,w,i)]['source_sha256'],'ALERT_SOURCE_SHA')
        k=(v,w,i,kind);require(k not in alert_keys,'DUP_ALERT')
        alert_keys.add(k);alert_cues.add((v,w,i));flagcount[(v,w)]+=1
    require(all(flagcount[(v,w)]==nf for v,w,np,nf in SCOPE),'FLAG_CENSUS')
    priority=set()
    for v,w,i in alert_cues:
        first=(int(w[1:])-1)*40+1
        for j in range(max(first,i-radius),min(first+39,i+radius)+1):priority.add((v,w,j))
    routed=[];counts=Counter();gaps=[]
    for v,w,np,nf in SCOPE:
        first=(int(w[1:])-1)*40+1
        for i in range(first,first+40):
            key=(v,w,i);row=rows[key]
            p=(key in priority);unassigned=(key not in claimed)
            kind=('PRIORITY_' if p else 'BASELINE_')+('UNASSIGNED_PENDING' if unassigned else 'PARENT_PENDING')
            counts[kind]+=1
            if unassigned:gaps.append([v,w,i,row['source_sha256']])
            routed.append({'video_id':v,'window_id':w,'cue_index':i,
                          'cue_sha256':row['source_sha256'],'parent_id':claimed.get(key),
                          'route':kind,'review_completed':False,
                          'independent_gold':False,'fact_approved':False,
                          'personalized_advice_approved':False})
    require(len(routed)==200 and len({(x['video_id'],x['cue_index']) for x in routed})==200,'ROUTE_CENSUS')
    require(len(priority)==145 and sum(v for k,v in counts.items() if k.startswith('BASELINE_'))==55,'PRIORITY_CENSUS')
    require(len(gaps)==7,'UNASSIGNED7')
    parent_routes=[]
    for v,w,cid in sorted(grouped):
        p=grouped[(v,w,cid)];parent_priority=any((v,w,i) in priority for i in p['cue_indices'])
        parent_routes.append({'video_id':v,'window_id':w,'parent_id':cid,
          'parent_source_sha256':p['source_text_sha256'],'priority':parent_priority,
          'draft_parent_review_completed':False,'atomic_completeness_certified':False,
          'fact_approved':False})
    require(len(parent_routes)==77,'PARENT_QUEUE77')
    return {'schema':'V98_ORIGINAL_CUE_HYBRID_PENDING_ROUTE_V1',
        'source_archive_sha256':SOURCE_SHA,'v97_baseline':V97_BASE,
        'source_cue_count':len(rows),'draft_parent_count':len(parent_routes),
        'alert_events':len(alert_keys),'flagged_cues':len(alert_cues),
        'priority_cues':len(priority),'baseline_fallback_cues':len(rows)-len(priority),
        'unassigned_cues':len(gaps),'zero_alert_window_fallback_cues':40,
        'route_counts':dict(sorted(counts.items())),
        'cue_routing_sha256':digest(routed),
        'parent_worklist_sha256':digest(parent_routes),
        'unassigned_cue_worklist_sha256':digest(gaps),
        'review_completed_cues':0,'all_original_cues_routed':True,
        'all_original_cues_semantically_reviewed':False,
        'full_atomic_recall_certified':False,'independent_gold':False,
        'financial_fact_approved':False,'personalized_advice_approved':False,'p0_go':False,
        'private_cue_routes':routed,'private_parent_worklist':parent_routes,
        'private_unassigned_worklist':gaps}

def verify_hybrid_receipt(receipt,actual):
    require(type(receipt) is dict and type(actual) is dict,'RECEIPT_TYPES')
    fields=('source_archive_sha256','v97_baseline','source_cue_count','draft_parent_count',
            'alert_events','flagged_cues','priority_cues','baseline_fallback_cues',
            'unassigned_cues','zero_alert_window_fallback_cues','route_counts',
            'cue_routing_sha256','parent_worklist_sha256','unassigned_cue_worklist_sha256')
    for f in fields:require(receipt.get(f)==actual.get(f),'DRIFT_'+f)
    for f in ('all_original_cues_semantically_reviewed','full_atomic_recall_certified',
              'independent_gold','financial_fact_approved','personalized_advice_approved','p0_go'):
        require(receipt.get(f) is False,'FALSE_GO_'+f)
    require(receipt.get('all_original_cues_routed') is True,'NOT_ALL_ROUTED')
    require(receipt.get('review_completed_cues')==0,'FALSE_REVIEW_COMPLETED')
    require(not any(k.startswith('private_') for k in receipt),'PRIVATE_LEAK')
    return True