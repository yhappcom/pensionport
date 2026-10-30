#!/usr/bin/env python3
"""Privacy-preserving video #1 raw SRT rehash and 23 core-span digest verifier.

In public CI, checks only provenance schema and historical crossrefs.
In trusted private runtime, pass --zip-path to prove actual raw SRT bytes match.
Never uploads/prints/stores raw subtitle content.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
RECORD="v5/research_progress/v5_001_private_srt_core_span_provenance_20261030.json"
GOLD="data/synthesis/investment_knowledge_v4/reviews/v4_001_gold_pilot_manifest_20261029.json"
V5="v5/retrofit/v5_001_sz5N9WJS310_bounded_closeout.json"
ZIP_MEMBER="1-100/youtube-transcript-sz5N9WJS310.srt"
ID="sz5N9WJS310"
SHA=re.compile("^[a-f0-9]{64}$")
SRT=re.compile(r"(?m)^(\d+)\s*\n((?:\d\d:){2}\d\d,\d+\s*-->[^\n]*)\n([\s\S]*?)(?=\n\s*\n|\Z)")

def need(x,msg):
    if not x: raise ValueError(msg)
def read(p):return json.loads(p.read_text(encoding="utf-8"))
def blockhash(cues,first,last):
    return hashlib.sha256("\n".join(
        str(i)+"|"+cues[i][0]+"|"+cues[i][1]
        for i in range(first,last+1)
    ).encode("utf-8")).hexdigest()

def validate(record,gold,v5,zip_path=None):
    need(record["schema"]=="V5_001_PRIVATE_SRT_CORE_SPAN_PROVENANCE_1.0"
         and record["video_id"]==gold["video_id"]==v5["video_id"]==ID,
         "source audit identity")
    need(record["source_zip_held_privately"] is True and
         record["source_path_reference"]==ZIP_MEMBER and
         record["raw_srt_text_or_zip_in_github"] is False and
         record["github_ci_rehashes_original_srt"] is False,
         "no raw SRT allowed on GitHub")
    need(record["whole_video_cues_semantically_reviewed_in_this_cycle"] is False
         and record["full_atom_42_statement_text_recovered"] is False
         and record["final_research_status"]=="RESEARCH_BLOCKED",
         "unearned comprehensive source approval")
    source_sha=record["raw_srt_sha256_recomputed_in_private_runtime"]
    need(source_sha==gold["source_srt_sha256"]==v5["source"]["source_sha256"]
         and SHA.fullmatch(source_sha) and
         record["raw_srt_byte_size"]==92252 and
         record["raw_srt_cue_count"]==1195,
         "historical source hash or size changed")
    a=record["core_claim_spans"]
    overlays={x["claim_id"]:x["source_cue_range"] for x in gold["claim_overlays"]}
    need(len(a)==record["core_claim_span_count"]==len(overlays)==23
         and len({x["claim_id"] for x in a})==23
         and {x["claim_id"] for x in a}==set(overlays),
         "all 23 core spans must have entries")
    covered=set()
    for row in a:
        lo,hi=row["first_cue"],row["last_cue"]
        need([lo,hi]==overlays[row["claim_id"]] and
             1<=lo<=hi<=1195 and SHA.fullmatch(row["span_sha256"]),
             "wrong claim cue span or digest")
        need(row["verification_level"]==
             ("DIRECT_SELECTED_CONTEXT_REVIEW" if row["claim_id"] in
              {ID+"-06",ID+"-15"} else "EXACT_BYTE_RANGE_HASH_ONLY"),
             "source review scope overstated")
        need(row["source_exact_statement_semantics_certified"] is False,
             "atomic semantics falsely certified")
        covered.update(range(lo,hi+1))
    need(len(covered)==record["unique_cues_in_core_spans"]==591,
         "source range denominator")
    result={"video_number":1,"original_raw_source_rehashed_in_this_execution":False,
            "original_byte_count_grounded_historically":92252,
            "core_spans_recorded":23,"unique_cues_in_spans":591,
            "42_original_atomic_wordings_verified":False,
            "completion":"RESEARCH_BLOCKED"}
    if zip_path is not None:
        with ZipFile(zip_path) as z:
            need(ZIP_MEMBER in z.namelist(),"source ZIP member missing")
            raw=z.read(ZIP_MEMBER)
        need(len(raw)==92252 and hashlib.sha256(raw).hexdigest()==source_sha,
             "current raw file does not match original #1 SRT")
        text=raw.decode("utf-8-sig")
        triples=SRT.findall(text)
        cues={int(n):(timing,text.strip()) for n,timing,text in triples}
        need(len(triples)==len(cues)==1195 and set(cues)==set(range(1,1196)),
             "1195 sequential subtitle blocks not present")
        for row in a:
            actual=blockhash(cues,row["first_cue"],row["last_cue"])
            need(actual==row["span_sha256"],
                 "raw private SRT cue hash mismatch: "+row["claim_id"])
        result.update(original_raw_source_rehashed_in_this_execution=True,
                      raw_cue_sequence_verified=True,private_23_spans_rehashed=23)
    return result

def selftest(record,gold,v5):
    invalid=[]
    x=copy.deepcopy(record);x["core_claim_spans"].pop();invalid.append(x)
    x=copy.deepcopy(record);x["core_claim_spans"][0]["first_cue"]+=1;invalid.append(x)
    x=copy.deepcopy(record);x["core_claim_spans"][0]["span_sha256"]="broken";invalid.append(x)
    x=copy.deepcopy(record);x["full_atom_42_statement_text_recovered"]=True;invalid.append(x)
    x=copy.deepcopy(record);x["github_ci_rehashes_original_srt"]=True;invalid.append(x)
    x=copy.deepcopy(record);x["raw_srt_sha256_recomputed_in_private_runtime"]="0"*64;invalid.append(x)
    x=copy.deepcopy(record);x["whole_video_cues_semantically_reviewed_in_this_cycle"]=True;invalid.append(x)
    x=copy.deepcopy(record);x["core_claim_spans"][0]["source_exact_statement_semantics_certified"]=True;invalid.append(x)
    for i,x in enumerate(invalid):
        try:validate(x,gold,v5)
        except (ValueError, KeyError, TypeError):continue
        raise ValueError("source audit mutation accepted: "+str(i))
    return {"negative_mutations_rejected":len(invalid)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--zip-path",type=Path)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    root=args.root.resolve()
    rec,gold,v5=[read(root/path) for path in (RECORD,GOLD,V5)]
    result=validate(rec,gold,v5,args.zip_path)
    if args.self_test:result["tests"]=selftest(rec,gold,v5)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))

if __name__=="__main__":
    try:main()
    except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
