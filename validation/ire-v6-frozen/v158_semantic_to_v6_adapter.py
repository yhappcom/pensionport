"""Reusable ChatGPT source-first decisions -> real native IRE V6 atomic exchange.

Input comes from a private in-chat ChatGPT review; the V6 host must then
run the actual submit_host_atomic_batch against original source and source
inventory. This module neither invokes an API nor approves finance facts,
gold precision/recall, V123, V128 or personalized advice.
"""
from __future__ import annotations
from copy import deepcopy
import re
from ire.v6.codec import json_digest
from ire.v6.atomic_exchange import audit_host_atomic_exchange, KINDS
from ire.v6.source import VerifiedSource
from ire.v6.errors import InvalidInput
from ire.v6.claim_census import QUALIFIER

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
CONDITIONAL = re.compile(r"전제|한다면|다면|경우|라면|하면|되면|으면|보더라도|아무리|만약|물어도|때|가정")
ACTIONS = {"SET_KIND", "EXTEND_QUESTION", "SET_CONDITIONAL", "SET_STANCE_AFFIRMED"}


def _need(condition, code):
    if not condition:
        raise InvalidInput("V158_FIELD_ADAPTER_" + code)


def apply_chat_review_to_v6_exchange(source: VerifiedSource, exchange: dict,
                                     decisions: list[dict]) -> tuple[dict, dict]:
    """Return a source-verified revised V6 exchange, not final research approval.

    Every decision is {claim_id,action,before_sha256,review_sha256,payload}.
    before_sha256 pins the initial atom before ANY change in this invocation.
    For a changed atom, all its decisions cite that same initial digest.
    """
    _need(isinstance(source, VerifiedSource), "ORIGINAL_VERIFIED_SOURCE_REQUIRED")
    _need(type(exchange) is dict and type(decisions) is list and bool(decisions),
          "PRIVATE_REVIEW_DECISIONS_REQUIRED")
    prior = audit_host_atomic_exchange(source, exchange)
    original = {a["claim_id"]: a for a in exchange["atoms"]}
    before = {k: json_digest(v) for k, v in original.items()}
    revised = deepcopy(exchange)
    atoms = {a["claim_id"]: a for a in revised["atoms"]}
    rows = {r["cue_index"]: r for r in revised["cue_dispositions"]}
    seen = set()
    changes = []
    for d in decisions:
        _need(type(d) is dict and set(d) ==
              {"claim_id", "action", "before_sha256", "review_sha256", "payload"},
              "DECISION_SCHEMA")
        cid, action = d["claim_id"], d["action"]
        _need(type(cid) is str and cid in atoms and action in ACTIONS and
              (cid, action) not in seen, "UNKNOWN_OR_DUPLICATE_ACTION")
        seen.add((cid, action))
        _need(type(d["before_sha256"]) is str and before[cid] == d["before_sha256"],
              "BEFORE_ATOM_SHA_DRIFT")
        _need(type(d["review_sha256"]) is str and HEX64.fullmatch(d["review_sha256"]) is not None,
              "REVIEW_CUSTODY_SHA_MISSING")
        payload = d["payload"]
        _need(type(payload) is dict, "PATCH_PAYLOAD_REQUIRED")
        atom = atoms[cid]
        if action == "SET_KIND":
            _need(set(payload) == {"kind"} and
                  type(payload["kind"]) is str and payload["kind"] in KINDS and
                  atom["kind"] != payload["kind"], "KIND_NOT_A_REAL_CHANGE")
            previous = atom["kind"]
            atom["kind"] = payload["kind"]
            changes.append({"claim_id": cid, "field": "kind", "old": previous,
                            "new": atom["kind"], "review_sha256": d["review_sha256"]})
        elif action == "EXTEND_QUESTION":
            _need(set(payload) == {"cue_indices", "speaker"} and
                  atom["kind"] == "QUESTION" and
                  payload["speaker"] == "QUESTIONER", "QUESTION_ROLE_NOT_GROUNDED")
            ix = payload["cue_indices"]
            existing = [r["cue_index"] for r in atom["source_refs"]]
            _need(type(ix) is list and ix and
                  all(type(i) is int for i in ix) and
                  ix == list(range(existing[-1] + 1, existing[-1] + len(ix) + 1)) and
                  max(ix) <= source.scope_last_cue,
                  "QUESTION_UTTERANCE_MUST_BE_CONTIGUOUS")
            _need(any("?" in source.cues[i - 1].text or
                      "？" in source.cues[i - 1].text for i in ix),
                  "QUESTION_TEXT_HAS_NO_INTERROGATIVE")
            for i in ix:
                row = rows.get(i)
                _need(row is not None and row["disposition"] == "NO_ATOM" and
                      row["claim_ids"] == [], "QUESTION_SOURCE_HAS_CONFLICTING_CANDIDATE")
                row["disposition"] = "CANDIDATES"
                row["claim_ids"] = [cid]
                row["note"] = ""
                atom["source_refs"].append({
                    "cue_index": i, "quote": source.cues[i - 1].text})
            atom["context_cue_indices"] = sorted(
                set(atom["context_cue_indices"] + ix))
            atom["speaker"] = "QUESTIONER"
            changes.append({"claim_id": cid, "field": "source_refs+speaker",
                            "cues_appended": ix, "review_sha256": d["review_sha256"]})
        elif action == "SET_STANCE_AFFIRMED":
            # Speech act only. AFFIRMED is NEVER a certification of market
            # history, primary legal evidence, source audio, or individual advice.
            _need(set(payload) == {"stance"} and payload["stance"] == "AFFIRMED" and
                  atom["stance"] == "UNRESOLVED" and atom["kind"] != "QUESTION",
                  "AFFIRMED_IS_SPEECH_ACT_ONLY")
            _need(not any(QUALIFIER.search(source.cues[i - 1].text)
                          for i in atom["context_cue_indices"]),
                  "QUALIFIED_ASSERTION_NOT_ALLOWED")
            atom["stance"] = "AFFIRMED"
            changes.append({"claim_id": cid, "field": "stance", "old": "UNRESOLVED",
                            "new": "AFFIRMED", "review_sha256": d["review_sha256"],
                            "financial_fact_truth_approved": False})
        else:
            _need(set(payload) == {"condition_cue_indices"}, "CONDITION_PAYLOAD_SCHEMA")
            ix = payload["condition_cue_indices"]
            _need(type(ix) is list and ix and all(type(i) is int for i in ix) and
                  ix == sorted(set(ix)) and
                  set(ix).issubset(atom["context_cue_indices"]),
                  "CONDITION_SOURCE_CONTEXT_MISSING")
            _need(all(CONDITIONAL.search(source.cues[i - 1].text) for i in ix),
                  "CONDITION_NOT_IN_ORIGINAL_LITERAL")
            atom["condition_cue_indices"] = sorted(
                set(atom["condition_cue_indices"] + ix))
            atom["stance"] = "CONDITIONAL"
            changes.append({"claim_id": cid,
                            "field": "condition_cue_indices+stance",
                            "source_cues": ix,
                            "review_sha256": d["review_sha256"]})
    result = audit_host_atomic_exchange(source, revised)
    _need(prior["original_scoped_cues_enumerated"] ==
          result["original_scoped_cues_enumerated"] and
          len(revised["atoms"]) == len(exchange["atoms"]), "ATOMIC_SOURCE_COUNT_DRIFT")
    return revised, {
        "source_sha256": source.source_sha256,
        "change_count": len(changes),
        "changes": changes,
        "old_atom_candidate_digest": prior["atom_candidate_digest"],
        "new_atom_candidate_digest": result["atom_candidate_digest"],
        "native_host_committed": False,
        "chat_v123_final_approved": False,
        "gold_accuracy_certified": False,
        "v128_published": False,
    }
