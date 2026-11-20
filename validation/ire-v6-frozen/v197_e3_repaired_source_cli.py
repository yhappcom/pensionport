"""Owner-only, read-only V197 source-repair E3 projection (NO E4/E5)."""
import argparse,hashlib,json,os,stat
from pathlib import Path
from ire.v6.errors import InvalidInput
from v195_e3_second_user_turn_audit import E3ActualSecondUserAudit,verify_full_private_response
from v196_e3_second_review_repair import E3SecondReviewRepairOverlay
from v197_e3_repaired_source_projection import (make_risk_register,build_review_view,
    seal_read_model,verify_seal,_canonical,_sha)

def _load_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))

def _private_write(path,obj):
    p=Path(path)
    if p.is_symlink() or p.exists():
        raise InvalidInput('V197_E3_PRIVATE_OUTPUT_ALREADY_EXISTS')
    p.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:
        f.write(_canonical(obj));f.flush();os.fsync(f.fileno())
    return _sha(obj)

def main(argv=None):
    x=argparse.ArgumentParser(description='Read-only actual CMA E3 overlay, unapproved risk-84 gate')
    for flag in ('v194-archive','v194-receipt','v195-review','v195-db',
                 'v195-receipt','v196-db','v196-receipt','risk-out','sealed-view-out'):
        x.add_argument('--'+flag,required=True)
    o=x.parse_args(argv)
    r194=_load_json(o.v194_receipt);r195=_load_json(o.v195_receipt);r196=_load_json(o.v196_receipt)
    resp=_load_json(o.v195_review)
    audit=E3ActualSecondUserAudit(frozen_archive=Path(o.v194_archive),external_receipt=r194,
         private_db=Path(o.v195_db),second_user_ref=resp['manual_second_user_ref'],
         second_user_message_sha256=resp['second_user_message_text_sha256'],create=False)
    if verify_full_private_response(resp,audit)['validated_reviews']!=120:
        raise InvalidInput('V197_E3_SECOND_CHAT_PRIVATE_RESPONSE_INVALID')
    if audit.status()['review_head_sha256']!=r195['v195_second_review_journal_head_sha256']:
        raise InvalidInput('V197_E3_OLD_SECOND_HEAD_MISMATCH')
    overlay=E3SecondReviewRepairOverlay(audit,Path(o.v196_db),
          expected_second_head=r195['v195_second_review_journal_head_sha256'],create=False)
    if overlay.status()['repair_overlay_head_sha256']!=r196['v196_overlay_head']:
        raise InvalidInput('V197_E3_OLD_CORRECTION_HEAD_MISMATCH')
    with audit._db() as db:_,judgments,_=audit._audit(db)
    risk=make_risk_register(audit,judgments)
    view=build_review_view(audit,overlay,expected_overlay_head=r196['v196_overlay_head'],risk_register=risk)
    _private_write(o.risk_out,risk)
    digest=seal_read_model(o.sealed_view_out,view)
    if digest!=verify_seal(o.sealed_view_out,view):
        raise InvalidInput('V197_E3_SEALED_VIEW_READBACK_MISMATCH')
    # Never print original owner data or claim text to public logs.
    print(json.dumps({'source_sha256':view['source_sha256'],
         'review_head_sha256':view['frozen_second_head_sha256'],
         'repair_head_sha256':view['frozen_v196_repair_head_sha256'],
         'high_risk_blocked':view['all_original_high_risk_blocked'],
         'quarantined_kept':view['original_quarantines_enforced'],
         'corrected_source_reading_proposals':view['source_rewrite_proposals'],
         'risk_register_sha256':_sha(risk),'sealed_view_sha256':digest,
         'e3_approved':False,'e4_approved':False,'e5_published':False},
         ensure_ascii=False,sort_keys=True))

if __name__=='__main__':main()