"""Reconstruction of published V33/V39 derivation for independent pinned source census.

All raw subtitles and candidate prose remain local; only aggregate SHA/counters are printed.
This is source/segmentation replay, NOT a new semantic judgment or gold evaluation.
"""
from __future__ import annotations
import hashlib,json,re,zipfile,argparse
from pathlib import Path
from dataclasses import dataclass

PINNED_SOURCE_ZIP='00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd'
PINNED_V42_COHORT='a17442d2a3ce6df555b601e11f47d68a50c58fea683103a1766cea05c48f5381'
VIDEO_PINS=[
(1,'sz5N9WJS310',1195,'2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f'),
(2,'6VEfKF7BzZU',1347,'a59b2fd424011c3f572aa52404411ff4ea435f6dd1e7e27e4f5c9e11f7218b72'),
(3,'OiDTNstaSpM',785,'e94b12a1084a8b57c3b9c2a630e27f840ae5a827b3a71c62526e15380a7c57bd'),
(4,'aNfGrcO6WPI',758,'853db2d4f01ab71bbc4f86b46714f4341aa32aa2bc07416f705a937b620ea12b'),
(5,'qtluAViPpsQ',1044,'af4fb6b702c5497e5c17bc7b9a3e87855a5488dd263cded32be9a09cec67a543')]
SRT_CLOCK = re.compile(r'(\d{2}):(\d{2}):(\d{2})[,\.](\d{3})\Z')
SRT_ARROW = re.compile(r'\s*-->\s*')
_CLOSING = re.compile(r'[.!?。？！][\s\"\']*$')
_FILLER = re.compile(r'^(?:>>\s*)?(?:네|예|응|어|아|음|그죠|그렇죠|맞아요|하하|아하|그렇군요|음|웃음|감사합니다|안녕하세요)[.?!\s\[\]]*$')
_SPEAKER = re.compile(r'^\s*>>\s*')
_V37_NUMBER = re.compile(r'(?<![0-9A-Za-z])\d[0-9,.]*(?:%|세|년|개월|원|만|억)?')

