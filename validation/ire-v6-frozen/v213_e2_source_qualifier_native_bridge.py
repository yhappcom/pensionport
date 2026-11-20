"""V213 E2-only qualifier provenance and safe native V6 projection.

Solves the actual V182 pipeline break: V176's free-text conditions and
exceptions have no cue indices in V6 unless a ChatGPT reviewer explicitly
attributes each term to original source text. Reviewer cautions MUST NOT be
cast as source-spoken conditions. The private reviewer journal is append-only
and pinned to an immutable V176 owner head and original source bytes.

This is E2 (not V186/V187 E3); no model API, no E3 or V123 approval, no
financial truth or independent gold claims. Frozen native V6 remains intact.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import stat
from contextlib import closing
from collections import Counter

from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput
from v176_chat_engine_loop import EngineChatSession

CHALLENGE = "IRE_V213_E2_CHAT_SOURCE_QUALIFIER_TASK_V1"
ANSWER = "IRE_V213_E2_CHAT_QUALIFIER_ANSWER_V1"
EVENT = "IRE_V213_E2_APPEND_ONLY_QUALIFIER_SOURCE_EVENT_V1"
CONFIG = "IRE_V213_E2_OWNER_QUALIFIER_JOURNAL_PIN_V1"
ZERO = "0" * 64
ORIGINS = {"SOURCE_EXPLICIT", "SOURCE_CONTEXT", "REVIEWER_ADDED", "UNRESOLVED"}
ANSWER_ROW_FIELDS = {
    "term_id","term_sha256","origin","source_quote","source_cue_index",
    "meaning_rationale","speaker_condition_certified","financial_fact_approved",
    "independent_gold_certified","e2_final_pass","e3_e4_e5_authorized",
}


def require(ok, reason):
    if not ok:
        raise InvalidInput("V213_E2_" + reason)


def digest(item):
    return json_digest(item)


class E2QualifierCustody:
    def __init__(self, engine, private_path, *, expected_owner_head):
        require(type(engine) is EngineChatSession, "NATIVE_OWNER_REQUIRED")
        require(type(expected_owner_head) is str and
                len(expected_owner_head)==64 and
                all(c in "0123456789abcdef" for c in expected_owner_head),
                "OWNER_HEAD_PIN")
        self.engine = engine
        self.expected_owner_head = expected_owner_head
        self.path = Path(private_path)
        require(self.path != engine.path and
                not self.path.is_symlink(), "PRIVATE_PATH_NOT_OWNER_OR_SYMLINK")
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if not self.path.exists():
            fd=os.open(str(self.path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
        require(self.path.is_file() and
                stat.S_IMODE(self.path.stat().st_mode)==0o600,
                "QUALIFIER_SQLITE_NOT_PRIVATE_0600")
        cfg=self._config()
        with closing(self._db()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS config(k TEXT PRIMARY KEY, v TEXT NOT NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS events(
                seq INTEGER PRIMARY KEY, prev_sha TEXT NOT NULL,
                event_sha TEXT NOT NULL,payload TEXT NOT NULL)""")
            row=db.execute("SELECT v FROM config WHERE k='owner'").fetchone()
            if row is None:
                db.execute("INSERT INTO config VALUES('owner',?)",
                           (canonical(cfg).decode("utf-8"),))
            else:
                try:
                    saved=json.loads(row[0])
                except (ValueError,TypeError) as e:
                    raise InvalidInput("V213_E2_OWNER_CONFIG_CORRUPT") from e
                require(saved==cfg and
                        row[0]==canonical(cfg).decode("utf-8"),
                        "OWNER_CONFIG_NOT_THIS_ORIGINAL")
            db.commit()
            self._audit(db)

    def _db(self):
        require(not self.path.is_symlink() and
                self.path.is_file() and
                stat.S_IMODE(self.path.stat().st_mode)==0o600,
                "QUALIFIER_SQLITE_PERMISSIONS_CHANGED")
        db=sqlite3.connect(self.path,isolation_level=None,timeout=20)
        db.execute("PRAGMA busy_timeout=20000")
        return db

    def _owner(self):
        p=self.engine.progress()
        require(p["checkpoint_head_sha256"]==self.expected_owner_head and
                p["source_first_review_complete"],"OWNER_HEAD_OR_CUE_CENSUS_CHANGED")
        with closing(self.engine._connect()) as db:
            head,rows=self.engine._audit(db)
        require(head==self.expected_owner_head,"OWNER_AUDIT_HEAD_CHANGED")
        return rows

    def _terms(self):
        rows=self._owner()
        terms={}
        for cue in sorted(rows):
            decision=rows[cue][1]
            if decision["disposition"]!="ASSERTION":
                continue
            for ordinal,claim in enumerate(decision["claims"],1):
                for typ in ("conditions","exceptions"):
                    for term_ord,term in enumerate(claim[typ],1):
                        tid=f"{cue:05d}:{ordinal:02d}:{typ}:{term_ord:02d}"
                        terms[tid]={
                            "term_id":tid,
                            "cue_index":cue,
                            "claim_ordinal":ordinal,
                            "field":typ,
                            "term_sha256":sha256(term.encode("utf-8")),
                            "owner_claim_sha256":digest(claim),
                            "claim_context_cues":claim["context_cue_indices"],
                            "source_cue_sha256":sha256(
                                self.engine.source.cues[cue-1].text.encode("utf-8")),
                        }
        return terms

    def _config(self):
        self._owner()
        return {"schema":CONFIG,"owner_head_sha256":self.expected_owner_head,
                "source_sha256":self.engine.source.source_sha256,
                "manifest_sha256":self.engine.source.manifest_sha256}

    def _packet(self,ids,prior_head,terms):
        require(type(ids) is list and
                ids==sorted(set(ids)) and
                all(t in terms for t in ids) and type(prior_head) is str and
                len(prior_head)==64,"TERM_TASK_INDEX_SCHEMA")
        cids=sorted({k for t in ids for k in terms[t]["claim_context_cues"]})
        rows=[{"cue_index":i,
               "source_text":self.engine.source.cues[i-1].text,
               "source_text_sha256":sha256(
                   self.engine.source.cues[i-1].text.encode("utf-8"))}
              for i in cids]
        p={"schema":CHALLENGE,
           "owner_head_sha256":self.expected_owner_head,
           "source_sha256":self.engine.source.source_sha256,
           "private_qualifier_head_sha256":prior_head,
           "term_ids":ids,
           "terms":[terms[i] for i in ids],
           "source_context_cues":rows,
           "independent_gold_certified":False,
           "financial_fact_approved":False,
           "e2_final_pass":False,
           "e3_e4_e5_authorized":False}
        return {**p,"challenge_sha256":digest(p)}

    def _validate_rows(self,packet,answer,terms):
        require(type(answer) is dict and set(answer)=={
                    "schema","challenge_sha256","review_executor","responses"} and
                answer["schema"]==ANSWER and
                answer["challenge_sha256"]==packet["challenge_sha256"] and
                answer["review_executor"]=="CHATGPT_IN_CHAT" and
                type(answer["responses"]) is list and
                len(answer["responses"])==len(packet["term_ids"]),
                "CHAT_REVIEW_ANSWER_SCHEMA")
        for tid,row in zip(packet["term_ids"],answer["responses"]):
            term=terms[tid]
            require(type(row) is dict and set(row)==ANSWER_ROW_FIELDS and
                    row["term_id"]==tid and
                    row["term_sha256"]==term["term_sha256"] and
                    type(row["origin"]) is str and
                    row["origin"] in ORIGINS and
                    type(row["meaning_rationale"]) is str and
                    len(row["meaning_rationale"].strip())>=28 and
                    all(row[k] is False for k in (
                        "speaker_condition_certified","financial_fact_approved",
                        "independent_gold_certified","e2_final_pass",
                        "e3_e4_e5_authorized")),
                    "QUALIFIER_RESPONSE_OR_FALSE_AUTHORITY")
            if row["origin"] in {"SOURCE_EXPLICIT","SOURCE_CONTEXT"}:
                i=row["source_cue_index"]
                require(type(i) is int and
                        i in term["claim_context_cues"] and
                        type(row["source_quote"]) is str and
                        len(row["source_quote"].strip())>=3 and
                        " ".join(row["source_quote"].split()) in
                        " ".join(self.engine.source.cues[i-1].text.split()),
                        "SOURCE_QUOTE_NOT_VERBATIM_IN_CONTEXT")
            else:
                require(row["source_quote"] is None and
                        row["source_cue_index"] is None,
                        "REVIEWER_CAUTION_CANNOT_BECOME_SOURCE_ANCHOR")

    def _audit(self,db):
        terms=self._terms()
        chain=ZERO
        done={}
        rows=db.execute(
            "SELECT seq,prev_sha,event_sha,payload FROM events ORDER BY seq").fetchall()
        for seq,(number,prev,event_sha,payload) in enumerate(rows,1):
            require(number==seq and prev==chain,
                    "HASHCHAIN_SEQUENCE_OR_PREV_CHANGED")
            try:
                frame=json.loads(payload)
            except (TypeError,ValueError) as e:
                raise InvalidInput("V213_E2_QUALIFIER_EVENT_JSON_CORRUPT") from e
            require(type(frame) is dict and set(frame)=={
                "schema","seq","prev_sha","owner_head_sha256",
                "source_sha256","challenge","answer",
                "financial_fact_approved","e2_final_pass","e3_e4_e5_authorized"
            } and frame["schema"]==EVENT and
                    frame["seq"]==seq and frame["prev_sha"]==prev and
                    frame["owner_head_sha256"]==self.expected_owner_head and
                    frame["source_sha256"]==self.engine.source.source_sha256 and
                    frame["financial_fact_approved"] is False and
                    frame["e2_final_pass"] is False and
                    frame["e3_e4_e5_authorized"] is False and
                    payload==canonical(frame).decode("utf-8") and
                    digest(frame)==event_sha,
                    "QUALIFIER_EVENT_HASH_OR_FIELDS_CHANGED")
            challenge=frame["challenge"]
            require(type(challenge) is dict and
                    type(challenge.get("term_ids")) is list,
                    "QUALIFIER_TASK_REPLAY_FIELDS")
            ids=challenge["term_ids"]
            require(challenge==self._packet(ids,prev,terms),
                    "REGENERATED_ORIGINAL_TASK_NOT_EQUAL")
            self._validate_rows(challenge,frame["answer"],terms)
            for row in frame["answer"]["responses"]:
                require(row["term_id"] not in done,
                        "DUPLICATE_OR_OVERWRITTEN_QUALIFIER")
                done[row["term_id"]]=row
            chain=event_sha
        return chain,terms,done

    def progress(self,*,expected_private_head=None):
        with closing(self._db()) as db:
            head,terms,done=self._audit(db)
        if expected_private_head is not None:
            require(head==expected_private_head,
                    "EXTERNAL_PRIVATE_CHECKPOINT_HEAD_MISMATCH")
        counts=Counter(x["origin"] for x in done.values())
        return {"schema":"IRE_V213_E2_SOURCE_QUALIFIER_PROGRESS_V1",
                "journal_head_sha256":head,
                "owner_head_sha256":self.expected_owner_head,
                "source_sha256":self.engine.source.source_sha256,
                "total_terms":len(terms),"reviewed_terms":len(done),
                "remaining_terms":len(terms)-len(done),
                "reviewed_origin_counts":dict(counts),
                "fully_covered":len(terms)==len(done),
                "source_explicit_terms":counts["SOURCE_EXPLICIT"],
                "reviewer_added_terms":counts["REVIEWER_ADDED"],
                "source_context_terms":counts["SOURCE_CONTEXT"],
                "unresolved_terms":counts["UNRESOLVED"] +
                    len(terms)-len(done),
                "original_owner_journal_mutated":False,
                "independent_gold_certified":False,
                "e2_final_pass":False,"e3_e4_e5_authorized":False}

    def prepare(self,*,limit=16):
        require(type(limit) is int and 1<=limit<=40,
                "QUALIFIER_BATCH_SIZE")
        with closing(self._db()) as db:
            head,terms,done=self._audit(db)
        available=[t for t in sorted(terms) if t not in done]
        return self._packet(available[:limit],head,terms)

    def submit(self,packet,answer,*,expected_private_head):
        require(type(packet) is dict and type(answer) is dict and
                type(expected_private_head) is str,"QUALIFIER_SUBMIT_FIELDS")
        with closing(self._db()) as db:
            db.execute("BEGIN IMMEDIATE")
            head,terms,done=self._audit(db)
            require(head==expected_private_head,"QUALIFIER_HEAD_STALE")
            require(packet==self._packet(
                [x for x in sorted(terms) if x not in done][:
                    len(packet.get("term_ids",[]))],head,terms) and
                len(packet["term_ids"])>=1 and
                len(packet["term_ids"])<=40,
                "QUALIFIER_TASK_NOT_ISSUED_OR_STALE")
            self._validate_rows(packet,answer,terms)
            next_seq=db.execute("SELECT COUNT(*) FROM events").fetchone()[0]+1
            event={"schema":EVENT,"seq":next_seq,"prev_sha":head,
                   "owner_head_sha256":self.expected_owner_head,
                   "source_sha256":self.engine.source.source_sha256,
                   "challenge":packet,"answer":answer,
                   "financial_fact_approved":False,
                   "e2_final_pass":False,"e3_e4_e5_authorized":False}
            event_head=digest(event)
            db.execute("INSERT INTO events VALUES(?,?,?,?)",(
                next_seq,head,event_head,canonical(event).decode("utf-8")))
            db.commit()
            return {"status":"E2_PRIVATE_SOURCE_QUALIFIER_REVIEW_COMMITTED_UNAPPROVED",
                    "private_head_sha256":event_head,
                    "terms_committed":len(answer["responses"]),
                    "e2_final_pass":False,"e3_e4_e5_authorized":False}

    def projected_source_anchors(self):
        """Adapter to frozen V176.compile_native_v6_stage optional input."""
        with closing(self._db()) as db:
            head,terms,done=self._audit(db)
        projections={}
        for tid,term in terms.items():
            key=(term["cue_index"],term["claim_ordinal"])
            q=projections.setdefault(key,{
                "conditions":set(),"exceptions":set(),
                "source_explicit_terms":0,
                "source_explicit_condition_terms":0,
                "source_explicit_exception_terms":0,
                "unmapped_terms":0,"reviewer_added_terms":0,
                "source_context_terms":0,"reviewed_terms":0})
            review=done.get(tid)
            if review is None:
                q["unmapped_terms"]+=1
                continue
            q["reviewed_terms"]+=1
            if review["origin"]=="SOURCE_EXPLICIT":
                q[term["field"]].add(review["source_cue_index"])
                q["source_explicit_terms"]+=1
                typ=("source_explicit_condition_terms" if
                     term["field"]=="conditions" else
                     "source_explicit_exception_terms")
                q[typ]+=1
            else:
                q["unmapped_terms"]+=1
                q["reviewer_added_terms"]+=int(review["origin"]=="REVIEWER_ADDED")
                q["source_context_terms"]+=int(review["origin"]=="SOURCE_CONTEXT")
        status=self.progress(expected_private_head=head)
        return {"head":head,"status":status,
                "by_claim":{key:{
                    field:sorted(values) if type(values) is set else values
                    for field,values in q.items()}
                    for key,q in projections.items()}}


