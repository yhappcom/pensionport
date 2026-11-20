"""V220 E2 bounded source-only quality evidence and explicit non-pass diagnoses.

This module does NOT invent independent gold, original audio, video, speakers,
financial truth or historical SQLite. No method here can authorize V123/E3/E4/E5.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256 as _sha256
from fractions import Fraction
from typing import Any

try:
    from ire.v6.errors import InvalidInput
    from ire.v6.source import parse_srt
except ImportError:  # avoid hiding missing frozen package in real CI
    raise


def _require(yes: bool, code: str) -> None:
    if not yes:
        raise InvalidInput("V220_E2_" + code)


def _hash(raw: bytes) -> str:
    return _sha256(raw).hexdigest()


def _uint(value: Any) -> bool:
    return type(value) is int and value >= 0


def _list(x: Any, limit: int) -> bool:
    return type(x) is list and len(x) <= limit


def diagnose_e2_proof_gaps(v219_receipt: dict, census: dict,
                            finance: dict, native: dict) -> dict:
    """Real observed blockers, separated by *semantic* and *lineage* domains.

    A 391/391 code-only CI score never becomes a semantic quality score.
    Input is the output of the independently run frozen V219 source audit.
    """
    _require(all(type(x) is dict for x in (v219_receipt,census,finance,native)), "INPUT_TYPES")
    _require(v219_receipt.get("schema")=="IRE_V219_E2_INTEGRATED_REAL_SOURCE_AND_UNAPPROVED_CLAIM_CUSTODY_V1", "RECEIPT_SCHEMA")
    _require(v219_receipt.get("e2_final_pass") is False and
             v219_receipt.get("financial_facts_approved") is False and
             v219_receipt.get("knowledge_published") is False, "FALSE_FINAL_APPROVAL")
    rows=census.get("rows");atoms=native.get("atoms");risks=finance.get("atoms")
    _require(_list(rows,2000) and _list(atoms,512) and _list(risks,512), "ROWS_MALFORMED")
    n=v219_receipt.get("original_cues_verified")
    _require(_uint(n) and 1<=n<=2000 and len(rows)==n and
             _uint(v219_receipt.get("native_unapproved_atoms")) and
             len(atoms)==v219_receipt["native_unapproved_atoms"] and
             len(risks)==len(atoms), "SOURCE_COUNTS_DRIFT")
    expected_sha=v219_receipt.get("original_source_sha256")
    _require(type(expected_sha) is str and len(expected_sha)==64 and
             census.get("original_source_sha256")==expected_sha and
             native.get("source_sha256")==expected_sha and
             finance.get("source_sha256")==expected_sha, "SOURCE_SHA_MISMATCH")
    ids=set();unverified_speakers=0;unverified_stances=0
    for a in atoms:
        _require(type(a) is dict and type(a.get("claim_id")) is str and
                 bool(a["claim_id"]) and a["claim_id"] not in ids and
                 type(a.get("source_refs")) is list, "INVALID_ATOM")
        ids.add(a["claim_id"])
        unverified_speakers+=int(a.get("speaker")=="UNKNOWN")
        unverified_stances+=int(a.get("stance")=="UNRESOLVED")
        _require(a.get("speaker")=="UNKNOWN" and a.get("stance")=="UNRESOLVED", "UNTRUSTED_SPEAKER_PROMOTION")
    tags=set();risk_count=0
    for item in risks:
        _require(type(item) is dict and type(item.get("claim_id")) is str and
                 _list(item.get("risk_tags"),64) and
                 item.get("financial_truth_certified") is False and
                 item.get("claim_approved") is False, "RISKS_MALFORMED_OR_APPROVED")
        tags.add(item["claim_id"])
        risk_count+=int(len(item["risk_tags"])>0)
    _require(tags==ids and risk_count==v219_receipt.get("source_risk_tagged_native_atoms"), "RISK_COUNT_DRIFT")
    classes=Counter();risk_cues=0;unresolved_rows=[]
    for k,r in enumerate(rows,1):
        _require(type(r) is dict and r.get("cue_index")==k and
                 type(r.get("classification")) is str and
                 type(r.get("independent_omission_review_complete")) is bool and
                 r.get("independent_omission_review_complete") is False and
                 type(r.get("original_audio_or_screen_review_required")) is bool,
                 "INCOMPLETE_CUE_CUSTODY")
        classes[r["classification"]]+=1
        if r["original_audio_or_screen_review_required"]:risk_cues+=1
        if r["classification"]=="MEDIA_DEPENDENT_UNMAPPED_QUARANTINE":unresolved_rows.append(k)
    _require(sum(classes.values())==n and
             classes==Counter(v219_receipt.get("all_cue_review_state_counts",{})) and
             risk_cues==v219_receipt.get("cues_flagged_audio_or_video_or_screen") and
             v219_receipt.get("historical_v176_owner_sqlite_recovered") is False and
             v219_receipt.get("separate_blind_independent_gold_measured") is False,
             "RECEIPT_CUE_CENSUS_MISMATCH")
    current_v182=v219_receipt.get("historical_v182_source_open_cases_unresolved")
    _require(_uint(current_v182), "HISTORICAL_OPEN_COUNT")
    return {
      "schema":"IRE_V220_E2_EXPLICIT_PROOF_READINESS_V1",
      "source_sha256":expected_sha, "native_count":len(atoms),"original_cues":n,
      "source_disposition_counts":dict(classes),"media_cue_indices":unresolved_rows,
      "audio_screen_risk_cues":risk_cues,"unverified_speaker_atoms":unverified_speakers,
      "unresolved_stance_atoms":unverified_stances,
      "financial_meaning_risk_atoms":risk_count,
      "semantic_core_blockers":[
        {"code":"INDEPENDENT_SOURCE_BLIND_GOLD_MISSING","required_evidence":"frozen source-only gold, independently reviewed one-to-one adjudication and confusion matrix","count":None},
        {"code":"SPEAKER_AND_STANCE_UNVERIFIED","required_evidence":"utterance-level verified speaker/stance or explicit scope exclusion","count":unverified_speakers},
        {"code":"AUDIOVISUAL_RISK_UNVERIFIED","required_evidence":"original audio/frames or non-published explicit quarantine for each affected assertion","count":risk_cues},
        {"code":"MEDIA_ASSERTION_NOT_RETAINED_AS_ATOM","required_evidence":"source-quoted unapproved sub-claims held outside approved native atom path","count":len(unresolved_rows)},
        {"code":"FINANCIAL_RISK_NOT_RESOLVED","required_evidence":"current official finance evidence and source-claim separation","count":risk_count}],
      "separate_historical_lineage_blockers":[
        {"code":"V176_OWNER_SQLITE_MISSING","required_evidence":"genuine owner event chain or formally quarantined legacy migration","count":None},
        {"code":"V182_OPEN_NOT_CLOSED","required_evidence":"17 source-first risks must remain OPEN until evidence verified","count":current_v182}],
      "e2_semantic_quality_status":"HOLD_EVIDENCE_MISSING",
      "e2_source_integrity_status":"PASS_ONLY_AS_PRIOR_V219_RECEIPT",
      "e2_final_pass":False,"e3_e4_e5_authorized":False,
      "historical_owner_required_for_new_video_gold_measurement":False,
      "historical_owner_required_for_legacy_knowledge_merge":True,
      "valid_independent_precision_recall_measured":False,
      "research_knowledge_published":False}


def assess_claim_precision_recall(gold: dict, native: dict, adjudications: dict,
                                  *, expected_source_sha256: str) -> dict:
    """Compute *conditional* quality figures, NEVER certify reviewer independence.

    Gold must have been authored from original-source only. The supplied
    matching judgments must have source overlap; PARTIAL is NOT a TP.
    A tool/user self-assertion of 'independent' is not a cryptographic attestation.
    """
    _require(all(type(x) is dict for x in (gold,native,adjudications)) and
             type(expected_source_sha256) is str and len(expected_source_sha256)==64,
             "GOLD_INPUT_TYPES")
    _require(gold.get("schema")=="IRE_V220_SOURCE_ONLY_GOLD_DRAFT_V1" and
             gold.get("source_sha256")==expected_source_sha256 and
             native.get("source_sha256")==expected_source_sha256 and
             adjudications.get("source_sha256")==expected_source_sha256,
             "GOLD_SOURCE_MISMATCH")
    gitems=gold.get("claims");nitems=native.get("atoms");matches=adjudications.get("pairs")
    _require(_list(gitems,1000) and _list(nitems,512) and _list(matches,1500) and
             len(gitems)>0 and len(nitems)>0, "GOLD_EMPTY_OR_TOO_LARGE")
    gs={};ns={}
    for g in gitems:
        _require(type(g) is dict and type(g.get("gold_id")) is str and
                 g["gold_id"] not in gs and
                 _list(g.get("cue_indices"),150) and bool(g["cue_indices"]) and
                 all(type(i) is int and 1<=i<=2000 for i in g["cue_indices"]) and
                 type(g.get("high_risk")) is bool and
                 type(g.get("kind")) is str, "INVALID_GOLD_ITEM")
        gs[g["gold_id"]]=g
    for n in nitems:
        _require(type(n) is dict and type(n.get("claim_id")) is str and
                 n["claim_id"] not in ns and
                 _list(n.get("source_refs"),150) and bool(n["source_refs"]) and
                 all(type(q) is dict and type(q.get("cue_index")) is int and
                     1<=q["cue_index"]<=2000 for q in n["source_refs"]),
                 "INVALID_NATIVE_FOR_GOLD")
        ns[n["claim_id"]]=n
    true_pairs=[];used_g=set();used_n=set();seen=set()
    for p in matches:
        _require(type(p) is dict and type(p.get("gold_id")) is str and
                 type(p.get("claim_id")) is str and
                 p["gold_id"] in gs and p["claim_id"] in ns and
                 p.get("verdict") in ("EQUIVALENT","PARTIAL","DISAGREE") and
                 (p["gold_id"],p["claim_id"]) not in seen,
                 "ADJUDICATION_INVALID_OR_DUPLICATED")
        seen.add((p["gold_id"],p["claim_id"]))
        if p["verdict"]!="EQUIVALENT":continue
        _require(p["gold_id"] not in used_g and p["claim_id"] not in used_n and
                 set(gs[p["gold_id"]]["cue_indices"]) &
                 {q["cue_index"] for q in ns[p["claim_id"]]["source_refs"]},
                 "DUPLICATE_OR_UNSOURCED_EQUIVALENCE")
        used_g.add(p["gold_id"]);used_n.add(p["claim_id"]);true_pairs.append((p["gold_id"],p["claim_id"]))
    tp=len(true_pairs);fp=len(ns)-tp;fn=len(gs)-tp
    high_risk_missed=sorted(gid for gid,g in gs.items() if g["high_risk"] and gid not in used_g)
    prec=Fraction(tp,len(ns));rec=Fraction(tp,len(gs))
    threshold=prec>=Fraction(95,100) and rec>=Fraction(98,100) and not high_risk_missed
    return {"schema":"IRE_V220_E2_UNCERTIFIED_PRECISION_RECALL_MEASUREMENT_V1",
        "source_sha256":expected_source_sha256,"gold_claims":len(gs),"native_claims":len(ns),
        "true_positives":tp,"false_positives":fp,"false_negatives":fn,
        "precision_numerator":tp,"precision_denominator":len(ns),
        "recall_numerator":tp,"recall_denominator":len(gs),
        "precision_pct":round(100*float(prec),4),"recall_pct":round(100*float(rec),4),
        "missed_high_risk_gold_ids":high_risk_missed,
        "numerical_thresholds_met_on_supplied_annotations":threshold,
        "source_claim_equivalence_independently_validated":False,
        "independent_gold_provenance_certified":False,
        "measured_scores_do_not_imply_e2_approval":True,
        "e2_final_pass":False,"e3_e4_e5_authorized":False,
        "status":"MEASURED_UNCERTIFIED_REQUIRES_BLIND_INDEPENDENCE_AND_CHATGPT_FINAL_GATE"}


def audit_media_claim_quarantine(census: dict, packet: dict, *,
                                raw_original_srt: bytes,
                                expected_source_sha256: str) -> dict:
    """Require every previously unmapped audiovisual cue be retained in a source-only claim packet."""
    _require(type(census) is dict and type(packet) is dict and
             census.get("original_source_sha256")==expected_source_sha256 and
             packet.get("source_sha256")==expected_source_sha256 and
             packet.get("schema")=="IRE_V220_E2_UNAPPROVED_MEDIA_SPEECH_DOCKET_V1",
             "MEDIA_PACKET_SOURCE_INVALID")
    _require(type(raw_original_srt) is bytes and
             _hash(raw_original_srt)==expected_source_sha256,
             "ORIGINAL_SRT_BYTES_CHANGED")
    original_cues=parse_srt(raw_original_srt)
    rows=census.get("rows");items=packet.get("unapproved_speech_claims")
    _require(_list(rows,2000) and _list(items,100) and len(items)>0 and
             len(rows)==len(original_cues), "MEDIA_PACKET_INPUTS")
    bycue={};expected=set()
    for row in rows:
        _require(type(row) is dict and type(row.get("cue_index")) is int and
                 type(row.get("source_quote")) is str, "MEDIA_BAD_CUE_ROW")
        idx=row["cue_index"]
        _require(idx not in bycue and 1<=idx<=len(original_cues) and
                 row["source_quote"]==original_cues[idx-1].text,
                 "MEDIA_DUPLICATE_OR_CHANGED_ORIGINAL_CUE")
        bycue[idx]=row
        if row.get("classification")=="MEDIA_DEPENDENT_UNMAPPED_QUARANTINE":expected.add(idx)
    used=set();seen=set()
    for item in items:
        _require(type(item) is dict and type(item.get("id")) is str and
                 item["id"] not in seen and item.get("claim_status")=="UNAPPROVED_SPEECH_ONLY_VISUAL_HOLD" and
                 item.get("financial_fact_approved") is False and item.get("speaker_verified") is False and
                 item.get("e2_pass") is False and item.get("native_claim_id") is None and
                 type(item.get("text_only_proposition_unverified")) is str and
                 len(item["text_only_proposition_unverified"].strip())>10 and
                 _list(item.get("source_refs"),50) and item["source_refs"],
                 "MEDIA_FALSE_CERTIFICATION_OR_MALFORMED_CLAIM")
        seen.add(item["id"])
        for q in item["source_refs"]:
            _require(type(q) is dict and type(q.get("cue_index")) is int and
                     q["cue_index"] in bycue and q["cue_index"] in expected and
                     q["cue_index"] not in used and
                     q.get("quote")==bycue[q["cue_index"]]["source_quote"] and
                     q.get("source_text_sha256")==_hash(q["quote"].encode("utf8")),
                     "MEDIA_QUOTE_OR_CUE_DUPLICATE_OR_SHA")
            used.add(q["cue_index"])
    _require(used==expected,"MEDIA_UNMAPPED_SPEECH_CUE_DROPPED")
    return {"schema":"IRE_V220_E2_SOURCE_SPEECH_MEDIA_HOLD_RECEIPT_V1",
        "original_media_unmapped_cues":len(expected),"media_claim_candidates_retained":len(items),
        "cue_ids_in_quarantine":sorted(used),"original_video_graphics_verified":False,
        "native_atoms_auto_inserted":0,"risk_resolved":False,"speaker_verified":False,
        "e2_final_pass":False,"e3_e4_e5_authorized":False,
        "status":"PASS_QUARANTINE_RETAINED_NOT_FINANCIAL_OR_SEMANTIC_APPROVAL"}