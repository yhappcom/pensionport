"""V145 source-only pending-cue escrow for host batch, NOT claim approval.

The native V6 host may write *structural* model/proof evidence even if some
source cues remain explicitly unresolved, but ONLY when every unresolved or
lexically suspicious unclaimed cue is present in a source-SHA-bound private
ChatGPT preflight ledger. V123 must subsequently exclude these exact source
cues and all dependent atoms before allowing any approved research candidate.
No official financial fact, audio fidelity, gold recall or P0 GO is certified.
"""
from __future__ import annotations
from .claim_census import FINANCIAL, QUALIFIER, MULTI_CLAIM
from .codec import require_hash, json_digest, sha256
from .errors import InvalidInput, QualityNotProven

_REASONS = frozenset({"ASR_ORIGINAL_UNVERIFIED", "FINANCIAL_CONTEXT_UNRESOLVED",
                      "SPEAKER_OR_QUESTION_AMBIGUOUS", "NUMERIC_OR_UNIT_AMBIGUOUS",
                      "OTHER_SOURCE_FIRST_RISK"})


def audit_host_quarantine_preflight(source, exchange, ledger):
    if type(ledger) is dict and ledger.get("schema") == TYPED_STAGING_SCHEMA:
        return audit_typed_premise_staging(source, exchange, ledger)
    rows = exchange["cue_dispositions"]
    mandatory = []
    for row in rows:
        idx = row["cue_index"]
        body = source.cues[idx - 1].text
        risky = bool(FINANCIAL.search(body) or QUALIFIER.search(body) or
                     MULTI_CLAIM.search(body))
        if row["disposition"] == "UNRESOLVED" or (
                row["disposition"] == "NO_ATOM" and risky):
            mandatory.append(idx)
    if not mandatory:
        if ledger is not None:
            raise InvalidInput("HOST_PREQUARANTINE_UNEXPECTED_WHEN_NO_RESIDUAL")
        return None
    if ledger is None:
        raise QualityNotProven("HOST_BATCH_UNRESOLVED_SOURCE_RESIDUALS")
    required = {"schema", "source_sha256", "manifest_sha256", "review_executor",
                "private_review_sha256", "cue_rows", "audio_authenticity_verified",
                "semantic_claims_independently_verified", "p0_go"}
    if (type(ledger) is not dict or set(ledger) != required or
        ledger["schema"] != "IRE_V6_HOST_SOURCE_PREQUARANTINE_V145" or
        ledger["source_sha256"] != source.source_sha256 or
        ledger["manifest_sha256"] != source.manifest_sha256 or
        ledger["review_executor"] != "CHATGPT_IN_CHAT" or
        ledger["audio_authenticity_verified"] is not False or
        ledger["semantic_claims_independently_verified"] is not False or
        ledger["p0_go"] is not False or
        type(ledger["cue_rows"]) is not list):
        raise InvalidInput("HOST_PREQUARANTINE_SOURCE_OR_AUTHORITY_INVALID")
    require_hash(ledger["private_review_sha256"],"HOST_PREQUARANTINE_CHAT_NOTE")
    checks = []
    for row in ledger["cue_rows"]:
        if (type(row) is not dict or set(row) != {
            "cue_index", "cue_text_sha256", "reason_code",
            "private_chat_cue_review_sha256", "source_first_context_reviewed"}):
            raise InvalidInput("HOST_PREQUARANTINE_ROW_SCHEMA")
        idx = row["cue_index"]
        if (type(idx) is not int or idx not in mandatory or
            row["cue_text_sha256"] != sha256(source.cues[idx-1].text.encode("utf-8")) or
            row["reason_code"] not in _REASONS or
            row["source_first_context_reviewed"] is not True):
            raise InvalidInput("HOST_PREQUARANTINE_CUE_MISSING_OR_DRIFT")
        require_hash(row["private_chat_cue_review_sha256"],"HOST_PREQUARANTINE_CUE_NOTE")
        checks.append(idx)
    if checks != mandatory or len(checks) != len(set(checks)):
        raise QualityNotProven("HOST_PREQUARANTINE_CUE_CENSUS_NOT_EXACT")
    return {
        "schema":"IRE_V6_HOST_SOURCE_PREQUARANTINE_RECEIPT_V145",
        "source_sha256":source.source_sha256,
        "manifest_sha256":source.manifest_sha256,
        "preflight_ledger_sha256":json_digest(ledger),
        "unresolved_original_cue_count":len(checks),
        "unresolved_original_cue_indices":checks,
        "host_structural_staging_only":True,
        "original_audio_authenticated":False,
        "all_claim_semantics_approved":False,
        "p0_go":False,
    }


