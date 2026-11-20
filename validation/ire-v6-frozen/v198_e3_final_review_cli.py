"""V198 read-only private recovery and adjudication status; no model API or E4."""
import argparse,hashlib,io,json,os,sqlite3,tempfile,zipfile
from pathlib import Path
from v195_e3_second_user_turn_audit import E3ActualSecondUserAudit
from v196_e3_second_review_repair import E3SecondReviewRepairOverlay
from v197_e3_repaired_source_projection import make_risk_register
from v198_e3_final_correction_adjudication import (E3CorrectionAdjudication,
       build_effective_unapproved_view,build_84_evidence_triage,_sha)

def _sha256(b):return hashlib.sha256(b).hexdigest()

def _extract_safe(z,path,expected_manifest):
    manifest=json.loads(z.read(path))
    assert _sha256(z.read(path))==expected_manifest,'CHECKPOINT_MANIFEST_SHA_INVALID'
    for m in manifest['files']:
        n=m['path']
        assert '/' not in n and '..' not in n and n in z.namelist(),'PRIVATE_ARCHIVE_PATH_INVALID'
        assert _sha256(z.read(n))==m['sha256'] and len(z.read(n))==m['bytes'],'PRIVATE_MEMBER_TAMPER'
    return manifest

def replay(*,v197_zip,v197_sha,v198_db,v198_head):
    archive=Path(v197_zip)
    assert _sha256(archive.read_bytes())==v197_sha,'V197_EXTERNAL_ARCHIVE_SHA_MISMATCH'
    with tempfile.TemporaryDirectory(prefix='v198_readonly_') as temp:
        d=Path(temp)
        with zipfile.ZipFile(archive) as z:
            m=_extract_safe(z,'V197_checkpoint_manifest.json',
                              '5858b0b297e1d408a5b34cfa74a2398ea63d96719ca3f2532abc5bbbf7efc433')
            for n in ('V194_SHA_ONLY_RECEIPT.json','V195_SHA_ONLY_RECEIPT.json',
                       'V196_SHA_ONLY_RECEIPT.json'):
                (d/n).write_bytes(z.read(n))
            v196_blob=z.read('V196_PRIVATE_CMA_PREVIOUS_FROZEN.zip')
        with zipfile.ZipFile(io.BytesIO(v196_blob)) as z:
            v196_m=json.loads(z.read('V196_manifest.json'))
            for f in v196_m['files']:
                assert _sha256(z.read(f['path']))==f['sha256'],'V196_CHAIN_MEMBER_CHANGED'
            (d/'v196.sqlite').write_bytes(z.read('V196_E3_REPAIR_APPEND_ONLY.sqlite'))
            v195_blob=z.read('V195_FROZEN_ACTUAL_TURN2_SOURCE.zip')
        with zipfile.ZipFile(io.BytesIO(v195_blob)) as z:
            v195_m=json.loads(z.read('v195_checkpoint_manifest.json'))
            for f in v195_m['files']:
                assert _sha256(z.read(f['path']))==f['sha256'],'V195_CHAIN_MEMBER_CHANGED'
            (d/'v195.sqlite').write_bytes(z.read('v195_E3_SECOND_USER_APPEND_ONLY.sqlite'))
            (d/'v194.zip').write_bytes(z.read('v194_FROZEN_RESEARCH_TURN1_PRIVATE.zip'))
            original_review=json.loads(z.read('v195_CHATGPT_FINAL_E3_TURN2_PRIVATE.json'))
        for p in ('v195.sqlite','v196.sqlite','v194.zip'):(d/p).chmod(0o600)
        old=json.loads((d/'V194_SHA_ONLY_RECEIPT.json').read_text());second=json.loads((d/'V195_SHA_ONLY_RECEIPT.json').read_text());repair=json.loads((d/'V196_SHA_ONLY_RECEIPT.json').read_text())
        for p in ('v195.sqlite','v196.sqlite'):
            with sqlite3.connect(d/p) as db:
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','CORRUPTED_OLD_SQLITE'
        review=E3ActualSecondUserAudit(frozen_archive=d/'v194.zip',external_receipt=old,
          private_db=d/'v195.sqlite',second_user_ref=original_review['manual_second_user_ref'],
          second_user_message_sha256=original_review['second_user_message_text_sha256'],create=False)
        v196=E3SecondReviewRepairOverlay(review,d/'v196.sqlite',
          expected_second_head=second['v195_second_review_journal_head_sha256'],create=False)
        assert v196.status()['repair_overlay_head_sha256']==repair['v196_overlay_head']
        with review._db() as db:_,old_judgments,_=review._audit(db)
        risk=make_risk_register(review,old_judgments)
        v198_copy=d/'v198.sqlite';v198_copy.write_bytes(Path(v198_db).read_bytes());v198_copy.chmod(0o600)
        with sqlite3.connect(v198_copy) as db:
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','CORRUPTED_V198_SQLITE'
        adjud=E3CorrectionAdjudication(review,v196,v198_copy,
          expected_repair_head=repair['v196_overlay_head'],risk_register=risk,create=False)
        s=adjud.status()
        assert s['adjudication_head_sha256']==v198_head,'V198_EXTERNAL_HEAD_CHANGED'
        assert s['reviewed']==16 and s['quarantined_preserved']==28
        view=build_effective_unapproved_view(adjud)
        evidence=build_84_evidence_triage(adjud)
        assert view['all_original_high_risk_blocked']==84 and len(evidence['risk_cases'])==84
        return {'status':s,'effective_view_sha256':_sha(view),
                'effective_provisional_candidates':view['effective_provisional_candidates_unapproved'],
                'risk_triage_sha256':_sha(evidence),
                'risk_families':evidence['risk_family_counts'],
                'issuer_document_raw_bytes_certified':False,
                'e3_approved':False,'e4_approved':False,'e5_published':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--v197-zip',required=True)
    p.add_argument('--v197-sha',required=True)
    p.add_argument('--v198-db',required=True)
    p.add_argument('--v198-head',required=True)
    a=p.parse_args()
    print(json.dumps(replay(v197_zip=a.v197_zip,v197_sha=a.v197_sha,
          v198_db=a.v198_db,v198_head=a.v198_head),ensure_ascii=False,sort_keys=True,indent=2))