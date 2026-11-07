"""Validate V5 #1-#5 chat-authored per-window semantic *draft* coverage.

A source ZIP is optional. With it, reconstructs exact original V5 18-cue /
1600-character windows and verifies all byte-level source hashes. Without it,
CI can verify only frozen recorded metadata, safety state and cue continuity.

Neither mode proves atomic-claim extraction recall, external financial fact
approval, model-generated final answer accuracy, or personal suitability.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

PREFIX = Path('ire/v5/validation')
VIDEO_IDS = ('sz5N9WJS310', '6VEfKF7BzZU', 'OiDTNstaSpM',
             'aNfGrcO6WPI', 'qtluAViPpsQ')
CUES = (1195,1347,785,758,1044)
WINDOWS = (67,76,44,43,58)
RAW_ZIP_SHA256 = '00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
_END = re.compile(r'(?:[.!?。]|(?:입니다|습니다|합니다|됩니다|네요|세요|어요|아요|겠죠|거죠|습니까))\s*$')
_TM = re.compile(r'^(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})$')
_ALLOWED_KINDS = {'CONDITIONAL_STRATEGY_OPINION', 'USER_QUESTION',
 'HYPOTHETICAL_FINANCIAL_MODEL', 'TAX_OR_PENSION_RULE', 'NON_FINANCIAL_CONTEXT',
 'PRODUCT_TERMS_OR_RISK','TIME_SENSITIVE_MACRO_DATA', 'EXPERIENCE_OR_UNVERIFIED_HISTORY'}

class WindowReviewError(ValueError): pass

def require(ok: bool, label: str) -> None:
    if not ok: raise WindowReviewError(label)

def ms(t: str) -> int:
    m=_TM.fullmatch(t)
    require(m is not None,'WINDOW_REVIEW_BAD_SOURCE_TIME')
    h,minute,sec,millisecond=map(int,m.groups())
    require(minute<60 and sec<60,'WINDOW_REVIEW_BAD_TIME_UNIT')
    return ((h*60+minute)*60+sec)*1000+millisecond

def source_windows(raw: bytes) -> list[dict]:
    text=raw.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n').strip()
    cues=[]
    for block in re.split(r'\n\s*\n',text):
        lines=block.split('\n')
        require(len(lines)>=3 and lines[0].strip().isdigit(),'WINDOW_REVIEW_BAD_SOURCE_CUE')
        n=int(lines[0])
        require(n==len(cues)+1,'WINDOW_REVIEW_CUE_GAP')
        times=lines[1].split(' --> ')
        require(len(times)==2,'WINDOW_REVIEW_BAD_SOURCE_TIME_ARROW')
        start,end=ms(times[0].strip()),ms(times[1].strip())
        require(start<=end,'WINDOW_REVIEW_TIME_REVERSED')
        body=' '.join(x.strip() for x in lines[2:] if x.strip())
        require(bool(body),'WINDOW_REVIEW_EMPTY_SOURCE_TEXT')
        cues.append((n,start,end,body))
    grouped=[];cur=[];chars=0;force=set()
    def flush():
        nonlocal cur,chars
        if cur: grouped.append(cur)
        cur=[];chars=0
    for cue in cues:
        if cur:
            prev=cur[-1]
            if len(cur)>=18 or chars+1+len(cue[3])>1600:
                if not _END.search(prev[3]): force.add(len(grouped))
                flush()
            elif len(cur)>=6 and max(0,cue[1]-prev[2])>=2500 and _END.search(prev[3]):
                flush()
        cur.append(cue);chars+=len(cue[3])+1
    flush()
    result=[]
    for idx,group in enumerate(grouped,1):
        result.append({'window_id':f'W{idx:05d}',
         'first_cue':group[0][0],'last_cue':group[-1][0],
         'start_ms':group[0][1],'end_ms':group[-1][2],
         'primary_text_sha256':hashlib.sha256(' '.join(x[3] for x in group).encode()).hexdigest(),
         'continuation_boundary_review_required':idx-1 in force})
    return result

def verify(root: Path, source_zip:Path|None=None, replacement:dict|None=None) -> dict:
    root=Path(root)
    by_video=[]; selected=None; num_risk=0; counts=Counter()
    for n,(vid,expected_cues,expected_windows) in enumerate(zip(VIDEO_IDS,CUES,WINDOWS),1):
        path=root/PREFIX/f'v5_first_five_video_{n:02d}_window_review_20261106.json'
        data=json.loads(path.read_text('utf-8')) if replacement is None or n!=1 else replacement
        require(data.get('schema')=='IRE_V5_FIRST_FIVE_MANUALLY_REVIEWED_WINDOWS_COMPACT_V1'
                and data.get('as_of')=='2026-11-06' and data.get('video_number')==n
                and data.get('video_id')==vid and data.get('expected_original_cues')==expected_cues
                and data.get('window_count')==expected_windows
                and data.get('source_archive_sha256')==RAW_ZIP_SHA256,
                'WINDOW_REVIEW_VIDEO_ID_COUNT_SHA_MISMATCH')
        require(data.get('source_window_full_review_pass')=='PROVISIONAL_WINDOW_MEANING_ONLY'
                and data.get('current_law_fact_research_completed') is False
                and data.get('legacy_knowledge_approved') is False
                and data.get('independent_atomic_claim_recall_proven') is False
                and data.get('historical_v5_per_window_events_altered') is False
                and data.get('personalized_advice_approved') is False,
                'WINDOW_REVIEW_FALSE_FINANCIAL_CERTIFICATION')
        rows=data.get('records',[])
        require(type(rows) is list and len(rows)==expected_windows,
                'WINDOW_REVIEW_UNPROCESSED_WINDOWS')
        start=1
        scopes=data.get('critical_applicability_scopes',{})
        require(type(scopes) is dict and bool(scopes),'WINDOW_REVIEW_SCOPES_MISSING')
        for i,row in enumerate(rows,1):
            require(row.get('window_id')==f'W{i:05d}'
                    and row.get('first_cue')==start
                    and type(row.get('last_cue')) is int
                    and start<=row['last_cue']<=expected_cues,
                    'WINDOW_REVIEW_CUE_COVERAGE_GAP')
            start=row['last_cue']+1
            require(type(row.get('start_ms')) is int and type(row.get('end_ms')) is int
                    and row['start_ms']<=row['end_ms']
                    and re.fullmatch('[0-9a-f]{64}',str(row.get('primary_text_sha256','')))
                    and type(row.get('continuation_boundary_review_required')) is bool,
                    'WINDOW_REVIEW_MISSING_OR_UNANCHORED_ORIGINAL')
            require(row.get('meaning_type') in _ALLOWED_KINDS
                    and len(row.get('semantic_summary','').strip())>=14
                    and row.get('domain') in scopes
                    and len(scopes[row['domain']])>=30
                    and isinstance(row.get('risk_review_codes'),list)
                    and isinstance(row.get('scoped_official_source_ids'),list),
                    'WINDOW_REVIEW_MISSING_MEANING_LIMITS')
            require(row.get('fact_approved') is False and row.get('personal_action_approved') is False,
                    'WINDOW_REVIEW_UNEARNED_ADVISORY_PROMOTION')
            counts[row['meaning_type']]+=1
            num_risk+=bool(row['risk_review_codes'])
        require(start==expected_cues+1,'WINDOW_REVIEW_TRAILING_CUES_UNREVIEWED')
        by_video.append((n,data,rows))
    if source_zip is not None:
        src=Path(source_zip)
        require(hashlib.sha256(src.read_bytes()).hexdigest()==RAW_ZIP_SHA256,
                'WINDOW_REVIEW_PRIVATE_ARCHIVE_HASH_MISMATCH')
        with zipfile.ZipFile(src) as z:
            for n,data,rows in by_video:
                vid=VIDEO_IDS[n-1]
                matching=[s for s in z.namelist() if s==f'youtube-transcript-{vid}.srt'
                          or s.endswith(f'/youtube-transcript-{vid}.srt')]
                require(len(matching)==1,'WINDOW_REVIEW_SOURCE_SRT_NOT_UNIQUE')
                raw=z.read(matching[0]); src_windows=source_windows(raw)
                require(len(src_windows)==WINDOWS[n-1],
                        'WINDOW_REVIEW_SOURCE_PLANNER_COUNT_CHANGED')
                for public,derived in zip(rows,src_windows):
                    require(all(public[k]==val for k,val in derived.items()),
                            'WINDOW_REVIEW_ORIGINAL_WINDOW_HASH_OR_BOUNDARY_MISMATCH')
        private_rechecked=True
    else: private_rechecked=False
    require(sum(counts.values())==288,'WINDOW_REVIEW_TOTAL_288_MISSING')
    return {'schema':'IRE_V5_FIRST_FIVE_288_WINDOW_MEANING_GATE_V1',
            'exact_private_archive_reopened_and_288_hashes_verified':private_rechecked,
            'video_cue_count':sum(CUES),'source_windows_with_chat_authored_meaning':sum(WINDOWS),
            'previous_public_v5_engine_event_windows_still_only':5,
            'new_provisional_window_meaning_drafts_outside_public_engine_receipts':283,
            'window_risk_or_scope_review_flagged':num_risk,
            'mode_counts':dict(counts),'independently_measured_atomic_claim_recall':False,
            'all_financial_claims_currently_source_certified':False,
            'approved_personal_trade_or_allocation':False,
            'legacy_B04_formally_merged':False,
            'full_research_release_go':False,
            'next_video_expansion_go':False}

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--source-zip',type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.root,a.source_zip),ensure_ascii=False,sort_keys=True))
if __name__=='__main__':main()