# A distinct, deliberately non-release-compatible receipt. V123 only accepts
# the legacy V145 receipt and must not treat this development stage as approval.
TYPED_STAGING_SCHEMA = "IRE_V6_HOST_TYPED_PREMISE_STAGING_V1"
TYPED_STAGING_RECEIPT = "IRE_V6_HOST_TYPED_PREMISE_STAGING_RECEIPT_V1"


def audit_typed_premise_staging(source, exchange, ledger):
    """Replay the original typed candidate; preserve exact conditions and OPENs.

    Source-backed structure only, not entailment or a new publication path.
    The original typed record and native exchange must be retained with the
    host seal. Every projection is explicitly acknowledged, even exact ones.
    """
    from .atomic_exchange import audit_host_atomic_exchange
    from .semantic_authoring_protocol import compile_authoring

    def need(ok, code):
        if not ok:
            raise InvalidInput("HOST_TYPED_STAGING_" + code)

    def nonblank(value):
        return type(value) is str and 4 <= len(value.strip()) <= 3000

    required = {"schema", "source_sha256", "manifest_sha256", "review_executor",
                "authored", "authoring_receipt", "exchange_sha256", "projection_rows",
                "support_rows", "quarantine_cues", "quarantine_atoms", "p0_go"}
    need(type(ledger) is dict and set(ledger) == required and
         ledger["schema"] == TYPED_STAGING_SCHEMA and
         ledger["source_sha256"] == source.source_sha256 and
         ledger["manifest_sha256"] == source.manifest_sha256 and
         ledger["review_executor"] == "CHATGPT_IN_CHAT" and ledger["p0_go"] is False,
         "SCHEMA_OR_SOURCE")
    audit_host_atomic_exchange(source, exchange)
    need(ledger["exchange_sha256"] == json_digest(exchange), "EXCHANGE_DRIFT")
    authored = ledger["authored"]
    packet, receipt = compile_authoring(source, authored)
    need(receipt == ledger["authoring_receipt"], "AUTHORING_RECEIPT_DRIFT")
    typed = {f"A{i:05d}": x for i, x in enumerate(authored["atoms"], 1)}
    native = {x["claim_id"]: x for x in exchange["atoms"]}
    projection = ledger["projection_rows"]
    need(type(projection) is list and len(projection) == len(typed) == len(native),
         "PROJECTION_CENSUS")
    open_tokens = {(c, source.cues[c-1].text[lo:hi]) for c, lo, hi in
                   (x["span"] for x in authored["occurrences"] if x["disposition"] == "OPEN")}
    seen_t, seen_n, dependencies, premises = set(), set(), {}, {}
    raw_open_owners = set()
    for row in projection:
        need(type(row) is dict and set(row) == {"typed_id", "claim_id", "typed_sha256",
             "native_sha256", "note"}, "PROJECTION_ROW")
        aid, cid = row["typed_id"], row["claim_id"]
        need(type(aid) is str and type(cid) is str and aid in typed and cid in native and
             aid not in seen_t and cid not in seen_n and nonblank(row["note"]), "PROJECTION_IDS")
        t, n = typed[aid], native[cid]
        need(row["typed_sha256"] == json_digest(t) and row["native_sha256"] == json_digest(n),
             "PROJECTION_HASH")
        seen_t.add(aid); seen_n.add(cid)
        node = t["node"]
        direct = {}
        for c, lo, hi in node["direct"]:
            direct.setdefault(c, set()).update(range(lo, hi))
        refs = {r["cue_index"]: r["quote"] for r in n["source_refs"]}
        need(set(refs) == set(direct), "DIRECT_CUE_DRIFT")
        for c, positions in direct.items():
            text = source.cues[c-1].text
            lo, hi = min(positions), max(positions)+1
            need(refs[c] == text[lo:hi] and all(i in positions or text[i].isspace()
                 for i in range(lo, hi)), "DIRECT_SPAN_DRIFT")
        spans = (node["direct"] + node["context"] + node["speaker"]["evidence"] +
                 [z for q in t["quantities"] for z in q["parts"] + q["anchor"]] +
                 [z for rel in t["relations"] for z in rel["premise"] + rel["consequent"]] +
                 [x["span"] for x in t["temporal"]])
        deps = sorted({z[0] for z in spans})
        need(n["context_cue_indices"] == deps, "CONTEXT_DRIFT")
        dependencies[cid] = set(deps)
        # The current native projection has only single-cue verbatim numeric
        # references. Unsupported multi-cue quantities stay blocked, never
        # silently shed. Additional raw OPEN tokens require quarantine.
        numbers = {(x["cue_index"], x["token"]) for x in n["numeric_references"]}
        typed_numbers = set()
        for q in t["quantities"]:
            need(len(q["parts"]) == 1, "QUANTITY_NATIVE_UNREPRESENTABLE")
            c, lo, hi = q["parts"][0]
            typed_numbers.add((c, source.cues[c-1].text[lo:hi]))
        need(typed_numbers <= numbers and numbers - typed_numbers <= open_tokens,
             "QUANTITY_PROJECTION_DRIFT")
        if numbers - typed_numbers:
            raw_open_owners.add(cid)
        from re import fullmatch
        date = packet["nodes"][int(aid[1:])-1]["as_of"]
        need(n["as_of"] == (date if date and fullmatch(r"\d{4}-\d{2}-\d{2}", date) else None),
             "TEMPORAL_PROJECTION_DRIFT")
        for typ, field in (("CONDITION", "condition_cue_indices"),
                           ("EXCEPTION", "exception_cue_indices")):
            links = [z for rel in t["relations"] if rel["type"] == typ for z in rel["premise"]]
            need(n[field] == sorted({z[0] for z in links}), "PREMISE_DRIFT")
            for c, lo, hi in links:
                premises.setdefault(c, {}).setdefault(cid, set()).update(range(lo, hi))
    need(seen_t == set(typed) and seen_n == set(native), "PROJECTION_PARTITION")
    rows = exchange["cue_dispositions"]
    mandatory = {r["cue_index"] for r in rows if r["disposition"] == "UNRESOLVED" or
                 (r["disposition"] == "NO_ATOM" and any(p.search(source.cues[r["cue_index"]-1].text)
                  for p in (FINANCIAL, QUALIFIER, MULTI_CLAIM)))}
    open_cues = {x["span"][0] for x in authored["segments"] if x["status"] == "OPEN"} | {
        x["span"][0] for x in authored["occurrences"] if x["disposition"] == "OPEN"}
    q_cues = set()
    need(type(ledger["quarantine_cues"]) is list, "QUARANTINE_CUE_SCHEMA")
    for row in ledger["quarantine_cues"]:
        need(type(row) is dict and set(row) == {"cue_index", "cue_sha256", "reason"}, "QUARANTINE_CUE_ROW")
        c = row["cue_index"]
        need(type(c) is int and source.scope_first_cue <= c <= source.scope_last_cue and
             c not in q_cues and row["cue_sha256"] == sha256(source.cues[c-1].text.encode())
             and nonblank(row["reason"]), "QUARANTINE_CUE_DRIFT")
        q_cues.add(c)
    need(open_cues <= q_cues, "OPEN_SOURCE_NOT_QUARANTINED")
    q_atoms = set()
    need(type(ledger["quarantine_atoms"]) is list, "QUARANTINE_ATOM_SCHEMA")
    for row in ledger["quarantine_atoms"]:
        need(type(row) is dict and set(row) == {"claim_id", "native_sha256", "reason"}, "QUARANTINE_ATOM_ROW")
        cid = row["claim_id"]
        need(type(cid) is str and cid in native and cid not in q_atoms and
             row["native_sha256"] == json_digest(native[cid]) and nonblank(row["reason"]),
             "QUARANTINE_ATOM_DRIFT")
        q_atoms.add(cid)
    need(raw_open_owners <= q_atoms, "RAW_OPEN_OWNER_NOT_QUARANTINED")
    need({cid for cid, deps in dependencies.items() if deps & q_cues} <= q_atoms,
         "QUARANTINE_DEPENDENCY_MISSING")
    need({row["claim_id"] for row in projection if row["typed_id"] in receipt["uncertain_atoms"]} <= q_atoms,
         "UNCERTAIN_ATOM_NOT_QUARANTINED")
    supports = set()
    need(type(ledger["support_rows"]) is list, "SUPPORT_SCHEMA")
    for row in ledger["support_rows"]:
        need(type(row) is dict and set(row) == {"cue_index", "cue_sha256", "claim_ids", "reason"}, "SUPPORT_ROW")
        c = row["cue_index"]
        need(type(c) is int and c in mandatory and c not in supports | q_cues and
             rows[c-source.scope_first_cue]["disposition"] == "NO_ATOM" and
             row["cue_sha256"] == sha256(source.cues[c-1].text.encode()) and nonblank(row["reason"]),
             "SUPPORT_CUE_DRIFT")
        owners = sorted(cid for cid, deps in dependencies.items() if c in deps)
        # Every consumer must carry the actual premise. No residual text may
        # disappear under a cue-level support label.
        body = source.cues[c-1].text
        need(bool(owners) and row["claim_ids"] == owners and all(
            cid in premises.get(c, {}) and all(i in premises[c][cid] or ch.isspace()
                for i, ch in enumerate(body)) for cid in owners), "SUPPORT_PREMISE_CENSUS")
        supports.add(c)
    need(mandatory <= supports | q_cues, "MANDATORY_RESIDUAL_MISSING")
    return {"schema": TYPED_STAGING_RECEIPT, "source_sha256": source.source_sha256,
            "manifest_sha256": source.manifest_sha256,
            "preflight_ledger_sha256": json_digest(ledger), "exchange_sha256": json_digest(exchange),
            "typed_graph_sha256": receipt["graph_sha256"], "typed_atom_count": len(typed),
            "reviewed_support_cue_indices": sorted(supports),
            "quarantined_cue_indices": sorted(q_cues), "quarantined_claim_ids": sorted(q_atoms),
            "open_numeric_occurrences": receipt["open_numeric_occurrences"],
            "host_structural_staging_only": True, "original_audio_authenticated": False,
            "all_claim_semantics_approved": False, "formal_v123_input_authorized": False,
            "p0_go": False}


