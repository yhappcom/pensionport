#!/usr/bin/env python3
"""Incremental, nonsemantic SRT keyword/timecode indexing (no transcript publishing).

Execute after scripts/ingest_subtitle_zip.py --apply. This never auto-approves
financial claims, and never silently revises subtitles with changed SHA-256.
"""
import argparse
import collections
import hashlib
import json
import re
import zipfile
from pathlib import Path

FILE = re.compile(r"youtube-transcript-([A-Za-z0-9_-]{11})(?:\s*\(\d+\))?\.srt$", re.I)
T = re.compile(r"^(\d{2,}):(\d\d):(\d\d)[,.](\d{3})\s*-->\s*(\d{2,}):(\d\d):(\d\d)[,.](\d{3})")
ALIASES = {
 "ETF":("ETF","상장지수펀드"), "연금저축":("연금저축","연금 저축"),
 "IRP":("IRP","개인형퇴직연금"), "ISA":("ISA","개인종합자산관리"),
 "CMA":("CMA",), "RP":("RP","환매조건부채권"),
 "MMF":("MMF",), "퇴직연금":("퇴직연금",), "세액공제":("세액공제","세액 공제"),
 "증여":("증여","증여세"), "과세":("비과세","과세","세금"),
 "자산배분":("자산배분","자산 배분"), "리밸런싱":("리밸런싱",),
 "포트폴리오":("포트폴리오",), "채권":("채권","국채","회사채"),
 "주식":("주식",), "배당":("배당","분배금"), "달러":("달러",),
 "엔화":("엔화","엔투자"), "환율":("환율",),
 "운용보수":("운용보수","총보수","수수료"), "상장폐지":("상장폐지",),
 "괴리율":("괴리율",), "추적오차":("추적오차","추적 오차"),
 "금리":("금리",), "분산투자":("분산투자","분산 투자"),
 "레버리지":("레버리지","인버스"), "손실·위험":("손실","위험","리스크"),
 "현금흐름":("현금흐름","현금 흐름"),
 "가계부·예산":("가계부","가게부","예산","지출","소비 패턴"),
 "저축·투자금":("저축","적금","월급","투자금","목돈"),
}
def stamp(seconds):
    n=int(seconds)
    return f"{n//3600:02d}:{n//60%60:02d}:{n%60:02d}"
def term_found(term,text):
    t=text.lower()
    return any((re.search(r"(?<![a-z0-9])"+re.escape(a.lower())+r"(?![a-z0-9])",t)
                if a.isascii() and a.isalnum() else a.lower() in t) for a in ALIASES[term])
def cues(raw):
    s=raw.decode("utf-8-sig").replace("\r\n","\n").replace("\r","\n")
    out=[]
    for block in re.split(r"\n\s*\n",s.strip()):
        lines=block.splitlines()
        offset=int(bool(lines and lines[0].strip().isdigit()))
        if len(lines)<offset+2:
            raise ValueError("short SRT block")
        m=T.match(lines[offset])
        if not m: raise ValueError("bad timecode")
        hh,mm,ss,ms=map(int,m.groups()[:4])
        start=hh*3600+mm*60+ss+ms/1000
        text=" ".join(lines[offset+1:]).strip()
        if not text or (out and start<out[-1][0]):
            raise ValueError("empty text/out of sequence")
        out.append((start,text))
    if not out:raise ValueError("SRT empty")
    return out
def sources(paths):
    groups=collections.defaultdict(list)
    for path in paths:
        if path.suffix.lower()==".srt":
            m=FILE.fullmatch(path.name)
            if m:groups[m.group(1)].append(path.read_bytes())
        elif path.suffix.lower()==".zip":
            with zipfile.ZipFile(path) as z:
                for entry in z.infolist():
                    name=entry.filename
                    if entry.is_dir() or name.startswith("__MACOSX/") or not name.lower().endswith(".srt"):
                        continue
                    m=FILE.fullmatch(name.rsplit("/",1)[-1])
                    if m and entry.file_size<25_000_000:
                        groups[m.group(1)].append(z.read(entry))
        else:raise ValueError("Pass only ZIP or SRT")
    return groups
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive",type=Path,action="append",required=True)
    p.add_argument("--registry",type=Path,required=True)
    p.add_argument("--index",type=Path,required=True)
    p.add_argument("--apply",action="store_true",help="write after preview; default dry run")
    a=p.parse_args()
    r=json.loads(a.registry.read_text(encoding="utf-8"))["items"]
    ix=json.loads(a.index.read_text(encoding="utf-8"))
    found=sources(a.archive)
    summary=collections.Counter()
    for vid,versions in found.items():
        unique={hashlib.sha256(raw).hexdigest() for raw in versions}
        if len(unique)!=1:
            summary["CONFLICT_IN_BATCH"]+=1;continue
        h=next(iter(unique))
        if vid not in r or r[vid]["sha256"]!=h:
            summary["OUTSIDE_REGISTRY_OR_CHANGED_SHA"]+=1;continue
        if vid in ix["items"]:
            summary["UNCHANGED" if ix["items"][vid]["subtitle_sha256"]==h else "REVISED_REVIEW"]+=1
            continue
        parsed=cues(versions[0])
        if len(parsed)!=r[vid]["cue_count"]:
            summary["SRT_COUNT_MISMATCH"]+=1;continue
        counts=collections.Counter()
        moments=collections.defaultdict(list)
        for t,body in parsed:
            for label in ALIASES:
                if term_found(label,body):
                    counts[label]+=1
                    moments[label].append(t)
        anchors=[]
        for label,_ in counts.most_common(8):
            for t in moments[label]:
                if all(abs(t-prev["seconds"])>=min(90,parsed[-1][0]*0.15) for prev in anchors):
                    anchors.append({"term":label,"timecode":stamp(t),"seconds":t})
                    break
            if len(anchors)>=4:break
        ix["items"][vid]={
            "roster_no":r[vid]["roster_no"],"subtitle_sha256":h,
            "cue_count":len(parsed),
            "timecoded_keyword_anchors":[{"term":o["term"],"timecode":o["timecode"]} for o in anchors],
            "analysis_status":"NOT_ANALYZED","verification_status":"NOT_VERIFIED"
        }
        summary["NEW_INDEX"]+=1
    print(json.dumps(dict(summary),ensure_ascii=False))
    if a.apply:
        ix["items"]=dict(sorted(ix["items"].items(),key=lambda p:p[1]["roster_no"]))
        ix["indexed_count"]=len(ix["items"])
        ix["total_anchors"]=sum(len(v["timecoded_keyword_anchors"]) for v in ix["items"].values())
        a.index.write_text(json.dumps(ix,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print("Index updated. Manually review and commit before updating registry content_stage.")
if __name__=="__main__":main()