@dataclass
class Cue:
    index:int
    start_ms:int
    end_ms:int
    text:str

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(data):return hashlib.sha256(data).hexdigest()
def digest(obj):return sha(json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8'))
def clock(t):
    m=SRT_CLOCK.fullmatch(t.strip()); require(m is not None, 'SRT_CLOCK_INVALID')
    hh,mm,ss,ms=map(int,m.groups());require(mm<60 and ss<60,'SRT_CLOCK_UNIT_INVALID')
    return ((hh*60+mm)*60+ss)*1000+ms

def parse_srt(raw):
    data=raw.decode('utf-8-sig',errors='strict')
    blocks=re.split(r'\n\s*\n',data.replace('\r\n','\n').replace('\r','\n').strip())
    out=[]; prev=-1
    for b in blocks:
        lines=b.split('\n'); require(len(lines)>=3 and lines[0].strip().isdecimal(),'SRT_BLOCK_INVALID')
        i=int(lines[0].strip());require(i==len(out)+1,'SRT_NONCONTIGUOUS_CUE_INDEX')
        times=SRT_ARROW.split(lines[1].strip());require(len(times)==2,'SRT_INVALID_TIME_ARROW')
        start,end=map(clock,times);require(end>=start and start>=prev,'SRT_NON_MONOTONE_TIME')
        text=' '.join(s.strip() for s in lines[2:] if s.strip());require(bool(text),'SRT_EMPTY_CUE')
        out.append(Cue(i,start,end,text));prev=start
    return out

def spans(cues,first,last,max_cues=7):
    out=[]; cur=[]
    def flush():
        nonlocal cur
        if cur:out.append(cur);cur=[]
    for i in range(first,last+1):
        t=cues[i-1].text.strip()
        if _SPEAKER.search(t) and cur:flush()
        if _FILLER.fullmatch(t) and len(t)<16:
            flush();out.append([i]);continue
        cur.append(i)
        combined=' '.join(cues[j-1].text for j in cur)
        if ((len(combined)>=5 and _CLOSING.search(t)) or len(cur)>=max_cues or len(combined)>1450):flush()
    flush();return out

def registry(cues):
    count=0;found={}
    for n,first in enumerate(range(1,len(cues)+1,40),1):
        last=min(first+39,len(cues)); rows=[]
        for idxs in spans(cues,first,last,max_cues=7):
            entire=' '.join(cues[i-1].text for i in idxs).strip()
            if len(entire)<5 or (_FILLER.fullmatch(entire) and len(entire)<16):continue
            valid=[i for i in idxs if len(cues[i-1].text.strip())>=2]
            if not valid:continue
            count+=1
            prop=' | '.join(cues[i-1].text for i in valid)
            rows.append({'claim_id':f'C{count:05d}', 'source_text_sha256':sha(prop.encode('utf-8')),'cue_indices':valid,'numeric_tokens':sum(len(_V37_NUMBER.findall(cues[i-1].text)) for i in valid)})
        found[f'W{n:05d}']=rows
    return found

def audit(zippath):
    b=Path(zippath).read_bytes();require(sha(b)==PINNED_SOURCE_ZIP,'OWNER_ZIP_MISMATCH')
    cohort=[]; vids=[]; allregs={};cuesbyvid={}; assigned_all=0; unassigned_all=0
    with zipfile.ZipFile(zippath) as z:
        for n,vid,expected,pin in VIDEO_PINS:
            hits=[x for x in z.namelist() if x.endswith(f'youtube-transcript-{vid}.srt') and not x.startswith('__MACOSX/')]
            require(len(hits)==1,'VIDEO_MEMBER_MISSING_OR_DUPLICATE')
            raw=z.read(hits[0]);require(sha(raw)==pin,'VIDEO_ORIGINAL_SHA_MISMATCH')
            cues=parse_srt(raw);require(len(cues)==expected,'ORIGINAL_CUE_COUNT_DRIFT')
            regs=registry(cues);allregs[vid]=regs;cuesbyvid[vid]=cues
            for wname,rows in regs.items():
                win=int(wname[1:]);first=(win-1)*40;last=min(first+40,len(cues))
                win_text=' '.join(c.text for c in cues[first:last])
                cohort.append([n,wname,sha(win_text.encode('utf-8')),digest(rows)])
            assigned={idx for rows in regs.values() for row in rows for idx in row['cue_indices']}
            require(all(1 <= i <= len(cues) for i in assigned),'CANDIDATE_SOURCE_OUT_OF_RANGE')
            assigned_all+=len(assigned);unassigned_all+=len(cues)-len(assigned)
            vids.append({'video_no':n,'video_id':vid,'cue_count':len(cues),'windows':len(regs),'v33_candidate_count':sum(len(a) for a in regs.values()), 'source_cues_assigned_candidate':len(assigned),'source_cues_without_candidate':len(cues)-len(assigned)})
    return {'source_zip_sha256':PINNED_SOURCE_ZIP,'v42_cohort_digest_replayed':digest(cohort),'v42_cohort_digest_matches':digest(cohort)==PINNED_V42_COHORT,'video_summaries':vids,'total_windows':len(cohort),'total_v33_candidates':sum(v['v33_candidate_count'] for v in vids),'source_cues_assigned_candidate':assigned_all,'source_cues_without_candidate':unassigned_all,'no_private_prose_published':True,'semantic_claim_fact_recall_certified':False},allregs,cuesbyvid

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('owner_zip',type=Path);a=ap.parse_args()
    rec,_,_=audit(a.owner_zip);print(json.dumps(rec,sort_keys=True,ensure_ascii=False,indent=2))
    if not rec['v42_cohort_digest_matches'] or rec['total_v33_candidates']!=1603 or rec['total_windows']!=130 or rec['source_cues_without_candidate']!=104:raise SystemExit(2)