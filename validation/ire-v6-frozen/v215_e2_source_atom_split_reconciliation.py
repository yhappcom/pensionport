"""V215 E2 source-anchored atomic split and visual-only quarantine.

Accepts ORIGINAL private SRT, prior V210 and V214 native drafts, plus a
ChatGPT reviewed, source-quoted private patch. All three files must match
externally pinned ORIGINAL byte SHA-256. No original is uploaded to GitHub.
The output is unapproved native V6; real historical V176 owner and
independent semantic gold are NOT inferred or modified.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import json

from ire.v6.atomic_exchange import NUMBER, KINDS, audit_host_atomic_exchange
from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import make_original_plan
from v210_e2_private_original_source_inventory import audit_private_e2_source_first_inventory

SCHEMA="IRE_V215_E2_REAL_SOURCE_ATOMIC_SPLIT_ADDITION_HOLD_V1"
TOP_FIELDS={
    "schema","video_id","source_sha256","v210_original_bytes_sha256",
    "v214_previous_native_bytes_sha256","replaced_parent_ids",
    "previously_blocked_source_maths_recovered_as_spoken_premises",
    "video_only_parent_ids_held","new_source_only_atomic_candidates",
    "equivalence_review_is_internal_chat_only","audio_screen_evidence_unavailable",
    "old_v176_owner_absent","independent_gold_certified",
    "financial_facts_approved","e2_final_pass","e3_e4_e5_authorized",
    "knowledge_written",
}
ROW_FIELDS={
    "source_split_id","from_v210_provisional_id","cue_indices",
    "exact_original_quotes","kind","proposition_unverified","reviewer_rationale",
    "semantic_risks","speaker_audio_verified","final_stance_certified",
    "financial_fact_approved","independent_gold_certified","e2_final_pass",
    "e3_e4_e5_authorized",
}
FALSE_ROWS=(
    "speaker_audio_verified","final_stance_certified","financial_fact_approved",
    "independent_gold_certified","e2_final_pass","e3_e4_e5_authorized",
)
FALSE_TOP=(
    "independent_gold_certified","financial_facts_approved","e2_final_pass",
    "e3_e4_e5_authorized","knowledge_written",
)


def require(test,reason):
    if not test:
        raise InvalidInput("V215_E2_"+reason)


def pinned(raw,parsed,sha,label):
    require(type(raw) is bytes and type(parsed) is dict and
            type(sha) is str and len(sha)==64,label+"_INPUT_TYPES")
    try:
        recovered=json.loads(raw)
    except (ValueError,TypeError,UnicodeError) as exc:
        raise InvalidInput("V215_E2_"+label+"_ORIGINAL_JSON_UNREADABLE") from exc
    require(type(recovered) is dict and recovered==parsed and
            sha256(raw)==sha,label+"_ORIGINAL_BYTES_TAMPERED")


def reconcile_private_native_source_splits(raw_srt,inventory,prior_exchange,
                                           patch,*,expected_source_sha256,
                                           v210_original_bytes,
                                           expected_v210_bytes_sha256,
                                           v214_original_bytes,
                                           expected_v214_bytes_sha256,
                                           patch_original_bytes,
                                           expected_patch_bytes_sha256,
                                           window_size=20):
    require(type(raw_srt) is bytes and type(expected_source_sha256) is str and
            sha256(raw_srt)==expected_source_sha256,"SOURCE_BYTES_CHANGED")
    require(type(window_size) is int and 1<=window_size<=1000,"BAD_WINDOW_SIZE")
    pinned(v210_original_bytes,inventory,expected_v210_bytes_sha256,"V210")
    audit_private_e2_source_first_inventory(
        raw_srt,inventory,expected_source_sha256=expected_source_sha256)
    pinned(v214_original_bytes,prior_exchange,expected_v214_bytes_sha256,"V214")
    pinned(patch_original_bytes,patch,expected_patch_bytes_sha256,"PATCH")
    source,_=make_original_plan(
        raw_srt,inventory["video_id"],expected_source_sha256=expected_source_sha256,
        window_size=window_size)
    audit_host_atomic_exchange(source,prior_exchange)
    require(type(patch) is dict and set(patch)==TOP_FIELDS and
            patch["schema"]==SCHEMA and
            patch["video_id"]==source.video_id and
            patch["source_sha256"]==expected_source_sha256 and
            patch["v210_original_bytes_sha256"]==expected_v210_bytes_sha256 and
            patch["v214_previous_native_bytes_sha256"]==expected_v214_bytes_sha256 and
            patch["equivalence_review_is_internal_chat_only"] is True and
            patch["audio_screen_evidence_unavailable"] is True and
            patch["old_v176_owner_absent"] is True and
            all(patch[k] is False for k in FALSE_TOP),
            "PATCH_SOURCE_OR_APPROVAL_SCHEMA")
    candidates=inventory.get("claims")
    require(type(candidates) is list and
            inventory.get("source_sha256")==source.source_sha256 and
            type(prior_exchange.get("atoms")) is list,"ORIGINAL_REVIEW_CLAIM_LIST")
    byid={c["provisional_id"]:c for c in candidates}
    require(len(byid)==len(candidates),"DUPLICATE_PRIOR_PROVISIONAL_ID")
    for field in ("replaced_parent_ids",
                  "previously_blocked_source_maths_recovered_as_spoken_premises",
                  "video_only_parent_ids_held"):
        ids=patch[field]
        require(type(ids) is list and all(type(i) is str for i in ids) and
                ids==sorted(set(ids)) and all(i in byid for i in ids),
                "BAD_PARENT_IDS_"+field)
    replaced=set(patch["replaced_parent_ids"])
    salvage=set(patch["previously_blocked_source_maths_recovered_as_spoken_premises"])
    held=set(patch["video_only_parent_ids_held"])
    require(not (replaced & salvage) and not (replaced & held) and
            not (salvage & held),"CONFLICTING_PARENT_ACTIONS")
    for pid in held:
        require(any("VISUAL" in risk for risk in byid[pid]["risks"]),
                "VISUAL_HOLD_WITHOUT_DOCUMENTED_SOURCE_RISK")
    orig_ids={a["claim_id"] for a in prior_exchange["atoms"]}
    bycode={x["provisional_id"]:f"C{i:05d}"
            for i,x in enumerate(candidates,1)}
    require(all(bycode[p] in orig_ids for p in replaced|held) and
            all(bycode[p] not in orig_ids for p in salvage),
            "REPLACED_PARENT_OR_PRIOR_BLOCKER_NOT_AS_EXPECTED")
    removed={bycode[x] for x in replaced|held}
    atoms=[dict(a) for a in prior_exchange["atoms"]
           if a["claim_id"] not in removed]
    maxid=max([int(i[1:]) for i in orig_ids]+[0])
    records=patch["new_source_only_atomic_candidates"]
    require(type(records) is list and 1<=len(records)<=1000,
            "EMPTY_OR_OVERSIZE_AMENDMENTS")
    counts=Counter()
    spoken_numbers=0
    for ordinal,entry in enumerate(records,1):
        require(type(entry) is dict and set(entry)==ROW_FIELDS,
                "SPLIT_ROW_FIELDS")
        pid=entry["from_v210_provisional_id"]
        cueids=entry["cue_indices"]
        require(entry["source_split_id"]==f"E215SRC-{ordinal:03d}" and
                type(pid) in (str,type(None)) and
                (pid is None or pid in replaced|salvage) and
                type(cueids) is list and
                all(type(i) is int for i in cueids) and
                cueids==sorted(set(cueids)) and
                1<=len(cueids)<=80 and
                all(1<=i<=len(source.cues) for i in cueids) and
                type(entry["kind"]) is str and entry["kind"] in KINDS and
                type(entry["proposition_unverified"]) is str and
                5<=len(entry["proposition_unverified"].strip())<=3000 and
                type(entry["reviewer_rationale"]) is str and
                len(entry["reviewer_rationale"].strip())>=25 and
                type(entry["semantic_risks"]) is list and
                all(type(r) is str and 4<=len(r)<=100
                    for r in entry["semantic_risks"]) and
                all(entry[k] is False for k in FALSE_ROWS),
                "SOURCE_SPLIT_ROW_INPUT_INVALID")
        if pid is not None:
            parent=byid[pid]
            # Source may complete the previous/next subtitle line, but
            # must touch the parent's original SRT range.
            require(all(max(1,parent["start_cue"]-1)<=i<=
                        min(len(source.cues),parent["end_cue"]+1)
                        for i in cueids) and
                    any(parent["start_cue"]<=i<=parent["end_cue"]
                        for i in cueids),
                    "SOURCE_SPLIT_OUTSIDE_ORIGINAL_PARENT_NEIGHBORHOOD")
            counts[pid]+=1
        quotes=entry["exact_original_quotes"]
        require(type(quotes) is list and len(quotes)==len(cueids),
                "MISSING_SOURCE_QUOTES")
        numeric=[]
        for i,q in zip(cueids,quotes):
            orig=source.cues[i-1].text
            require(type(q) is dict and set(q)=={
                "cue_index","quote","source_text_sha256"} and
                q["cue_index"]==i and q["quote"]==orig and
                q["source_text_sha256"]==sha256(orig.encode("utf-8")),
                "SOURCE_QUOTE_SHA_MISMATCH")
            numeric.extend({"cue_index":i,"token":token}
                           for token in NUMBER.findall(orig))
        spoken=Counter(n["token"] for n in numeric)
        proposed=Counter(NUMBER.findall(entry["proposition_unverified"]))
        require(all(spoken[token]>=number for token,number in proposed.items()),
                "MATH_OR_NUMBER_NOT_SPOKEN_IN_SOURCE")
        spoken_numbers+=sum(proposed.values())
        maxid+=1
        atoms.append({
            "claim_id":f"C{maxid:05d}",
            "owner_window_id":source.owner(cueids[0]),
            "proposition":entry["proposition_unverified"],
            "kind":entry["kind"],"stance":"UNRESOLVED","speaker":"UNKNOWN",
            "source_refs":[{"cue_index":cueids[0],
                            "quote":source.cues[cueids[0]-1].text}],
            "context_cue_indices":cueids,
            "condition_cue_indices":[],"exception_cue_indices":[],
            "numeric_references":numeric,"as_of":None,
        })
    require(all(counts[pid]>=2 for pid in replaced|salvage),
            "MISSING_SPLIT_CHILDREN_FOR_PARENT")
    bycue=defaultdict(list)
    for atom in atoms:
        for ref in atom["source_refs"]:
            bycue[ref["cue_index"]].append(atom["claim_id"])
    cue_rows=[]
    for cue in source.cues:
        ids=sorted(bycue[cue.index])
        cue_rows.append({
            "cue_index":cue.index,
            "cue_text_sha256":sha256(cue.text.encode("utf-8")),
            "disposition":"CANDIDATES" if ids else "UNRESOLVED",
            "claim_ids":ids,"numeric_tokens":NUMBER.findall(cue.text),
            "note":("출처 인용 원자 후보이며 금융 사실·화자 미승인" if ids
                    else "문맥 연결 및 원자 추출 완전성 미확정"),
        })
    exchange={
        "schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
        "video_id":source.video_id,"source_sha256":source.source_sha256,
        "manifest_sha256":source.manifest_sha256,
        "cue_dispositions":cue_rows,"atoms":atoms,
    }
    proof=audit_host_atomic_exchange(source,exchange)
    require(proof["proposed_atomic_claims"]==len(atoms) and
            all(a["speaker"]=="UNKNOWN" and a["stance"]=="UNRESOLVED"
                for a in atoms),"NATIVE_OR_UNAPPROVED_STATE_LOST")
    return exchange,{
        "schema":"IRE_V215_E2_REAL_ATOMIC_RECONCILIATION_PRIVATE_RECEIPT_V1",
        "source_sha256":source.source_sha256,
        "v210_file_sha256":expected_v210_bytes_sha256,
        "v214_previous_native_file_sha256":expected_v214_bytes_sha256,
        "patch_file_sha256":expected_patch_bytes_sha256,
        "original_250_source_cue_census":len(source.cues),
        "baseline_native_unapproved_atoms":len(prior_exchange["atoms"]),
        "parent_native_atoms_replaced":len(replaced),
        "visual_source_unverified_atoms_quarantined":len(held),
        "derived_math_parents_salvaged_by_spoken_split":len(salvage),
        "new_source_anchored_atomic_children":len(records),
        "native_v6_unapproved_atoms_after_reconciliation":len(atoms),
        "source_spoken_numbers_in_amendments_checked":spoken_numbers,
        "all_original_source_refs_reverified":True,
        "native_v6_structural_audit_passed":True,
        "post_reconciliation_native_atom_digest":proof["atom_candidate_digest"],
        "native_v6_unresolved_primary_cues":proof["unresolved_cues"],
        "financial_truth_gold_certified":False,
        "speaker_stance_audio_verified":False,
        "historical_v176_owner_replayed":False,
        "historical_v179_owner_atom_equivalence_complete":False,
        "independent_gold_precision_recall_measured":False,
        "e2_final_pass":False,"e3_e4_e5_authorized":False,
        "knowledge_published":False,
    }
