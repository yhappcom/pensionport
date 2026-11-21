"""V228: V193 two ACTUAL user-command stage control, portable owner-private turn-1.

Public module; contains no owner text. NOT an API/LLM, blind-gold evaluator, or
host-message identity attestor. New later chat turn must provide a distinct
USER command; caller-supplied refs never become trusted host IDs.

Turn-1 source/study ZIP is PRIVATE and unencrypted; never upload to GitHub.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
from itertools import combinations
from copy import deepcopy
import hashlib, io, json, os, stat, zipfile
from typing import Any
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan
from v193_e3_two_user_turn_contract import validate_manual_turn_receipt

SCHEMA = 'IRE_V228_V193_TWO_DISTINCT_USER_TURNS_RUNTIME_GATE_V1'
ZIP_MEMBERS=('source.srt','native.json','cue250.json','e3_tasks.json','atom_pairs.json',
             'first_turn_research.json','turn1_manual_receipt.json','freeze_manifest.json')
SOURCE_MEMBERS=ZIP_MEMBERS[:6]
MAX_BYTES=12_000_000

def need(ok:Any,code:str):
    if not ok:raise InvalidInput('V228_TWO_TURN_'+code)

def digest(data:bytes)->str:
    need(type(data) is bytes,'NONBYTES')
    return hashlib.sha256(data).hexdigest()

def canonical(value:Any)->bytes:
    return (json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf8')

def load(raw:bytes,name:str)->dict:
    try:x=json.loads(raw.decode('utf8'))
    except (ValueError,UnicodeError,TypeError) as ex:raise InvalidInput('V228_TWO_TURN_BAD_JSON_'+name) from ex
    need(type(x) is dict,'DOC_TYPE_'+name)
    return x

def audit_study(source_raw:bytes,native_raw:bytes,cue_raw:bytes,e3_raw:bytes,pairs_raw:bytes,
                *,window_size:int=20)->dict:
    """Full source/claim/cue/relationship custody, not financial truth review."""
    try:
        need(type(window_size) is int and 1<=window_size<=1000,'WINDOW_SIZE')
        native=load(native_raw,'NATIVE');cue=load(cue_raw,'CUES');e3=load(e3_raw,'E3');pairs=load(pairs_raw,'PAIRS')
        source,manifest=make_original_plan(source_raw,native['video_id'],
                expected_source_sha256=digest(source_raw),window_size=window_size)
        audit_host_atomic_exchange(source,native)
        need(native['source_sha256']==source.source_sha256,'SOURCE_NATIVE_SHA')
        need(native['manifest_sha256']==source.manifest_sha256,'ORIGINAL_WINDOW_MANIFEST')
        need(cue['original_srt_sha256']==source.source_sha256 and
             cue['native_sha256']==digest(native_raw),'CUE_SOURCE_NATIVE_JOIN')
        need(e3['source_sha256']==source.source_sha256 and
             e3['native_sha256']==digest(native_raw),'E3_SOURCE_NATIVE_JOIN')
        need(pairs['source_sha256']==source.source_sha256 and
             pairs['native_sha256']==digest(native_raw),'PAIR_SOURCE_NATIVE_JOIN')
        atoms=native['atoms'];ids=[a['claim_id'] for a in atoms];idset=set(ids)
        need(len(ids)==len(idset) and len(ids)>0,'NATIVE_ID_DUPLICATE')
        need(len(cue['rows'])==len(source.cues),'CUE_COUNT')
        byid={a['claim_id']:a for a in atoms}
        for idx,r in enumerate(cue['rows'],1):
            txt=source.cues[idx-1].text
            need(r['cue_index']==idx and r['source_quote']==txt and
                 r['source_quote_sha256']==digest(txt.encode()),'CUE_QUOTE_OR_INDEX')
            want=sorted(a['claim_id'] for a in atoms if any(k['cue_index']==idx for k in a['source_refs']))
            need(r['original_primary_atom_ids']==want,'CUE_PRIMARY_JOIN')
            ctx=set(r['all_native_context_atom_ids'])
            need(ctx=={a['claim_id'] for a in atoms if idx in a['context_cue_indices']},'CUE_CONTEXT_JOIN')
        tasks=e3['task_rows'];need(len(tasks)==len(ids),'E3_TASK_COVERAGE')
        need({t['claim_id'] for t in tasks}==idset,'E3_TASK_SET')
        for t in tasks:
            a=byid[t['claim_id']]
            need(t['proposition']==a['proposition'],'E3_PROPOSITION_DRIFT')
            indices=set(a['context_cue_indices'])|{s['cue_index'] for s in a['source_refs']}
            ctx=t['source_context'];need(type(ctx) is list and len(ctx)==len(indices),'E3_CONTEXT_SHAPE')
            need({c['cue_index'] for c in ctx}==indices,'E3_CONTEXT_IDS')
            for c in ctx:
                actual=source.cues[c['cue_index']-1].text
                need(c['quote']==actual and c['quote_sha256']==digest(actual.encode()),'E3_QUOTE_SHA')
            need(t.get('e3_final_approved') is False and t.get('financial_fact_approved') is False and
                 t.get('v227_gold_precision_or_recall_certified') is False,'E3_PREMATURE_APPROVAL')
        prs=pairs['rows'];need(len(prs)==len(ids)*(len(ids)-1)//2,'PAIR_COUNT')
        need({tuple(sorted(r['claim_ids'])) for r in prs} == set(combinations(sorted(ids),2)),'PAIR_ENUMERATION')
        need(all(r.get('independently_verified_exact_equivalence') is False and
                 r.get('automatically_merged') is False and r.get('financial_fact_approved') is False for r in prs),
             'PAIR_FALSE_GOLD')
        need(e3.get('e3_final_approved') is False and e3.get('e4_approved') is False and
             e3.get('e5_published') is False and pairs.get('independent_recall_evaluation_completed') is False,
             'UNAUTHORIZED_E3_OR_GOLD')
        return {'original_cues':len(source.cues),'unapproved_native_atoms':len(atoms),
                'source_claim_pairs':len(prs),'e3_source_contexts_audited':len(tasks),
                'source_sha256':source.source_sha256,'native_sha256':digest(native_raw),
                'e3_sha256':digest(e3_raw),'window_count':len(manifest['windows']),
                'e3_final_approved':False,'independent_gold_certified':False}
    except InvalidInput:raise
    except (ValueError,TypeError,AttributeError,KeyError,IndexError) as ex:
        raise InvalidInput('V228_TWO_TURN_MALFORMED_SOURCE_OR_STUDY') from ex

def research_first_turn_rows(source_raw,native_raw,cue_raw,e3_raw,pairs_raw,
                             *,first_user_ref:str,first_user_text:str,window_size:int=20)->dict:
    """Re-review complete original cue inventory and retain prior V227 as explicit input.

    This is not a fresh blind study: original V227 candidate labels are disclosed.
    Does NOT contain a second-turn answer and does NOT certify semantic quality.
    """
    counts=audit_study(source_raw,native_raw,cue_raw,e3_raw,pairs_raw,window_size=window_size)
    cu=load(cue_raw,'CUES');native=load(native_raw,'NATIVE');e3=load(e3_raw,'E3')
    # Turn-1 authored current study: every source cue and candidate is retained.
    # Original text meaning checks require ChatGPT; this is an evidence census.
    classes=Counter(r['source_audit_class'] for r in cu['rows'])
    flags=sorted({r['cue_index'] for r in cu['rows'] if r['source_audit_class'] in
                  ('DISCOURSE_PROVISIONAL','MEDIA_CONTEXT_AV_HOLD','EXPLICIT_SOURCE_REVIEWED_NO_ATOM_PROVISIONAL')})
    need(flags==sorted(cu['outstanding_direct_audio_or_nonclaim_review_cues']),'PENDING_SOURCE_CUE_REVIEW_NOT_EXHAUSTIVE')
    need(len(native['atoms'])==len(e3['task_rows']),'ATOMS_TASKS_DIFFER')
    need(type(first_user_ref) is str and first_user_ref.startswith('user:') and
         type(first_user_text) is str and first_user_text.strip(),'MANUAL_TURN1_REQUIRED')
    return {'schema':'IRE_V228_OWNER_FIRST_USER_TURN_RESEARCH_REEXECUTION_V1',
       'phase':'RESEARCH_AND_FREEZE',
       'video_id':native['video_id'], 'source_sha256':counts['source_sha256'],
       'native_sha256':counts['native_sha256'],
       'research_input_v227_e3_sha256':counts['e3_sha256'],
       'full_original_cue_rows_reinspected':counts['original_cues'],
       'existing_unapproved_v6_atoms_reinspected':counts['unapproved_native_atoms'],
       'full_pairwise_lexical_screen_reinspected':counts['source_claim_pairs'],
       'cue_classes_from_source':dict(sorted(classes.items())),
       'pending_cue_ids_for_later_chatgpt_review':flags,
       'first_user_message_ref_manual':first_user_ref,
       'first_user_message_sha256':digest(first_user_text.encode('utf8')),
       'review_is_not_blind':True, 'old_v227_candidates_supplied_as_context':True,
       'all_source_claims_independently_measured':False,
       'e2_accuracy_final_pass':False,'e3_review_run_in_this_turn':False,
       'host_message_id_verified':False, 'e3_final_approved':False,
       'v123_e4_approved':False,'e5_knowledge_published':False}

def freeze_turn1_private(*,source_raw:bytes,native_raw:bytes,cue_raw:bytes,
             e3_raw:bytes,pairs_raw:bytes,first_user_ref:str,first_user_text:str,
             private_zip:Path,window_size:int=20)->dict:
    """Atomic private O_EXCL first-turn freeze and externally pinnable head."""
    study=research_first_turn_rows(source_raw,native_raw,cue_raw,e3_raw,pairs_raw,
            first_user_ref=first_user_ref,first_user_text=first_user_text,window_size=window_size)
    files={'source.srt':source_raw,'native.json':native_raw,'cue250.json':cue_raw,
           'e3_tasks.json':e3_raw,'atom_pairs.json':pairs_raw,
           'first_turn_research.json':canonical(study)}
    source_sha=digest(source_raw)
    first_head=digest(canonical({'schema':SCHEMA,'phase':'RESEARCH_AND_FREEZE',
             'source_sha256':source_sha,'files':{k:digest(v) for k,v in sorted(files.items())},
             'first_user_message_ref_manual':first_user_ref,
             'first_user_message_sha256':digest(first_user_text.encode('utf8'))}))
    first={'phase':'RESEARCH_AND_FREEZE','user_message_ref':first_user_ref,
           'user_message_sha256':digest(first_user_text.encode('utf8')),
           'source_sha256':source_sha,'owner_head_sha256':first_head,'research_frozen':True}
    contract=validate_manual_turn_receipt(first=first,second=None,
            source_sha256=source_sha,owner_head_sha256=first_head)
    need(contract['phase']=='AWAIT_SEPARATE_USER_VERIFICATION_COMMAND' and
         contract['two_user_turns_proven'] is False,'V193_TURN1_CONTRACT')
    files['turn1_manual_receipt.json']=canonical(first)
    manifest={'schema':SCHEMA,'phase':'RESEARCH_AND_FREEZE',
        'owner_video_id':study['video_id'],'source_sha256':source_sha,
        'owner_first_turn_head_sha256':first_head,
        'window_size':window_size,'claimed_user_turns':1,
        'v193_contract':'V193_E3_TWO_ACTUAL_USER_TURNS_MANDATORY_PROTOCOL_20261120.md',
        'members_sha256':{k:digest(v) for k,v in sorted(files.items())},
        'semantic_accuracy_certified':False,'two_user_turns_host_verified':False,
        'e3_final_approved':False,'e4_approved':False,'e5_published':False}
    files['freeze_manifest.json']=canonical(manifest)
    target=Path(private_zip);need(not target.exists() and not target.is_symlink(),'ZIP_ALREADY_EXISTS')
    target.parent.mkdir(parents=True,exist_ok=True)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for n in ZIP_MEMBERS:
            need(len(files[n])<=MAX_BYTES,'OVERSIZE_'+n)
            z.writestr(n,files[n])
    raw=buffer.getvalue();fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    except BaseException:
        target.unlink(missing_ok=True);raise
    return {'schema':SCHEMA,'status':'TURN1_FROZEN_AWAIT_DISTINCT_USER_TURN2',
       'private_zip_sha256':digest(raw),'manifest_sha256':digest(files['freeze_manifest.json']),
       'owner_first_turn_head_sha256':first_head,'source_sha256':source_sha,
       'original_cues':study['full_original_cue_rows_reinspected'],
       'native_drafts':study['existing_unapproved_v6_atoms_reinspected'],
       'outstanding_cues':len(study['pending_cue_ids_for_later_chatgpt_review']),
       'platform_message_provenance_verified':False,'chat_turns_completed':1,
       'e3_final_approved':False,'e4_approved':False,'e5_published':False,
       'private_zip_path':str(target)}

def verify_turn1_frozen(*,private_zip:Path,externally_pinned_zip_sha256:str,
               externally_pinned_manifest_sha256:str,
               externally_pinned_first_head_sha256:str,
               externally_pinned_source_sha256:str)->dict:
    """Fail closed without separately held pinned sha/head. No zip path traversal."""
    try:
        p=Path(private_zip)
        need(p.is_file() and not p.is_symlink() and
             not (stat.S_IMODE(p.stat().st_mode)&0o077),'OWNER_PRIVATE_ARCHIVE_REQUIRED')
        raw=p.read_bytes()
        need(digest(raw)==externally_pinned_zip_sha256,'EXTERNAL_ZIP_SHA_DRIFT')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos=z.infolist();need(len(infos)==len(ZIP_MEMBERS) and
                    {i.filename for i in infos}==set(ZIP_MEMBERS) and
                    len({i.filename for i in infos})==len(infos),'ZIP_MEMBERS_OR_TRAVERSAL')
            need(all(i.file_size<=MAX_BYTES for i in infos),'ZIP_OVERSIZED_MEMBER')
            content={n:z.read(n) for n in ZIP_MEMBERS}
        need(digest(content['freeze_manifest.json'])==externally_pinned_manifest_sha256,
             'EXTERNAL_MANIFEST_SHA_DRIFT')
        manifest=load(content['freeze_manifest.json'],'MANIFEST')
        need(manifest['schema']==SCHEMA and manifest['phase']=='RESEARCH_AND_FREEZE' and
             manifest['claimed_user_turns']==1 and
             manifest['source_sha256']==externally_pinned_source_sha256 and
             manifest['owner_first_turn_head_sha256']==externally_pinned_first_head_sha256 and
             manifest['two_user_turns_host_verified'] is False and
             manifest['e3_final_approved'] is False and manifest['e4_approved'] is False and
             manifest['e5_published'] is False,'FROZEN_MANIFEST_CONTRACT')
        for n,h in manifest['members_sha256'].items():
            need(n in content and digest(content[n])==h,'ARCHIVE_MEMBER_CHANGED_'+n)
        need(set(manifest['members_sha256'])==set(ZIP_MEMBERS)-{'freeze_manifest.json'},'MEMBER_HASH_COVERAGE')
        r=load(content['turn1_manual_receipt.json'],'RECEIPT')
        study=load(content['first_turn_research.json'],'RESEARCH')
        need(study['phase']=='RESEARCH_AND_FREEZE' and study['e3_review_run_in_this_turn'] is False and
             study['first_user_message_ref_manual']==r['user_message_ref'] and
             study['first_user_message_sha256']==r['user_message_sha256'],'FIRST_RESEARCH_RECORD')
        frame_files={k:v for k,v in content.items() if k in SOURCE_MEMBERS}
        expected_head=digest(canonical({'schema':SCHEMA,'phase':'RESEARCH_AND_FREEZE',
            'source_sha256':externally_pinned_source_sha256,
            'files':{k:digest(v) for k,v in sorted(frame_files.items())},
            'first_user_message_ref_manual':r['user_message_ref'],
            'first_user_message_sha256':r['user_message_sha256']}))
        need(expected_head==externally_pinned_first_head_sha256,'FROZEN_HEAD_CONTENT_MISMATCH')
        audit=audit_study(content['source.srt'],content['native.json'],content['cue250.json'],
           content['e3_tasks.json'],content['atom_pairs.json'],window_size=manifest['window_size'])
        need(study['full_original_cue_rows_reinspected']==audit['original_cues'] and
             study['existing_unapproved_v6_atoms_reinspected']==audit['unapproved_native_atoms'] and
             study['full_pairwise_lexical_screen_reinspected']==audit['source_claim_pairs'],
             'FIRST_TURN_RESEARCH_COVERAGE_MISMATCH')
        v193=validate_manual_turn_receipt(first=r,second=None,
            source_sha256=audit['source_sha256'],owner_head_sha256=expected_head)
        need(v193['two_user_turns_proven'] is False,'FAKE_TURN2')
        return {'manifest':manifest,'turn1_receipt':r,'study':study,
                'audit':audit,'content':content,'phase':'AWAIT_SEPARATE_USER_VERIFICATION_COMMAND'}
    except InvalidInput:raise
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,zipfile.BadZipFile,OSError) as ex:
        raise InvalidInput('V228_TWO_TURN_BAD_FROZEN_ARCHIVE') from ex

def prepare_turn2_source_only_review(*,private_zip:Path,externally_pinned_zip_sha256:str,
             externally_pinned_manifest_sha256:str,
             externally_pinned_first_head_sha256:str,
             externally_pinned_source_sha256:str,
             second_user_ref:str,second_user_text:str,
             current_actual_user_message_observed:bool)->dict:
    """Called only on a later USER instruction, not when turn1 is being frozen.

    The current ChatGPT must genuinely observe a second user message. The
    caller-provided confirmation is NOT a cryptographically trusted host claim.
    """
    first=verify_turn1_frozen(private_zip=private_zip,
       externally_pinned_zip_sha256=externally_pinned_zip_sha256,
       externally_pinned_manifest_sha256=externally_pinned_manifest_sha256,
       externally_pinned_first_head_sha256=externally_pinned_first_head_sha256,
       externally_pinned_source_sha256=externally_pinned_source_sha256)
    first_ref=first['turn1_receipt']['user_message_ref']
    need(current_actual_user_message_observed is True,'DISTINCT_USER_COMMAND_NOT_OBSERVED')
    need(type(second_user_ref) is str and second_user_ref.startswith('user:') and
         second_user_ref!=first_ref and type(second_user_text) is str and
         second_user_text.strip(),'SECOND_COMMAND_MISSING_OR_SAME')
    from ire.v6.source import parse_srt
    original=parse_srt(first['content']['source.srt'])
    return {'schema':'IRE_V228_TURN2_SOURCE_ONLY_CHATGPT_REVIEW_CHALLENGE_V1',
       'source_sha256':externally_pinned_source_sha256,
       'turn1_frozen_head_sha256':externally_pinned_first_head_sha256,
       'turn1_manual_user_ref':first_ref,
       'turn2_manual_user_ref':second_user_ref,
       'turn2_manual_message_sha256':digest(second_user_text.encode()),
       'actual_second_user_message_claimed_observed_not_host_cryptographic_proof':True,
       'host_two_turns_verified':False,
       'prior_candidate_propositions_visible_to_reviewer':False,
       'source_only_cues':[{'cue_index':i,'quote':c.text,
              'quote_sha256':digest(c.text.encode('utf8'))} for i,c in enumerate(original,1)],
       'final_e3_approved':False,'e4_authorized':False,'e5_knowledge_published':False,
       'independent_gold_certified':False,
       'phase':'TURN2_SOURCE_FIRST_REVIEW_PENDING'}

def reject_final_approval_without_trusted_evidence(*,e3_final_approved:bool=False,
                   e4_approved:bool=False,e5_published:bool=False,**_):
    # A documented two-turn procedure is not an independent financial fact/gold certification.
    need(not any([e3_final_approved,e4_approved,e5_published]),'FINAL_APPROVAL_NOT_AUTHORIZED')
    return {'e3_final_approved':False,'e4_approved':False,'e5_published':False}

def record_completed_turn2_review(*,private_zip:Path,externally_pinned_zip_sha256:str,
      externally_pinned_manifest_sha256:str,externally_pinned_first_head_sha256:str,
      externally_pinned_source_sha256:str,second_user_ref:str,second_user_text:str,
      current_actual_user_message_observed:bool,
      source_only_review_rows:list,atom_adjudication_rows:list,
      private_turn2_receipt:Path)->dict:
    """Append-only *actual second USER command* review receipt; NO approvals.

    This cannot be called in turn 1 without a new real ChatGPT/user interaction.
    A boolean from a caller does not independently prove an actual host turn;
    the resulting receipt explicitly says so. All source material stays PRIVATE.
    """
    challenge=prepare_turn2_source_only_review(private_zip=private_zip,
      externally_pinned_zip_sha256=externally_pinned_zip_sha256,
      externally_pinned_manifest_sha256=externally_pinned_manifest_sha256,
      externally_pinned_first_head_sha256=externally_pinned_first_head_sha256,
      externally_pinned_source_sha256=externally_pinned_source_sha256,
      second_user_ref=second_user_ref,second_user_text=second_user_text,
      current_actual_user_message_observed=current_actual_user_message_observed)
    study=verify_turn1_frozen(private_zip=private_zip,
      externally_pinned_zip_sha256=externally_pinned_zip_sha256,
      externally_pinned_manifest_sha256=externally_pinned_manifest_sha256,
      externally_pinned_first_head_sha256=externally_pinned_first_head_sha256,
      externally_pinned_source_sha256=externally_pinned_source_sha256)
    originals=challenge['source_only_cues']
    need(type(source_only_review_rows) is list and len(source_only_review_rows)==len(originals),
         'TURN2_FULL_ORIGINAL_CUE_REVIEW_REQUIRED')
    dispositions={'ASSERTION_CANDIDATE','QUESTION','QUOTE','NONCLAIM_PROVISIONAL',
                  'CONTEXT_OF_ANOTHER_CLAIM','OPEN_AUDIO_OR_SCREEN'}
    for a,b in zip(source_only_review_rows,originals):
        need(type(a) is dict and a.get('cue_index')==b['cue_index'] and
             a.get('quote')==b['quote'] and a.get('quote_sha256')==b['quote_sha256'],
             'TURN2_ORIGINAL_CUE_QUOTE_DRIFT')
        need(a.get('disposition') in dispositions and
             type(a.get('review_reason')) is str and len(a['review_reason'].strip())>=12,
             'TURN2_SOURCE_FIRST_MEANING_REASON_MISSING')
        need(a.get('is_independent_blind_gold') is False and
             a.get('financial_fact_approved') is False,
             'TURN2_CUE_FALSE_GOLD_OR_FINANCE')
    native=load(study['content']['native.json'],'NATIVE')
    ids={a['claim_id'] for a in native['atoms']}
    need(type(atom_adjudication_rows) is list and len(atom_adjudication_rows)==len(ids),
         'TURN2_EVERY_NATIVE_CLAIM_REVIEW_REQUIRED')
    need({a.get('claim_id') for a in atom_adjudication_rows if type(a) is dict}==ids,
         'TURN2_ATOM_ID_COVERAGE')
    decisions={'HOLD','QUARANTINE','REQUIRES_SOURCE_MEANING_REPAIR',
               'APPROVE_CANDIDATE_PENDING_INDEPENDENT_EVIDENCE'}
    for a in atom_adjudication_rows:
        need(type(a) is dict and a.get('disposition') in decisions and
             type(a.get('source_grounded_reason')) is str and
             len(a['source_grounded_reason'].strip())>=12,'TURN2_ATOM_REASON_MISSING')
        need(a.get('e3_final_approved') is False and
             a.get('financial_fact_approved') is False and
             a.get('independent_gold_certified') is False,
             'TURN2_ATOM_FORGED_APPROVAL')
    review={'schema':'IRE_V228_PRIVATE_SECOND_USER_CHATGPT_SOURCE_AND_ATOM_VERDICT_V1',
        'phase':'CHATGPT_FINAL_SEMANTIC_VERIFICATION',
        'turn1_frozen_head_sha256':externally_pinned_first_head_sha256,
        'source_sha256':externally_pinned_source_sha256,
        'second_user_ref_manual':second_user_ref,
        'second_user_text_sha256':digest(second_user_text.encode('utf8')),
        'source_only_review_rows':source_only_review_rows,
        'atom_adjudication_rows':atom_adjudication_rows,
        'review_complete_as_internal_not_blind_gold':True,
        'host_user_turn_proven_by_cryptographic_id':False,
        'e3_final_approved':False,'e4_approved':False,'e5_published':False}
    review_head=digest(canonical(review))
    first=study['turn1_receipt']
    second={'phase':'CHATGPT_FINAL_SEMANTIC_VERIFICATION',
       'user_message_ref':second_user_ref,
       'user_message_sha256':digest(second_user_text.encode('utf8')),
       'source_sha256':externally_pinned_source_sha256,
       'owner_head_sha256':externally_pinned_first_head_sha256,
       'review_recorded':True,'review_head_sha256':review_head}
    contract=validate_manual_turn_receipt(first=first,second=second,
        source_sha256=externally_pinned_source_sha256,
        owner_head_sha256=externally_pinned_first_head_sha256)
    need(contract['phase']=='TWO_DISTINCT_USER_COMMANDS_CLAIMED_UNVERIFIED' and
         contract['two_user_turns_proven'] is False and
         contract['e3_semantic_accuracy_certified'] is False,
         'V193_TURN2_CONTRACT_NOT_SATISFIED')
    record={'schema':'IRE_V228_TWO_DISTINCT_USER_MESSAGE_E3_REVIEW_HOLD_RECEIPT_V1',
        'v193_contract_receipt':contract,'source_sha256':externally_pinned_source_sha256,
        'first_frozen_head_sha256':externally_pinned_first_head_sha256,
        'second_review_head_sha256':review_head,
        'turn1_manual_message_ref':first['user_message_ref'],
        'turn2_manual_message_ref':second_user_ref,
        'turn2_review':review,'e3_formal_approved':False,
        'e4_authorized':False,'e5_published':False,
        'independent_blind_gold_certified':False}
    target=Path(private_turn2_receipt)
    need(not target.exists() and not target.is_symlink(),'SECOND_REVIEW_ALREADY_FROZEN')
    target.parent.mkdir(parents=True,exist_ok=True)
    content=canonical(record)
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,'wb') as f:f.write(content);f.flush();os.fsync(f.fileno())
    except BaseException:
        target.unlink(missing_ok=True);raise
    return {'schema':record['schema'],
      'status':'TURN2_CHATGPT_REVIEW_RECORDED_E3_FINAL_HOLD',
      'first_frozen_head_sha256':externally_pinned_first_head_sha256,
      'second_review_head_sha256':review_head,
      'second_receipt_sha256':digest(content),
      'original_cues_reviewed':len(originals),
      'native_claim_adjudications_recorded':len(ids),
      'host_distinct_user_turns_cryptographically_verified':False,
      'independent_blind_gold_certified':False,
      'e3_final_approved':False,'e4_authorized':False,'e5_published':False}