def compile_e2_safe_native_stage(owner,custody):
    """Stage genuine cue-anchored V6 candidates; never release E2 approval."""
    require(type(custody) is E2QualifierCustody and
            owner is custody.engine and
            owner.progress()["checkpoint_head_sha256"]==
                custody.expected_owner_head,
            "STAGE_NOT_PINNED_TO_OWNER")
    # V176's audited real native V6 converter, NOT a parallel fake schema.
    exchange,stage=owner.compile_native_v6_stage(
        qualifier_provenance=custody)
    q=custody.projected_source_anchors()
    from ire.v6.atomic_exchange import audit_host_atomic_exchange
    audit=audit_host_atomic_exchange(owner.source,exchange)
    assert audit["proposed_atomic_claims"]==len(exchange["atoms"])
    # Reconstruct the exact V176 ordinal assignment without modifying owner.
    with closing(owner._connect()) as db:
        _,reviewed=owner._audit(db)
    ordinal=[]
    for cue in owner.source.cues:
        row=reviewed.get(cue.index)
        if row and row[1]["disposition"]=="ASSERTION" and all(
                c["kind"]!="ANECDOTE" for c in row[1]["claims"]):
            ordinal.extend((cue.index,i) for i in
                           range(1,len(row[1]["claims"])+1))
    require(len(ordinal)==len(exchange["atoms"]),
            "NATIVE_CLAIM_COUNT_CHANGED")
    for atom,key in zip(exchange["atoms"],ordinal):
        attrs=q["by_claim"].get(key)
        conditions=attrs["conditions"] if attrs else []
        exceptions=attrs["exceptions"] if attrs else []
        require(atom["condition_cue_indices"]==conditions and
                atom["exception_cue_indices"]==exceptions and
                set(conditions+exceptions).issubset(
                    atom["context_cue_indices"]) and
                atom["stance"]=="UNRESOLVED" and
                atom["speaker"]=="UNKNOWN",
                "NATIVE_V6_SOURCE_QUALIFIER_LOST_OR_PREMATURE_SPEAKER")
    mapped=sum(v["source_explicit_terms"]
               for v in q["by_claim"].values())
    unresolved=sum(v["unmapped_terms"] for v in q["by_claim"].values())
    return exchange,{
        "schema":"IRE_V213_E2_SOURCE_QUALIFIER_NATIVE_V6_RECEIPT_V1",
        "original_source_sha256":owner.source.source_sha256,
        "owner_head_sha256":custody.expected_owner_head,
        "e2_qualifier_private_head_sha256":q["head"],
        "native_v6_atom_candidate_count":len(exchange["atoms"]),
        "source_explicit_condition_exception_terms_mapped":mapped,
        "source_terms_not_projected_as_speaker_spoken":unresolved,
        "all_original_owner_terms_reviewed":q["status"]["fully_covered"],
        "all_v6_projected_indices_match_verbatim_source_reviews":True,
        "source_context_and_reviewer_cautions_not_misrepresented":True,
        "owner_original_journal_mutated":False,
        "speaker_and_stance_finalized":False,
        "independent_gold_certified":False,
        "e2_final_pass":False,"e3_e4_e5_authorized":False,
        "financial_truth_approved":False,
        "knowledge_published":False,
        "native_v6_audit_sha256":digest(audit),
    }
