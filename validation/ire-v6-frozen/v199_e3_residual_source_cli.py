"""Read-only restart and source-pinned V199 E3 HOLD verification.

Input is a user-private checkpoint directory. Never prints owner SRT, individual
verdict text, or any private personal investment data. No model/API invocation.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from v195_e3_second_user_turn_audit import E3ActualSecondUserAudit, verify_full_private_response
from v196_e3_second_review_repair import E3SecondReviewRepairOverlay,_sha
from v197_e3_repaired_source_projection import make_risk_register
from v198_e3_final_correction_adjudication import E3CorrectionAdjudication
from v199_e3_residual_source_verdict import (E3SixResidualVerdicts,
    build_84_contextual_risk_view, validate_web_text_spot_checks)


def verify(private_dir:Path,expected_v199_head:str):
    p=Path(private_dir)
    def j(name):return json.loads((p/name).read_text(encoding='utf-8'))
    v194=j('V194_E3_FIRST_ACTUAL_USER_RESEARCH_TURN_SHA_ONLY_RECEIPT.json')
    v195=j('V195_ACTUAL_TURN2_E3_SHA_ONLY_RECEIPT.json')
    v196=j('V196_CMA_E3_LAST_TURN_REPAIRS_SHA_ONLY_RECEIPT.json')
    v198=j('V198_CMA_E3_16_VERDICTS_84_RISKS_SHA_ONLY_RECEIPT.json')
    resp=j('v195_CHATGPT_FINAL_E3_TURN2_PRIVATE.json')
    review=E3ActualSecondUserAudit(
      frozen_archive=p/'v194_FROZEN_RESEARCH_TURN1_PRIVATE.zip',
      external_receipt=v194,private_db=p/'v195_E3_SECOND_USER_APPEND_ONLY.sqlite',
      second_user_ref=resp['manual_second_user_ref'],
      second_user_message_sha256=resp['second_user_message_text_sha256'])
    assert verify_full_private_response(resp,review)['validated_reviews']==120
    assert review.status()['review_head_sha256']==v195['v195_second_review_journal_head_sha256']
    repair=E3SecondReviewRepairOverlay(review,p/'V196_E3_REPAIR_APPEND_ONLY.sqlite',
              expected_second_head=v195['v195_second_review_journal_head_sha256'])
    assert repair.status()['repair_overlay_head_sha256']==v196['v196_overlay_head']
    with review._db() as con:_,old,_=review._audit(con)
    risk=make_risk_register(review,old)
    v198_obj=E3CorrectionAdjudication(review,repair,
        p/'V198_E3_FINAL_CORRECTION_ADJUDICATION.sqlite',
        expected_repair_head=v196['v196_overlay_head'],risk_register=risk)
    assert v198_obj.status()['adjudication_head_sha256']==v198['v198_head']
    z=E3SixResidualVerdicts(v198_obj,p/'V199_E3_SIX_RESIDUALS_APPEND_ONLY.sqlite',
           expected_v198_head=v198['v198_head'])
    st=z.status();assert st['v199_head_sha256']==expected_v199_head and st['reviewed']==6
    all_risk=build_84_contextual_risk_view(z)
    spot=j('V199_PRIVATE_12_PUBLIC_WEB_TEXT_RISK_COMPARISONS.json')
    validation=validate_web_text_spot_checks(z,spot)
    assert all_risk==j('V199_PRIVATE_84_RISK_WEB_CONTEXT_VIEW.json')
    assert _sha(spot)==j('V199_PRIVATE_HOLD_STATUS.json')['spot_check_sha256']
    assert _sha(all_risk)==j('V199_PRIVATE_HOLD_STATUS.json')['risk_84_web_context_sha256']
    assert st==j('V199_PRIVATE_HOLD_STATUS.json')['status']
    return {'schema':'IRE_V199_E3_SEPARATE_PROCESS_PRIVATE_HOLD_REPLAY_V1',
         'source_sha256':st['source_sha256'],
         'first_turn_unmodified_head_sha256':v194['owner_head_sha256'],
         'v199_head_sha256':st['v199_head_sha256'],
         'residual_source_verdicts':st['reviewed'],
         'web_text_financial_risk_spot_checks':validation['sample_size'],
         'high_risk_all_blocked':all_risk['risk_count'],
         'quarantines_preserved':all_risk['quarantines'],
         'issuer_raw_source_authenticated':False,
         'independent_gold_approved':False,
         'e3_approved':False,'e4_approved':False,'e5_published':False}


def main(argv=None):
    arg=argparse.ArgumentParser(description='Verify owner-private V199 E3 HOLD checkpoint only')
    arg.add_argument('--private-dir',type=Path,required=True)
    arg.add_argument('--expected-v199-head',required=True)
    opts=arg.parse_args(argv)
    print(json.dumps(verify(opts.private_dir,opts.expected_v199_head),ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()