def audit_typed_staging_successor(source, previous, current, predecessor_sha256):
    """Conservative additive successor; never a semantic approval or retirement.

    Both records are replayed. The caller must obtain the predecessor from the
    current native event chain, not from a caller-supplied replacement graph.
    Retraction, split/merge and resolution of OPEN require a different reviewed
    transition; this path intentionally refuses them.
    """
    require_hash(predecessor_sha256, 'HOST_TYPED_PREDECESSOR')
    def need(ok, code):
        if not ok:
            raise InvalidInput('HOST_TYPED_SUCCESSOR_' + code)
    def cells(spans):
        return {(c, i) for c, lo, hi in spans for i in range(lo, hi)}
    for r in (previous, current):
        need(type(r) is dict and set(r) == {'exchange', 'ledger'}, 'RECORD')
        pin = audit_host_quarantine_preflight(source, r['exchange'], r['ledger'])
        need(type(pin) is dict and pin.get('schema') == TYPED_STAGING_RECEIPT, 'NOT_TYPED')
    old, new = previous['ledger'], current['ledger']
    a, b = old['authored'], new['authored']
    need(a['segments'] == b['segments'] and a['occurrences'] == b['occurrences'], 'SOURCE_CENSUS_CHANGED')
    need([(x['typed_id'], x['claim_id']) for x in old['projection_rows']] ==
         [(x['typed_id'], x['claim_id']) for x in new['projection_rows']], 'ATOM_LINEAGE_CHANGED')
    need(len(a['atoms']) == len(b['atoms']), 'ATOM_COUNT_CHANGED')
    retained = 0
    for x, y in zip(a['atoms'], b['atoms']):
        n, m = x['node'], y['node']
        need(all(n[k] == m[k] for k in n if k not in {'context', 'predicate', 'atomicity_reason'}), 'NODE_ROLE_OR_DIRECT_CHANGED')
        need(cells(n['context']) <= cells(m['context']), 'CONTEXT_LOSS')
        need(all(x[k] == y[k] for k in x if k not in {'node', 'relations'}), 'QUANTITY_TEMPORAL_OR_TYPE_CHANGED')
        # Every prior edge must be preserved as its own exact edge. A change
        # to its coordinates/reason requires an explicit non-additive review.
        old_edges = [json_digest(r) for r in x['relations']]
        new_edges = [json_digest(r) for r in y['relations']]
        from collections import Counter
        need(not (Counter(old_edges) - Counter(new_edges)), 'CONDITION_OR_EXCEPTION_LOSS')
        retained += len(old_edges)
    for x, y in zip(previous['exchange']['atoms'], current['exchange']['atoms']):
        need(all(x[k] == y[k] for k in x if k not in {'proposition','context_cue_indices','condition_cue_indices','exception_cue_indices'}), 'NATIVE_ROLE_OR_EVIDENCE_CHANGED')
        need(all(set(x[k]) <= set(y[k]) for k in ('context_cue_indices','condition_cue_indices','exception_cue_indices')), 'NATIVE_CONTEXT_LOSS')
    need(previous['exchange']['cue_dispositions'] == current['exchange']['cue_dispositions'], 'NATIVE_CUE_CENSUS_CHANGED')
    for field, key in (('quarantine_cues','cue_index'), ('quarantine_atoms','claim_id')):
        need({r[key] for r in old[field]} <= {r[key] for r in new[field]}, 'QUARANTINE_LOSS')
    return {'schema':'IRE_V6_TYPED_STAGING_SUCCESSOR_RECEIPT_V1',
            'predecessor_event_sha256':predecessor_sha256,
            'predecessor_record_sha256':json_digest(previous),
            'successor_record_sha256':json_digest(current),
            'retained_typed_relations':retained,
            'formal_v123_input_authorized':False, 'p0_go':False}


