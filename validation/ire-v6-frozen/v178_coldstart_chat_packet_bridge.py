"""V178: true source-only cold-start transfer from live ChatGPT into native V176.

The packet is authored in the active ChatGPT conversation against an original
SRT; this module cannot invoke a model, certify that authorship, certify
external financial facts, or issue any native V123/E4/E5 approval.

A packet may be transferred between conversations as owner-private data.
Each V176 challenge is rebuilt from the original bytes and submitted through
V176's unmodified native source-first validation; private video/rows are not
part of GitHub CI. This is a *transport*, not a new semantics engine.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession, COMMIT, ZERO

SCHEMA = 'CS178_IN_CHAT_V176_FORMATTED_SOURCE_ONLY_ROWS_V1'
ROW_KEYS={'cue_index','source_text_sha256','disposition','analysis',
          'speaker_role','limitations_checked','claims'}


def _need(x,reason):
    if not x:raise InvalidInput('V178_COLDSTART_'+reason)


def import_chat_packet(db_path,raw,video_id,packet,*,original_sha256,
                       expected_head,expected_cues_reviewed,
                       window_size=125,allow_new_session=False,
                       context_radius=8):
    """Apply *only explicit actual model-authored rows* to frozen V176 checks.

    Requires external old head, reviewed count and original source SHA. The
    default refuses a missing journal, preventing fresh resets on resume.
    May commit multiple V176 batches; if interrupted use checkpoint/resume
    guards and only the uncommitted suffix in a new packet.
    """
    _need(type(raw) is bytes and hashlib.sha256(raw).hexdigest()==original_sha256,
          'RAW_SOURCE_SHA_MISMATCH')
    _need(type(packet) is dict and set(packet)=={
          'schema','owner_source_sha256','first_cue','last_cue',
          'chat_authored_review_source','original_journal_head_sha256',
          'supplied_prior_research','native_approval','rows'},
          'PACKET_SCHEMA')
    _need(packet['schema']==SCHEMA and
          packet['owner_source_sha256']==original_sha256 and
          packet['chat_authored_review_source']=='ACTIVE_CONVERSATION_NONCRYPTO' and
          packet['supplied_prior_research'] is False and
          packet['native_approval'] is False, 'SOURCE_ONLY_AND_NO_APPROVAL')
    _need(type(expected_head) is str and len(expected_head)==64 and
          all(ch in '0123456789abcdef' for ch in expected_head) and
          type(expected_cues_reviewed) is int and expected_cues_reviewed>=0,
          'EXTERNAL_RESUME_PINS_REQUIRED')
    path=Path(db_path)
    if path.exists() or path.is_symlink():
        _need(not allow_new_session,'NEW_SESSION_MUST_NOT_OVERWRITE')
        _need(path.is_file() and not path.is_symlink(),'PRIVATE_SQLITE_NOT_REGULAR')
        import stat
        _need(not (stat.S_IMODE(path.stat().st_mode)&0o077),
              'INSECURE_PRIVATE_SQLITE')
    else:
        _need(allow_new_session and expected_head==ZERO and
              expected_cues_reviewed==0,'MISSING_EXISTING_SESSION_DO_NOT_RESET')
    rows=packet['rows']
    _need(type(rows) is list and len(rows)>=1 and
          type(packet['first_cue']) is int and
          type(packet['last_cue']) is int and
          packet['first_cue']==expected_cues_reviewed+1 and
          packet['last_cue']==expected_cues_reviewed+len(rows) and
          [r.get('cue_index') for r in rows if type(r) is dict]==
             list(range(packet['first_cue'],packet['last_cue']+1)) and
          all(type(r) is dict and set(r)==ROW_KEYS for r in rows),
          'EXACT_CONTIGUOUS_PACKET_CENSUS')
    engine=EngineChatSession(path,raw,video_id,
                 owner_source_sha256=original_sha256,window_size=window_size)
    status=engine.progress()
    _need(status['checkpoint_head_sha256']==expected_head and
          status['cue_reviewed']==expected_cues_reviewed,
          'PREVIOUS_TURN_HEAD_OR_COUNT_MISMATCH')
    committed=[]
    index=0
    while index<len(rows):
        challenge=engine.prepare(limit=min(20,len(rows)-index),
                 context_radius=context_radius,source_first_only=True)
        _need(challenge['type']=='CLASSIFY_SOURCE_CUES',
              'NATIVE_ENGINE_NOT_ISSUING_CLASSIFY_CHALLENGE')
        selected=challenge['target_cues']
        segment_rows=rows[index:index+len(selected)]
        _need(len(selected)==len(segment_rows) and
              [r['cue_index'] for r in segment_rows]==
              [r['cue_index'] for r in selected] and
              all(a['source_text_sha256']==b['source_text_sha256']
                  for a,b in zip(segment_rows,selected)),
              'NATIVE_SOURCE_ISSUANCE_OR_ROW_MISMATCH')
        answer={'schema':COMMIT,
                'challenge_sha256':challenge['challenge_sha256'],
                'review_executor':'CHATGPT_IN_CHAT',
                'responses':segment_rows}
        receipt=engine.submit(challenge,answer)
        _need(receipt['status']=='CHAT_SOURCE_REVIEW_COMMITTED_UNRELEASED' and
              receipt['cues_committed']==len(segment_rows) and
              receipt['e4_approved'] is False and
              receipt['e5_published'] is False,
              'NATIVE_CHAT_COMMIT_NOT_SAFE')
        committed.append({'first_cue':segment_rows[0]['cue_index'],
                          'last_cue':segment_rows[-1]['cue_index'],
                          'native_journal_head_sha256':receipt['checkpoint_head_sha256']})
        index+=len(segment_rows)
    final=engine.progress()
    _need(final['cue_reviewed']==expected_cues_reviewed+len(rows) and
          final['e4_pass_claimed'] is False and
          final['v123_pass_claimed'] is False and
          final['e5_knowledge_written'] is False,'FALSE_RESEARCH_PUBLICATION')
    return {'schema':'IRE_V178_NATIVE_COLDSTART_IMPORT_UNRELEASED_V1',
            'owner_source_sha256':original_sha256,
            'first_cue_committed':packet['first_cue'],
            'last_cue_committed':packet['last_cue'],
            'native_batch_receipts':committed,
            'native_checkpoint_head_sha256':final['checkpoint_head_sha256'],
            'remaining_original_cues':final['cue_remaining'],
            'v123_approved':False,'e4_approved':False,'e5_released':False,
            'prior_research_imported':False,
            'actual_chat_identity_cryptographically_authenticated':False}