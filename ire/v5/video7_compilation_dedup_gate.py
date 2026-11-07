"""#7 compilation dedupe against all 101 SRT members of owner's 1-100.zip.

The default CI case verifies the immutable source-derived research receipt.
With --source-zip the exact normalized 940 matching cues, source SRT SHA,
83.1%-segment shingle overlap and the 596 V5 window rollup are independently
replayed from the private original archive. Do NOT treat 80% unmatched as novel.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from .first_five_window_review_gate import source_windows
from .first_five_remnant_221_gate import cue_txt

LEDGER=Path("ire/v5/validation/video7_compilation_archive101_exact_reprint_20261107.json")
PIN="a4a197c588d7a23d2387e83fb24f7c139a21b542"
VIDEO_ID="4CQ4FjGT2gA"
REPRINT_ID="i32DeJPzsfE"
ARCHIVE_SHA="088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716"
VIDEO_SHA="70a4fab14f26618780fa1fc9b1473df829c851d06125ae3745ecc3b6eadc79ca"
REPRINT_SHA="5f9574fc4136c77436be7dbc2dfd90086154e3f24161770866bc9e39d5ba42b9"
VIDEO_WINDOW_SHA="b1ae3adfcb4aab9c77875c4f66afc5d1f9e6431355dcbec9ff37baac3874b575"
REPRINT_MEMBER=f"1-100/youtube-transcript-{REPRINT_ID}.srt"

class CompilationError(ValueError):pass

def check(ok,label):
    if not ok:raise CompilationError(label)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def gitblob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

def norm(s):
    return re.sub(r"[^0-9a-z가-힣]+","",s.casefold())

def rollup(w):
    return sha("".join(
        x["window_id"]+":"+x["primary_text_sha256"]+"\n" for x in w
        ).encode())

def load(root):
    raw=(Path(root)/LEDGER).read_bytes()
    check(gitblob(raw)==PIN,"COMP7_REVIEWED_REPRINT_MANIFEST_CHANGED")
    return json.loads(raw)

def audit(root,source_zip=None):
    root=Path(root)
    d=load(root)
    require=[
       d.get("schema")=="IRE_V5_VIDEO7_ORIGINAL_ARCHIVE_101_FILES_REPRINT_FINGERPRINT_V1",
       d.get("as_of")=="2026-11-07",
       d.get("zip_sha256")==ARCHIVE_SHA,
       d.get("video_id")==VIDEO_ID,
       d.get("original_video_number")==7,
       d.get("original_srt_sha256")==VIDEO_SHA,
       d.get("source_cues")==10728,
       d.get("source_v5_windows")==596,
       d.get("compared_srt_files_in_zip_including_target")==101,
       d.get("comparison_sources_excluding_target")==100,
       d.get("minimum_normalized_cue_characters")==12,
       d.get("matched_video_ids")==[REPRINT_ID],
       d.get("matched_original_file")==REPRINT_MEMBER,
       d.get("matched_original_srt_sha256")==REPRINT_SHA,
       d.get("matched_original_source_cues")==1976,
       d.get("exact_reprinted_cues_unique")==940,
       d.get("exact_reprinted_target_first_cue")==14,
       d.get("exact_reprinted_target_last_cue")==1973,
       d.get("exact_match_cues_in_target_after_1973")==0,
       d.get("preexisting_video_consecutive_reprint_segment")==[14,1975],
       d.get("reprint_segment_is_precise_audio_identity_proof") is False,
       d.get("first_1973_cues_15_char_distinct_shingles_total")==22085,
       d.get("first_1973_cues_15_char_distinct_shingles_shared")==18352,
       d.get("first_1973_cues_shingle_coverage_pct")==83.1,
       d.get("all_10728_cues_proven_distinct") is False,
       d.get("unmatched_portion_proven_new") is False,
       d.get("all_other_791_videos_searched") is False,
       d.get("video7_eligible_as_independent_blind_holdout") is False,
       d.get("video7_eligible_for_new_unique_knowledge_auto_approval") is False,
       d.get("all_original_audio_rechecked") is False,
       d.get("private_original_corpus_uploaded_to_github") is False,
       d.get("source_window_rollup_sha256")==VIDEO_WINDOW_SHA,
       d.get("strict_dedupe_release")==
         "EXACT_TEXT_EVIDENCE_OF_ONE_REPRINT_SEGMENT_ONLY_NOT_FULL_COMPILATION_DUPLICATE_RESOLUTION",
    ]
    check(all(require),"COMP7_FORGED_INDEPENDENT_HOLDOUT_OR_EVIDENCE_COUNT")
    prev=json.loads((root/"ire/v5/validation/first_ten_original_crossvalidation_20261106.json").read_text("utf-8"))
    vid=prev["video_records"][6]
    check(vid["video_id"]==VIDEO_ID and vid["source_sha256"]==VIDEO_SHA
          and vid["windows"]==596 and vid["cues"]==10728
          and vid["window_hash_rollup_sha256"]==VIDEO_WINDOW_SHA,
          "COMP7_PREVIOUS_V5_ORIGINAL_SOURCE_MISMATCH")
    replayed=False
    if source_zip is not None:
        path=Path(source_zip)
        check(path.is_file(),"COMP7_PRIVATE_SOURCE_ZIP_MISSING")
        check(sha(path.read_bytes())==ARCHIVE_SHA,
              "COMP7_WRONG_PRIVATE_ARCHIVE")
        with zipfile.ZipFile(path) as z:
            files=[p for p in z.namelist()
                  if p.startswith("1-100/youtube-transcript-")
                  and p.endswith(".srt")]
            target=f"1-100/youtube-transcript-{VIDEO_ID}.srt"
            check(len(files)==101 and files.count(target)==1
                  and files.count(REPRINT_MEMBER)==1,
                  "COMP7_ARCHIVE_MEMBERS_NOT_REPRODUCIBLE")
            raw=z.read(target);other=z.read(REPRINT_MEMBER)
            check(sha(raw)==VIDEO_SHA and sha(other)==REPRINT_SHA,
                  "COMP7_ORIGINAL_SRT_BYTES_CHANGED")
            cues=cue_txt(raw)
            windows=source_windows(raw)
            check(len(cues)==10728 and len(windows)==596
                  and rollup(windows)==VIDEO_WINDOW_SHA,
                  "COMP7_V5_WINDOWS_OR_CUES_NOT_REPLAYED")
            all_norm={}
            for file in files:
                if file==target:continue
                for txt in cue_txt(z.read(file)):
                    n=norm(txt)
                    if len(n)>=12:
                        all_norm.setdefault(n,set()).add(file)
            exact=[i+1 for i,txt in enumerate(cues)
                   if len(norm(txt))>=12 and norm(txt) in all_norm]
            hit_sources={s for i in exact for s in all_norm[norm(cues[i-1])]}
            check(len(exact)==940 and min(exact)==14
                  and max(exact)==1973 and
                  hit_sources=={REPRINT_MEMBER},
                  "COMP7_ORIGINAL_EXACT_REPRINT_COUNT_CHANGED")
            a="".join(norm(t) for t in cue_txt(other))
            b="".join(norm(t) for t in cues[:1973])
            needle=15
            sa={a[j:j+needle] for j in range(len(a)-needle+1)}
            sb={b[j:j+needle] for j in range(len(b)-needle+1)}
            check(len(sa&sb)==18352 and len(sb)==22085,
                  "COMP7_ORIGINAL_FIRST_SEGMENT_OVERLAP_CHANGED")
        replayed=True
    return {
      "schema":"IRE_V5_VIDEO7_COMPILATION_DEDUP_SOURCE_RECEIPT_V1",
      "compilation_cues":10728,
      "compilation_v5_windows":596,
      "owner_archive_srt_files_compared":101,
      "known_independent_original_video_id":REPRINT_ID,
      "known_exact_cue_reprints":940,
      "known_reprint_first_to_last_cue":[14,1973],
      "15_character_shingle_shared_in_first1973":18352,
      "15_character_shingle_total_in_first1973":22085,
      "private_archive_replayed_in_this_process":replayed,
      "exact_dedup_certified_only_when_private_source_replayed":replayed,
      "rest_of_compilation_is_proven_novel":False,
      "video7_is_independent_holdout":False,
      "video7_auto_promoted_unique_financial_facts":0,
      "release":"ONE_PROVEN_REPRINT_REGION_OTHERS_REQUIRE_COMPARISON",
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--source-zip",type=Path)
    a=p.parse_args()
    print(json.dumps(audit(a.root,a.source_zip),ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