def audit_clean_typed_transition(source, previous, exchange, predecessor_sha256,
                                 prior_marker, prior_relation_digest):
    """Authorize formal input only for an unchanged, fully representable typed stage.

    This is deliberately NOT an OPEN/quarantine resolution or change approval.
    The predecessor remains immutable; V123 must still adjudicate
    every original cue and claim. Fully replayed support-only premises carry
    an explicit pin, not a rewritten cue disposition or a quarantine.
    """
    require_hash(predecessor_sha256, 'HOST_FORMAL_PREDECESSOR')
    require_hash(prior_relation_digest, 'HOST_FORMAL_RELATION_DIGEST')
    if type(previous) is not dict or set(previous) != {'exchange', 'ledger'}:
        raise InvalidInput('HOST_FORMAL_TYPED_RECORD_REQUIRED')
    pin = audit_typed_premise_staging(source, previous['exchange'], previous['ledger'])
    if pin != prior_marker.get('host_source_prequarantine_pin'):
        raise InvalidInput('HOST_FORMAL_PREDECESSOR_PIN_DRIFT')
    if previous['exchange'] != exchange:
        raise InvalidInput('HOST_FORMAL_EXCHANGE_CHANGED')
    if pin['quarantined_claim_ids'] or pin['quarantined_cue_indices'] or pin['open_numeric_occurrences']:
        raise QualityNotProven('HOST_FORMAL_UNRESOLVED_TYPED_SOURCE')
    if 'knowledge_change_pin' in prior_marker:
        raise QualityNotProven('HOST_FORMAL_PENDING_KNOWLEDGE_CHANGE')
    if 'private_chat_revision_sha256' in prior_marker:
        raise QualityNotProven('HOST_FORMAL_REVISION_REPLAY_REQUIRED')
    # The legacy native exchange has no separate fields for attribution or
    # estimated/speculative certainty. Do not silently erase those types.
    from .semantic_authoring_protocol import compile_authoring
    graph, _ = compile_authoring(source, previous['ledger']['authored'])
    native = {a['claim_id']:a for a in exchange['atoms']}
    for row in previous['ledger']['projection_rows']:
        i = int(row['typed_id'][1:])-1
        authored = previous['ledger']['authored']['atoms'][i]
        node, n = graph['nodes'][i], native[row['claim_id']]
        stance = 'CONDITIONAL' if node['modality']=='CONDITIONAL' else node['polarity']
        if (node['predicate'] != n['proposition'] or node['kind'] != n['kind'] or
            node['attribution'] != 'DIRECT' or node['correction'] or
            authored['certainty'] != 'ASSERTED' or authored['scenario'] != 'ACTUAL' or
            node['modality'] not in {'ASSERTED','CONDITIONAL'} or
            stance not in {'AFFIRMED','NEGATED','CONDITIONAL'} or n['stance'] != stance):
            raise QualityNotProven('HOST_FORMAL_TYPED_SEMANTIC_REPRESENTATION_REQUIRED')
    from .atomic_exchange import audit_host_atomic_exchange
    a = audit_host_atomic_exchange(source, exchange)
    if a['unresolved_cues'] or a['suspicious_no_atom_cues'] != len(pin['reviewed_support_cue_indices']):
        raise QualityNotProven('HOST_FORMAL_UNRESOLVED_NATIVE_RESIDUAL')
    return {'schema':'IRE_V6_CLEAN_TYPED_FORMAL_INPUT_V1',
            'predecessor_event_sha256':predecessor_sha256,
            'predecessor_bundle_sha256':require_hash(prior_marker['bundle_sha256']),
            'predecessor_record_sha256':json_digest(previous),
            'exchange_sha256':json_digest(exchange),
            'atom_candidate_digest':a['atom_candidate_digest'],
            'cue_disposition_digest':a['cue_disposition_digest'],
            'prior_relation_digest':prior_relation_digest,
            'reviewed_support_cue_indices':pin['reviewed_support_cue_indices'],
            'formal_input_only':True,'financial_facts_approved':False,
            'research_export_authorized':False,'p0_go':False}
