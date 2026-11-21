"""V215.1 E2 private native V6 all-pair lexical triage, NOT semantic dedup.

Bounded exact source/native bytes -> frozen V6 audit -> all pairwise lexical
scoring. No external model API and no automatic atom merges. Comparisons
are retrieval candidates for a real ChatGPT semantic adjudication only;
cosine similarity cannot certify equality or independent recall/gold.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import json
from math import log,sqrt

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from v176_chat_engine_loop import make_original_plan


def require(ok,code):
    if not ok:
        raise InvalidInput("V2151_E2_"+code)


def char_ngrams(s):
    s=" ".join(s.casefold().split())
    c=Counter()
    for size in (2,3,4):
        for i in range(max(0,len(s)-size+1)):
            c[s[i:i+size]]+=1
    return c


def source_only_native_pairwise_screen(raw_srt,exchange,original_exchange_bytes,*,
                                      expected_source_sha256,
                                      expected_exchange_sha256,
                                      window_size=20,
                                      top_n=30,threshold_basis_points=2000):
    require(type(raw_srt) is bytes and type(expected_source_sha256) is str and
            sha256(raw_srt)==expected_source_sha256,"SOURCE_BYTES_CHANGED")
    require(type(original_exchange_bytes) is bytes and
            type(exchange) is dict and
            type(expected_exchange_sha256) is str and
            sha256(original_exchange_bytes)==expected_exchange_sha256,
            "PRIVATE_NATIVE_BYTES_OR_HASH_NOT_PINNED")
    try:
        saved=json.loads(original_exchange_bytes)
    except (ValueError,UnicodeError,TypeError) as exc:
        raise InvalidInput("V2151_E2_NATIVE_JSON_UNREADABLE") from exc
    require(saved==exchange and
            type(window_size) is int and 1<=window_size<=1000 and
            type(top_n) is int and 1<=top_n<=100 and
            type(threshold_basis_points) is int and
            0<=threshold_basis_points<=10000,
            "SOURCE_NATIVE_ARGS_MISMATCH")
    source,_=make_original_plan(
        raw_srt,exchange["video_id"],
        expected_source_sha256=expected_source_sha256,
        window_size=window_size)
    audit_host_atomic_exchange(source,exchange)
    atoms=exchange["atoms"]
    # Safety: quadratic comparisons are bounded; larger videos must be
    # sharded by provenance and checked independently to avoid RunFail.
    require(2<=len(atoms)<=512,"PAIRWISE_VIDEO_TOO_LARGE_SHARD_REQUIRED")
    require(all(a["speaker"]=="UNKNOWN" and a["stance"]=="UNRESOLVED"
                for a in atoms),"SOURCE_SPEAKER_PREMATURELY_CERTIFIED")
    vectors=[char_ngrams(x["proposition"]) for x in atoms]
    df=Counter()
    for v in vectors:
        df.update(set(v))
    n=len(atoms)
    weights=[]
    for c in vectors:
        v={key:(1+log(tf))*(1+log((n+1)/(df[key]+1)))
           for key,tf in c.items()}
        norm=sqrt(sum(value**2 for value in v.values())) or 1
        weights.append({key:value/norm for key,value in v.items()})
    candidates=[]
    above=0
    all_pairs=0
    exact_same_proposition=0
    for i in range(n):
        for j in range(i+1,n):
            all_pairs+=1
            a,b=weights[i],weights[j]
            if len(a)>len(b):
                a,b=b,a
            score=sum(value*b.get(key,0) for key,value in a.items())
            score_bps=min(10000,max(0,round(10000*score)))
            above+=int(score_bps>=threshold_basis_points)
            exact_same_proposition+=int(
                atoms[i]["proposition"]==atoms[j]["proposition"])
            candidates.append({
                "a":atoms[i]["claim_id"],"b":atoms[j]["claim_id"],
                "lexical_similarity_basis_points":score_bps,
                "source_overlap":bool(
                    set(atoms[i]["context_cue_indices"])&
                    set(atoms[j]["context_cue_indices"])),
                "semantic_equivalence_verified":False,
                "automatic_merge_authorized":False,
            })
    candidates.sort(
        key=lambda x:(-x["lexical_similarity_basis_points"],x["a"],x["b"]))
    return {
        "schema":"IRE_V215_1_E2_PRIVATE_LEXICAL_PAIR_SCREEN_RECEIPT_V1",
        "source_sha256":expected_source_sha256,
        "native_original_bytes_sha256":expected_exchange_sha256,
        "native_unapproved_atoms":n,
        "native_pairwise_pairs_lexically_screened":all_pairs,
        "pairs_at_or_above_threshold":above,
        "threshold_basis_points":threshold_basis_points,
        "exact_same_text_pair_count":exact_same_proposition,
        "top_pairs_for_chat_meaning_review":candidates[:top_n],
        "all_pairs_source_semantically_verified":False,
        "lexical_similarity_does_not_imply_equivalence":True,
        "automatic_atom_merges":0,
        "independent_gold_certified":False,
        "speaker_stance_audio_verified":False,
        "e2_final_pass":False,
        "e3_e4_e5_authorized":False,
        "knowledge_published":False,
    }
