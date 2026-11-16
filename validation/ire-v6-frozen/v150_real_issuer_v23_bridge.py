"""V150 actual V5→V23 synthetic-clause integration with *live* official HTTP bodies.

Owner video claims are NOT approved; this checker can never publish user-owner
advice. It exercises the old P3 function plus current-law and source-body
replay in one invocation. Raw bytes are collected fresh, not invented hashes.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from datetime import date
from pathlib import Path
from ire.v6.codec import sha256
from ire.v6.tests.test_stage_repair import fixture,atom,exchange
from ire.v6.current_advisory_bridge import answer_with_current_law
from v149_official_https_body import SPECS,try_live_fetch,_visible,audit_original_bytes

Q='2026년 ISA 모든 가입자가 500만원 비과세이고 연금저축 900만원 및 IRP 추가 900만원이 각각 세액공제 되나요?'
ASOF='2026-11-16'


def evidence_from_exact_live_bytes(raw_dir:Path, receipts:list,*,as_of=ASOF):
    index={x['rule_id']:x for x in receipts}
    if set(index)!=set(SPECS):raise ValueError('OFFICIAL_SOURCE_CENSUS')
    laws=[]
    for rule,spec in SPECS.items():
        old=index[rule]
        if old.get('status')!='HTTPS_TRANSPORT_RAW_BODY_CAPTURED_SCOPE_REVIEW_STILL_REQUIRED' or old.get('tls_session_executed_by_this_function') is not True:
            raise ValueError('OFFICIAL_LIVE_ORIGIN_NOT_VERIFIED')
        raw=(Path(raw_dir)/(rule+'.original_http_body.bin')).read_bytes()
        replay=audit_original_bytes(rule,raw,requested_url=spec['url'],final_url=old['final_https_url'],captured_on=as_of,as_of=as_of)
        if replay['body_sha256']!=old['body_sha256'] or len(raw)!=old['byte_count']:
            raise ValueError('OFFICIAL_HTTP_BYTES_DRIFT')
        visible=_visible(raw)
        anchor=visible.find(spec['article'])
        if anchor<0:raise ValueError('OFFICIAL_ARTICLE_MISSING')
        excerpt=visible[max(0,anchor-10):min(len(visible),anchor+300)]
        if len(excerpt)<20 or excerpt not in visible:
            raise ValueError('OFFICIAL_VERBATIM_EXCERPT_MISSING')
        laws.append({'rule_id':rule,'source_url':spec['url'],'effective_from':spec['effective'],
             'effective_to':None,'retrieved_on':as_of,'excerpt':excerpt,
             'excerpt_sha256':sha256(excerpt.encode()),'document_body_sha256':replay['body_sha256'],
             'scope_note':'해당 조문의 일반 비과세·공제 한도 확인에 한정하며 가입자 소득과 계좌별 실제 적용은 별도 검증한다.'})
    return laws


def synthetic_current_question():
    s=fixture([
        'ISA에 가입한 사람은 누구나 수익 500만원을 비과세받을 수 있다.',
        '연금저축 900만원과 IRP 900만원은 각각 독립적으로 세액공제받는다.'
    ])
    ex=exchange(s,[
        atom(s,'C00001',[1],[1],'ISA 소득 비과세 한도가 모든 가입자에게 예외 없이 500만원이라고 단정한다.',stance='AFFIRMED'),
        atom(s,'C00002',[2],[2],'연금저축 900만원과 IRP 900만원이 각각 별도 세액공제 한도라고 단정한다.',stance='AFFIRMED')
    ])
    decisions=[]
    for cid,rule,reason,missing in [
       ('C00001','ISA_91_18','현행 조세특례제한법의 일반 한도 200만원과 법정 우대자격에 따른 400만원은 모두에게 적용되는 500만원 비과세 단정과 충돌한다.', ['가입자 소득 및 우대자격','실제 계좌 유형과 소득 발생시점']),
       ('C00002','PENSION_59_3','현행 소득세법의 연금저축 세액공제 납입 600만원, 퇴직연금 합산 900만원 한도는 각 계좌마다 900만원씩 공제된다는 단정과 충돌한다.', ['거주자·소득세액','기존 연금저축 및 퇴직연금 납입 합계'])
    ]:
        a=next(z for z in ex['atoms'] if z['claim_id']==cid)
        decisions.append({'claim_id':cid,'proposition_sha256':sha256(a['proposition'].encode()),
            'classification':'CURRENT_RULE_CONTRADICTS_SOURCE','rule_ids':[rule],
            'reason':reason,'missing_conditions':sorted(missing),
            'reviewer':'CHATGPT_CURRENT_TURN','reviewed_as_of':ASOF})
    return s,ex,decisions


def run(root,*,raw_dir,as_of=ASOF,force_block=False):
    if as_of!=ASOF:raise ValueError('V150_CANNOT_REUSE_CHAT_JUDGMENT_ON_ANOTHER_DAY')
    receipts=[try_live_fetch(k,as_of=as_of,raw_store=raw_dir) for k in SPECS]
    initial={'schema':'V150_REAL_OFFICIAL_TO_V23_PIPELINE_V1','as_of':as_of,
       'capture_statuses':{r['rule_id']:r['status'] for r in receipts},
       'real_official_http_body_count':sum(r.get('original_http_bytes_locally_rehashed') is True for r in receipts),
       'official_raw_sha256':{r['rule_id']:r.get('body_sha256') for r in receipts},
       'actual_V5_called':False,'actual_V23_run':False,
       'actual_owner_approved_knowledge_attached':False,'actual_owner_video_approved_scopes':0,
       'full_video_precision_recall_measured':False,'individual_tax_eligibility_verified':False,
       'issuer_digitally_signed_body_verified':False,'p0_e_go':False,'p0_go':False}
    if force_block or not all(r.get('original_http_bytes_locally_rehashed') is True for r in receipts):
        initial['status']='HOLD_OFFICIAL_HTTP_BODY_MISSING_NO_SYNTHETIC_FALLBACK'
        return initial
    evidence=evidence_from_exact_live_bytes(raw_dir,receipts,as_of=as_of)
    s,ex,decisions=synthetic_current_question()
    out=answer_with_current_law(Path(root),Q,source=s,exchange=ex,current_as_of=as_of,
                primary_evidence=evidence,chat_decisions=decisions,selected_claim_ids=['C00001','C00002'])
    if (out['schema']!='IRE_V6_V5_P3_CURRENT_LAW_ANSWER_BRIDGE_V23' or
       out['v5_p3_executed'] is not True or out['reviewed_current_rule_claim_count']!=2 or
       out['official_context_urls']!=sorted(sx['url'] for sx in SPECS.values()) or
       out['personal_account_eligibility_or_tax_approved'] is not False or
       out['direct_order_or_personal_recommendation_approved'] is not False or
       out['v5_p3_legacy_text_rendered_as_current_law'] is not False or
       out['p0_go'] is not False):raise ValueError('V23_UNSAFE_CURRENT_LAW_RESULT')
    initial.update(actual_V5_called=True,actual_V23_run=True,real_official_http_body_count=2,
       V23_reviewed_rule_claims=out['reviewed_current_rule_claim_count'],
       V23_primary_rule_urls=out['official_context_urls'],
       synthetic_source_fact_check_only=True,
       original_response_sha256=hashlib.sha256(out['answer_text'].encode()).hexdigest(),
       current_rule_status='HTTPS_RAW_VERIFIED_BUT_LEGAL_SCOPE_CHAT_ONLY',
       status='V5_V23_LIVE_TWO_RULE_SYNTHETIC_SOURCE_PASSED_OWNER_NOT_APPROVED')
    return initial

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--raw-dir',type=Path,default=Path('/tmp/v150_official_http_body'))
    p.add_argument('--output',type=Path,default=Path('/tmp/v150_v23_live_receipt.json'))
    p.add_argument('--force-block',action='store_true');a=p.parse_args()
    try:res=run(a.root,raw_dir=a.raw_dir,force_block=a.force_block)
    except Exception as e:
        res={'schema':'V150_REAL_OFFICIAL_TO_V23_PIPELINE_V1','status':'V23_LIVE_INTEGRATION_EXCEPTION_HOLD',
             'error_type':type(e).__name__,'error_message_sha256':hashlib.sha256(str(e).encode()).hexdigest(),
             'actual_owner_approved_knowledge_attached':False,'p0_e_go':False,'p0_go':False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(res,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps(res,ensure_ascii=False,sort_keys=True))
    if res['status']=='V23_LIVE_INTEGRATION_EXCEPTION_HOLD':sys.exit(1)
