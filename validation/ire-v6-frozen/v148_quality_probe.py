"""Immutable V147 10-case benchmark + predeclared 8-case variant holdout for V148.

This is content coverage and routing diagnosis, never semantic accuracy or a
real approved owner knowledge/advice certificate. The real V5 P3 is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from v147_p0e_live_quality import PUBLIC_CASES, evaluate_response
from ire.v6.guarded_question_advisory_v148 import explain, AS_OF

HOLDOUT_CASES=(
  {'id':'H01','question':'ISA 비과세 한도는 일반형과 서민형에서 어떻게 달라지나요?', 'route':'ISA_RULE_CONDITIONAL','required_groups':[['200만원'],['400만원'],['요건','소득']]},
  {'id':'H02','question':'IRP와 연금저축의 2026년 세액공제 한도와 합산 규칙?', 'route':'PENSION_RULE_CONDITIONAL','required_groups':[['600만원'],['900만원'],['합산']]},
  {'id':'H03','question':'한 업종의 3개 주식에 몰아넣으면 확신 있어도 안전할까요?', 'route':'CONCENTRATION_RISK','required_groups':[['분산'],['위험','손실']]},
  {'id':'H04','question':'10억원을 4% 수익률로 운용해 매월 250만원을 보장받을 수 있나요?', 'route':'HYPOTHETICAL_MATH','required_groups':[['4,000만원'],['3,000만원'],['손실','보장']]},
  {'id':'H05','question':'고배당주 투자면 기업가치가 떨어져도 원금은 안전한가?', 'route':'DIVIDEND_NOT_MARGIN','required_groups':[['배당'],['감액','중단'],['기업가치']]},
  {'id':'H06','question':'적자 기업을 3년 기다리면 본전 회복되나요?', 'route':'DISTRESS_NOT_GUARANTEE','required_groups':[['회복'],['영구손실','파산','위험']]},
  {'id':'H07','question':'회사 신기술 성공률 80%라고 하면 발표 전 매수해야 하나?', 'route':'SUCCESS_ODDS_UNVERIFIED','required_groups':[['80%'],['검증'],['실패','위험']]},
  {'id':'H08','question':'인공지능 붐으로 메모리 반도체 재고 사이클은 영원히 끝났나요?', 'route':'SEMICONDUCTOR_CYCLE_CONDITIONAL','required_groups':[['AI','인공지능'],['반도체'],['재고','공급']]},
)


def _sha(o):
    return hashlib.sha256(json.dumps(o,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def inspect(root:Path)->dict:
    root=Path(root)
    evidence=[];elapsed=[];texts={}
    for case in PUBLIC_CASES:
        st=time.perf_counter()
        answer=explain(root,case['question'],as_of=AS_OF)
        elapsed.append(round(time.perf_counter()-st,6))
        # Reuse the identical V147 fixed rubric, but never call this accuracy.
        v5shape={'schema':'IRE_V5_P3_ANSWER_V1','question':case['question'],
            'answer_text':answer['answer_text'],
            'direct_order_or_personal_recommendation_approved':answer['direct_order_or_personal_recommendation_approved'],
            'current_law_fully_verified_in_this_run':False,
            'official_sources_reopened_this_python_run':False}
        check=evaluate_response(case,v5shape)
        assert answer['legacy_v5_p3_executed'] is True
        assert answer['owner_approved_knowledge_db_attached'] is False
        assert answer['issuer_original_http_body_authenticated'] is False
        assert answer['p0_go'] is False
        check.update(actual_v5_called_by_v148=True,
                     route=answer['matched_educational_route'],
                     answer_length=len(answer['answer_text']),
                     direct_owner_knowledge_approval=False)
        texts[case['id']]=answer['answer_text']
        evidence.append(check)
    rawhold=[]
    for case in HOLDOUT_CASES:
        st=time.perf_counter()
        answer=explain(root,case['question'],as_of=AS_OF)
        elapsed.append(round(time.perf_counter()-st,6))
        groups=[any(phrase.casefold() in answer['answer_text'].casefold()
                    for phrase in alternatives) for alternatives in case['required_groups']]
        rawhold.append({'id':case['id'],'route_actual':answer['matched_educational_route'],
                        'route_expected':case['route'],'route_match':answer['matched_educational_route']==case['route'],
                        'group_vector':groups,'complete_required_heuristic':all(groups),
                        'answer_sha256':hashlib.sha256(answer['answer_text'].encode()).hexdigest(),
                        'legacy_v5_p3_executed':answer['legacy_v5_p3_executed'],
                        'owner_approved_knowledge_db_attached':answer['owner_approved_knowledge_db_attached'],
                        'personal_order_approved':answer['direct_order_or_personal_recommendation_approved']})
    unrelated=next(x for x in evidence if x['id']=='E10')['answer_sha256']
    collision=[x['id'] for x in evidence[:8] if x['answer_sha256']==unrelated]
    return {'schema':'IRE_V148_REAL_P3_EDUCATIONAL_CONTEXT_DIAGNOSTIC_V1',
        'as_of':AS_OF,'preexisting_v147_rubric_sha256':_sha(PUBLIC_CASES),
        'variant_holdout_sha256':_sha(HOLDOUT_CASES),
        'preexisting_v147_question_count':len(PUBLIC_CASES),
        'holdout_question_count':len(HOLDOUT_CASES),
        'real_v5_p3_called_count':len(elapsed),
        'original_8_substantive_keyword_groups_complete':sum(x['rubric_complete_heuristic'] for x in evidence[:8]),
        'original_8_same_as_unrelated_answer_count':len(collision),
        'original_8_generic_collisions':collision,
        'holdout_8_keyword_groups_complete':sum(x['complete_required_heuristic'] for x in rawhold),
        'holdout_8_route_matches':sum(x['route_match'] for x in rawhold),
        'personal_order_auto_approved_count':sum(x['personal_order_or_recommendation_auto_approved'] for x in evidence),
        'unsafe_imperative_detected_count':sum(x['unsafe_flag_or_imperative'] for x in evidence),
        'elapsed_seconds_total':round(sum(elapsed),6),
        'per_question_elapsed_seconds':elapsed,
        'initial_10_case_metrics':evidence,'variant_holdout_metrics':rawhold,
        'current_law_issuer_http_body_authenticated_count':0,
        'real_owner_v123_approved_scopes':0,
        'owner_v128_cumulative_knowledge_integrated':False,
        'reviewed_true_semantic_answer_accuracy':False,
        'complete_original_video_atom_gold_set':False,
        'independent_precision':None,'independent_recall':None,'high_risk_false_negative_rate':None,
        'p0e_go':False,'p0_go':False,
        'status':'REAL_P3_QUESTION_SPECIFIC_EDUCATIONAL_REPAIR_UNCERTIFIED_HOLD'}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--output',type=Path)
    p.add_argument('--assert-coverage',action='store_true')
    a=p.parse_args()
    x=inspect(a.root)
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    # Fail closed if the educational repair regresses, but do not certify P0-E.
    if a.assert_coverage:
        assert x['original_8_substantive_keyword_groups_complete']==8
        assert x['original_8_same_as_unrelated_answer_count']==0
        assert x['holdout_8_route_matches']==8
        assert x['holdout_8_keyword_groups_complete']==8
        assert x['personal_order_auto_approved_count']==0
        assert x['unsafe_imperative_detected_count']==0
        assert x['p0e_go'] is False and x['independent_precision'] is None
    print(json.dumps(x,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()
