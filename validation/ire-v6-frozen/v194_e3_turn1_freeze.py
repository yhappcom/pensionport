"""V194 research-first-turn freeze and next-user-turn restore guard.

Owner-private original and full research are NEVER committed to GitHub.
This module verifies a V176 native research-only journal, original SRT and
source-quoted ChatGPT research summary, writes an immutable private checkpoint,
and cannot perform final E3 review or any V123/E4/E5 action.

Neither caller-provided user refs nor separate Python processes prove host turns.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,io,json,os,sqlite3,stat,tempfile,zipfile
from ire.v6.codec import sha256,canonical
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession
from v193_e3_two_user_turn_contract import validate_manual_turn_receipt

SCHEMA='IRE_V194_CMA_REAL_CHAT_TURN1_FREEZE_V1'
FILES=('cma_original.srt','cma_first_research.json','cma_owner_v176.sqlite','turn1_manual_receipt.json')
RESEARCH_SCHEMA='IRE_V194_CHATGPT_RESEARCH_FIRST_TURN_PRIVATE_V1'

def _need(ok,why):
    if not ok:raise InvalidInput('V194_E3_TURN1_'+why)

def _hex(s):
    return isinstance(s,str) and len(s)==64 and all(c in '0123456789abcdef' for c in s)

def _json(x):return canonical(x)

def _write_excl(path:Path,raw:bytes):
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw)

def check_native_research(original:bytes, research:dict, sqlite_path:Path, *, video_id:str):
    _need(type(research) is dict and research.get('schema')==RESEARCH_SCHEMA and
          research.get('video_id')==video_id and research.get('research_phase')=='RESEARCH_AND_FREEZE' and
          research.get('e3_final_review_run') is False and
          research.get('host_verified_two_turns') is False and
          research.get('e3_final_approved') is False and
          research.get('v123_e4_invoked') is False and
          research.get('e5_knowledge_published') is False and
          research.get('quality_precision') is None and research.get('quality_recall') is None and
          research.get('official_claim_verified_count')==0,
          'NO_FINANCE_OR_E3_APPROVAL')
    _need(isinstance(original,bytes) and research['source_sha256']==sha256(original),
          'SOURCE_HASH_DRIFT')
    _need(sqlite_path.is_file() and not sqlite_path.is_symlink() and
          not (stat.S_IMODE(sqlite_path.stat().st_mode)&0o077),'PRIVATE_SOURCE_DB_REQUIRED')
    eng=EngineChatSession(sqlite_path,original,video_id,owner_source_sha256=sha256(original),window_size=120)
    status=eng.progress()
    total=status['cue_total']
    _need(total>0 and status['cue_remaining']==0 and status['source_first_review_complete'] and
          status['cue_reviewed']==research.get('cue_count') and
          status['checkpoint_head_sha256']==research.get('frozen_v176_head') and
          not status['e4_pass_claimed'] and not status['e5_knowledge_written'],
          'FIRST_RESEARCH_NOT_FROZEN')
    parents=research.get('parents');atoms=research.get('claims');issues=research.get('unresolved_cue_issues')
    _need(isinstance(parents,list) and parents and isinstance(atoms,list) and
          isinstance(issues,list) and research.get('claim_count')==len(atoms),'RESEARCH_SHAPE')
    start=1;anchors=[]
    for i,p in enumerate(parents,1):
        _need(isinstance(p,dict) and p.get('parent_id')==f'P{i:03}' and
              p.get('start_cue')==start and type(p.get('end_cue')) is int and
              start<=p['end_cue']<=total and
              isinstance(p.get('semantic_parent'),str) and len(p['semantic_parent'])>=8 and
              p.get('parent_completeness_status')=='FIRST_TURN_PROVISIONAL',
              'PARENT_CENSUS_OR_ORDER')
        a=p.get('claim_cues');b=p.get('no_claim_cues')
        _need(isinstance(a,list) and isinstance(b,list) and
              a==sorted(set(a)) and b==sorted(set(b)) and
              sorted(a+b)==list(range(start,p['end_cue']+1)),
              'PARENT_CUE_CENSUS')
        anchors.extend(a);start=p['end_cue']+1
    _need(start==total+1 and len(anchors)==len(atoms) and sorted(anchors)==[a.get('cue_index') for a in atoms],
          'CLAIM_PARENT_COVERAGE')
    with eng._connect() as con:_,rowmap=eng._audit(con)
    for atom in atoms:
        i=atom['cue_index']; row=rowmap[i][1]
        _need(row['disposition']=='ASSERTION' and len(row['claims'])==1 and
              atom['kind']==row['claims'][0]['kind'] and
              atom['proposition']==row['claims'][0]['proposition'] and
              atom['quote']==eng.source.cues[i-1].text and
              atom['quote']==row['claims'][0]['quote'] and
              atom['evidence_cues']==row['claims'][0]['context_cue_indices'] and
              atom['high_risk']==row['claims'][0]['high_risk'] and
              atom['needs_official_source']==row['claims'][0]['needs_official_source'] and
              atom['financial_fact_verified'] is False and
              atom['e3_semantic_approved'] is False,
              'CLAIM_NOT_NATIVE_PINNED')
    for p in parents:
        for i in p['no_claim_cues']:
            _need(rowmap[i][1]['disposition'] in ('NON_RESEARCH','OPEN') and
                  not rowmap[i][1]['claims'],'CUE_REVIEW_MISMATCH')
    _need(all(type(x.get('cue_index')) is int and 1<=x['cue_index']<=total and
              isinstance(x.get('task'),str) and len(x['task'])>=10 for x in issues),
          'UNRESOLVED_ISSUE_BROKEN')
    _need(all(s.get('status') in {'WEB_TEXT_PRELIMINARY_NOT_ISSUER_BYTES_CERTIFIED',
             'HISTORICAL_WEB_TEXT_PRELIMINARY'} for s in research.get('official_sources_preliminary',[])),
          'ISSUER_BYTES_NOT_CERTIFIED')
    return {'source_sha256':sha256(original),'owner_head_sha256':status['checkpoint_head_sha256'],
            'video_id':video_id,'cue_count':total,'parent_count':len(parents),
            'claim_count':len(atoms),'native_events':None,
            'high_risk_flags':sum(bool(x['high_risk']) for x in atoms),
            'open_cues':status['unresolved_open_cues'],
            'unresolved_tasks':len(issues),
            'independent_accuracy':None,'e3_final_review':False,'e4_invoked':False,'e5_published':False}

def freeze(*, original:bytes,research:dict,sqlite_path:Path,
           archive_path:Path,manual_first_user_ref:str,manual_first_user_message_sha256:str,
           video_id:str):
    _need(not archive_path.exists() and not archive_path.is_symlink(),'NO_OVERWRITE')
    result=check_native_research(original,research,sqlite_path,video_id=video_id)
    receipt=validate_manual_turn_receipt(first={
        'phase':'RESEARCH_AND_FREEZE','user_message_ref':manual_first_user_ref,
        'user_message_sha256':manual_first_user_message_sha256,
        'source_sha256':result['source_sha256'],
        'owner_head_sha256':result['owner_head_sha256'],'research_frozen':True},
        second=None,source_sha256=result['source_sha256'],
        owner_head_sha256=result['owner_head_sha256'])
    _need(receipt['phase']=='AWAIT_SEPARATE_USER_VERIFICATION_COMMAND' and
          not receipt['host_separate_turns_verified'] and
          not receipt['e3_semantic_accuracy_certified'],'SECOND_USER_COMMAND_NOT_YET_PRESENT')
    contents={FILES[0]:original,FILES[1]:_json(research),
              FILES[2]:sqlite_path.read_bytes(),FILES[3]:_json(receipt)}
    manifest={'schema':SCHEMA,'video_id':video_id,'source_sha256':result['source_sha256'],
              'owner_head_sha256':result['owner_head_sha256'],
              'turn1_research_sha256':sha256(contents[FILES[1]]),
              'files':[{'path':f,'sha256':sha256(contents[f]),'bytes':len(contents[f])} for f in FILES],
              'counts':result,'phase':'AWAIT_SEPARATE_USER_VERIFICATION_COMMAND',
              'current_user_turns_recorded':1,'platform_turn_identity_verified':False,
              'independent_gold':False,'e3_approved':False,'e4_approved':False,
              'e5_published':False}
    contents['turn1_manifest.json']=_json(manifest)
    archive_path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=archive_path.parent) as tmp:
        intermediate=Path(tmp)/'private_unsigned_tmp.zip'
        with zipfile.ZipFile(intermediate,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
            for name in FILES+('turn1_manifest.json',):
                info=zipfile.ZipInfo(name,date_time=(2026,11,20,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=(0o600&0xFFFF)<<16
                z.writestr(info,contents[name])
        _write_excl(archive_path,intermediate.read_bytes())
    return {**result,'schema':'IRE_V194_TURN1_SOURCE_FROZEN_SHA_ONLY_RECEIPT_V1',
            'archive_sha256':sha256(archive_path.read_bytes()),
            'manifest_sha256':sha256(contents['turn1_manifest.json']),
            'first_turn_text_sha256':manual_first_user_message_sha256,
            'untrusted_manual_first_user_ref':manual_first_user_ref,
            'phase':receipt['phase'],'platform_turn_identity_verified':False,
            'actual_second_user_message_observed':False,
            'e3_final_review':False,'e3_approved':False,'e4_approved':False,'e5_published':False}

def restore_verify(*,archive_path:Path,expected_archive_sha256:str,
                   expected_manifest_sha256:str,expected_source_sha256:str,
                   expected_owner_head_sha256:str):
    _need(all(_hex(x) for x in (expected_archive_sha256,expected_manifest_sha256,
                               expected_source_sha256,expected_owner_head_sha256)),
          'EXTERNAL_PIN_REQUIRED')
    raw=archive_path.read_bytes()
    _need(sha256(raw)==expected_archive_sha256,'ARCHIVE_HASH_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        _need(set(z.namelist())==set(FILES)|{'turn1_manifest.json'} and
              len(z.namelist())==len(set(z.namelist())) and
              all(x.file_size<4_000_000 for x in z.infolist()),
              'PRIVATE_ARCHIVE_MEMBERS_CHANGED')
        contents={x:z.read(x) for x in FILES+('turn1_manifest.json',)}
    _need(sha256(contents['turn1_manifest.json'])==expected_manifest_sha256,
          'MANIFEST_HASH_MISMATCH')
    manifest=json.loads(contents['turn1_manifest.json'])
    _need(manifest['schema']==SCHEMA and manifest['phase']=='AWAIT_SEPARATE_USER_VERIFICATION_COMMAND' and
          manifest['source_sha256']==expected_source_sha256 and
          manifest['owner_head_sha256']==expected_owner_head_sha256 and
          manifest['platform_turn_identity_verified'] is False and
          manifest['e3_approved'] is False and
          manifest['e4_approved'] is False and manifest['e5_published'] is False,
          'FROZEN_PHASE_OR_APPROVAL_FORGERY')
    for m in manifest['files']:
        _need(m['path'] in FILES and sha256(contents[m['path']])==m['sha256'] and
              len(contents[m['path']])==m['bytes'],'FILE_HASH_MISMATCH')
    _need([x['path'] for x in manifest['files']]==list(FILES),'FILE_CENSUS_MISMATCH')
    with tempfile.TemporaryDirectory() as tmp:
        d=Path(tmp);db=d/'owner.sqlite';_write_excl(db,contents['cma_owner_v176.sqlite'])
        checked=check_native_research(contents['cma_original.srt'],
                                      json.loads(contents['cma_first_research.json']),db,
                                      video_id=manifest['video_id'])
    _need(checked['owner_head_sha256']==expected_owner_head_sha256 and
          checked['source_sha256']==expected_source_sha256,'REPLAY_SOURCE_OR_HEAD_DRIFT')
    receipt=json.loads(contents['turn1_manual_receipt.json'])
    _need(receipt['phase']=='AWAIT_SEPARATE_USER_VERIFICATION_COMMAND' and
          receipt['recorded_distinct_user_commands']==1 and
          not receipt['two_user_turns_proven'] and
          not receipt['host_separate_turns_verified'],'TURN_COUNT_FORGERY')
    return {**checked,'zip_members_verified':len(FILES)+1,
            'phase':receipt['phase'],'platform_turn_identity_verified':False,
            'turn2_review_performed':False,'e3_approved':False,'e4_approved':False,'e5_published':False}