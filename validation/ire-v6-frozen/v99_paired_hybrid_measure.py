"""V99 same-source V91/V96/V98 pilot; CPU structural and routing coverage only.

No fabricated independent accuracy, no token/human latency, no completed
semantic review, no claimed cost saving or full-source recall.
"""
from __future__ import annotations
from collections import Counter
from v98_hybrid_source_guard import require,sha,digest

EXPECTED_ISSUES=20

def paired_compare(source_rows,alerts,internal_issues,hybrid):
    require(type(internal_issues) is list and len(internal_issues)==EXPECTED_ISSUES,'ISSUE_COUNT')
    require(hybrid.get('source_cue_count')==200 and hybrid.get('priority_cues')==145
            and hybrid.get('baseline_fallback_cues')==55,'HYBRID_SCOPE')
    require(len(source_rows)==200 and len(alerts)==21,'SOURCE_INPUT')
    by_cue={}
    for s in source_rows:
        key=(s['video_id'],s['window_id'],s['cue_index'])
        require(key not in by_cue and s['source_sha256']==sha(s['source_text_private']),'SOURCE_SHA')
        by_cue[key]=s
    require(len(by_cue)==200,'SOURCE_CENSUS')
    alerted=set()
    for f in alerts:
        key=(f['video_id'],f['window_id'],f['cue_index'])
        require(key in by_cue and f['cue_sha256']==by_cue[key]['source_sha256'],'FLAG_SOURCE')
        alerted.add(key)
    require(len(alerted)==21,'FLAGGED_CUES')
    route_map={}
    for r in hybrid['private_cue_routes']:
        k=(r['video_id'],r['window_id'],r['cue_index'])
        require(k in by_cue and k not in route_map,'ROUTE_CUE_DUP_OR_EXTRA')
        require(r['cue_sha256']==by_cue[k]['source_sha256'],'ROUTE_SHA')
        require(r['review_completed'] is False and r['independent_gold'] is False
                and r['fact_approved'] is False,'FALSE_REVIEW_OR_APPROVAL')
        route_map[k]=r
    require(set(route_map)==set(by_cue),'MISSING_CUE_ROUTE')
    issue_rows=[];alerted_issues=0;hybrid_routed=0;previously_unalerted=[];seen=set()
    for i in internal_issues:
        require(type(i) is dict and i.get('independent_gold') is False
                and i.get('actual_error_certified') is False,'FAKE_ISSUE_GOLD')
        v,w,a,b=i.get('video_id'),i.get('window_id'),i.get('first_cue'),i.get('last_cue')
        require(type(a) is int and type(b) is int and a<=b,'ISSUE_RANGE')
        key=(v,w,a,b);require(key not in seen,'DUP_ISSUE');seen.add(key)
        span=[(v,w,j) for j in range(a,b+1)]
        require(all(k in by_cue for k in span),'ISSUE_SOURCE_GAP')
        require(i.get('source_span_sha256')==sha(''.join(by_cue[k]['source_sha256'] for k in span)),'ISSUE_DIGEST')
        alerted_any=any(k in alerted for k in span)
        routed_all=all(k in route_map for k in span)
        require(routed_all,'ISSUE_UNROUTED')
        if alerted_any:alerted_issues+=1
        else:previously_unalerted.append([v,w,a,b,i['source_span_sha256']])
        if routed_all:hybrid_routed+=1
        issue_rows.append([v,w,a,b,alerted_any,routed_all,i['source_span_sha256']])
    require(alerted_issues==12 and hybrid_routed==20 and len(previously_unalerted)==8,'PAIRED_LOCK')
    return {'schema':'V99_SOURCE_PAIRED_INTERNAL_ISSUE_COVERAGE_NOT_GOLD_V1',
       'scope_cues':200,'v91_provisional_parents':77,'v91_unassigned_cues':7,
       'v96_unique_alerted_cues':21,'v96_envelope_cues':145,
       'v96_unrouted_by_alert_envelope':55,
       'v98_priority_cues':145,'v98_obligatory_baseline_fallback':55,
       'v98_routed_cues':200,'v98_unassigned_cues_pending':7,
       'internally_annotated_issue_spans_not_gold':20,
       'v96_issue_spans_with_direct_alert':12,
       'v96_issue_spans_without_direct_alert':8,
       'v98_issue_spans_routed_to_review':20,
       'v98_previously_unalerted_issue_spans_routed':8,
       'risk_signal_alert_improvement_not_proven':True,
       'semantic_decision_time_seconds':None,
       'human_review_time_seconds':None,
       'financial_precision':None,'financial_recall':None,'certified_latency_reduction':None,
       'independent_gold':False,'full_semantic_recall_certified':False,
       'all_200_cues_semantically_reviewed':False,'p0_go':False,
       'paired_issue_receipt_sha256':digest(issue_rows),
       'previously_unalerted_issue_receipt_sha256':digest(previously_unalerted)}

def validate_structural_benchmark(row):
    require(type(row) is dict,'BENCHMARK_TYPE')
    require(row.get('repetitions')==500 and row.get('alternated_order') is True,'BENCHMARK_SETUP')
    for kind in ('v91_parent_census','v96_risk_screen','v98_hybrid_route'):
        d=row.get(kind);require(type(d) is dict,'BENCHMARK_MISSING_'+kind)
        for k in ('median_ms','p95_ms'):
            require(type(d.get(k)) in (int,float) and d[k]>=0,'BENCHMARK_VALUE_'+kind)
        require(d['p95_ms']>=d['median_ms'],'BENCHMARK_ORDER')
    for name in ('model_semantic_time_s','human_review_time_s','certified_workflow_speedup',
                 'precision','recall','high_risk_recall'):
        require(row.get(name) is None,'FALSE_PERFORMANCE_'+name)
    require(row.get('p0_go') is False and row.get('independent_gold') is False,'FALSE_GO')
    return True