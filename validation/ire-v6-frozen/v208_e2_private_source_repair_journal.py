"""V208 E2 — atomic private cue→ChatGPT repair custody and resume.

Only an audited, already-checkpointed V206 cue batch can own a V207 repair.
One PRIVATE 0600 SQLite database carries two append-only hash-linked ledgers.
ChatGPT must explicitly author V207; the engine never generates a verdict.
Nothing here writes the V176 owner, native V6 claims or V123/V126/V128.
"""
from __future__ import annotations

from contextlib import closing
import json

from ire.v6.codec import ZERO_SHA, canonical, json_digest
from ire.v6.errors import InvalidInput
from v206_e2_private_cue_checkpoint import PrivateE2CensusCheckpoint
from v207_e2_unreleased_chat_repair import audit_e2_chat_repairs

SCHEMA="IRE_V208_E2_PRIVATE_SOURCE_REPAIR_CHAIN_V1"


def need(ok,reason):
    if not ok:
        raise InvalidInput("V208_E2_REPAIR_"+reason)


class PrivateE2RepairJournal:
    """A second SHA chain, foreign-keyed to the actual V206 review batch."""

    def __init__(self,path,owner,*,expected_owner_head):
        self.census=PrivateE2CensusCheckpoint(
            path,owner,expected_owner_head=expected_owner_head)
        self.owner=owner
        self.owner_head=expected_owner_head
        with closing(self.census._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE IF NOT EXISTS e2_repairs(
                seq INTEGER PRIMARY KEY,
                prev_sha256 TEXT NOT NULL,
                event_sha256 TEXT NOT NULL,
                event_json TEXT NOT NULL)""")
            db.commit()
            self._audit_repairs(db)

    def _audit_repairs(self,db):
        self.census._check_owner()
        census_head,covered,saved=self.census._audit(db)
        owners={}
        for _,(event_hash,event) in saved.items():
            owners[event_hash]=event
        # The checkpoint head used for a repair must be at or AFTER the
        # specific review it cites. A forged event cannot claim an older
        # snapshot that did not yet contain that source review.
        ordered_census=[digest for _,(digest,_) in saved.items()]
        census_positions={ZERO_SHA:0}
        census_positions.update({
            digest:index for index,digest in enumerate(ordered_census,1)
        })
        prev=ZERO_SHA
        repaired={}
        projections={}
        for seq,row in enumerate(db.execute(
                "SELECT seq,prev_sha256,event_sha256,event_json "
                "FROM e2_repairs ORDER BY seq"),1):
            rseq,rprev,rdigest,payload=row
            need(rseq==seq and rprev==prev,
                 "CHAIN_SEQUENCE_OR_PREV_CHANGED")
            try:
                event=json.loads(payload)
            except (TypeError,ValueError) as error:
                raise InvalidInput(
                    "V208_E2_REPAIR_CHAIN_JSON_CORRUPT") from error
            need(type(event) is dict and set(event)=={
                "schema","seq","prev_sha256","source_sha256",
                "owner_head_sha256","census_event_sha256",
                "census_head_sha256","challenge_sha256","answer_sha256",
                "review_plan","unreleased_projection_sha256",
            } and event.get("schema")==SCHEMA and
                event.get("seq")==rseq and
                event.get("prev_sha256")==rprev and
                event.get("source_sha256")==self.owner.source.source_sha256 and
                event.get("owner_head_sha256")==self.owner_head and
                json_digest(event)==rdigest and
                canonical(event).decode("utf-8")==payload,
                "CHAIN_RECORD_OR_HASH_CHANGED")
            # All indexed custody fields MUST be hash-shaped strings before
            # any dict or set lookup. Otherwise malformed private SQLite
            # payloads can trigger KeyError/TypeError instead of fail-closed.
            hashes=(
                "census_event_sha256","census_head_sha256",
                "challenge_sha256","answer_sha256",
                "unreleased_projection_sha256")
            need(all(type(event[k]) is str and len(event[k])==64 and
                     all(c in "0123456789abcdef" for c in event[k])
                     for k in hashes),
                 "INVALID_REPAIR_HASH_FIELD_SCHEMA")
            census_event=owners.get(event["census_event_sha256"])
            need(census_event is not None and
                 event["census_head_sha256"] in census_positions and
                 census_positions[event["census_head_sha256"]]>=
                    census_positions[event["census_event_sha256"]] and
                 event["census_event_sha256"] not in repaired,
                 "UNLINKED_OR_DUPLICATED_CENSUS_REPAIR")
            challenge=census_event["challenge"]
            answer=census_event["answer"]
            need(event["challenge_sha256"]==
                     challenge.get("challenge_sha256") and
                 event["answer_sha256"]==json_digest(answer) and
                 type(event["review_plan"]) is dict,
                 "REPAIR_NOT_PINNED_TO_SAVED_ORIGINAL")
            projection=audit_e2_chat_repairs(
                self.owner,challenge,answer,event["review_plan"],
                expected_owner_head=self.owner_head)
            need(event["unreleased_projection_sha256"]==
                     json_digest(projection) and
                 projection["e2_final_pass"] is False and
                 projection["knowledge_written"] is False and
                 projection["original_v176_changed"] is False,
                 "REPLAYED_REPAIR_PROJECTION_DRIFT")
            repaired[event["census_event_sha256"]]=event
            projections[event["census_event_sha256"]]=projection
            prev=rdigest
        return prev,census_head,saved,repaired,projections

    def progress(self,*,externally_pinned_repair_head=None):
        with closing(self.census._connect()) as db:
            head,census_head,saved,repaired,projections=self._audit_repairs(db)
        if externally_pinned_repair_head is not None:
            need(head==externally_pinned_repair_head,
                 "EXTERNAL_REPAIR_HEAD_CHANGED")
        held={h:e for _,(h,e) in saved.items()
              if e["audit_status"]=="HOLD_SEMANTIC_OR_EXTRACTION_LOSS"}
        return {
            "schema":"IRE_V208_E2_PRIVATE_REPAIR_PROGRESS_V1",
            "source_sha256":self.owner.source.source_sha256,
            "owner_head_sha256":self.owner_head,
            "census_head_sha256":census_head,
            "repair_head_sha256":head,
            "source_review_batches":len(saved),
            "held_review_batches":len(held),
            "repair_batches_recorded":len(repaired),
            "held_batches_awaiting_explicit_chat_repair":
                sum(h not in repaired for h in held),
            "unreleased_draft_claims":
                sum(p["unreleased_draft_claims"] for p in projections.values()),
            "review_issues_kept_open":
                sum(p["still_open_issues"] for p in projections.values()),
            "original_v176_mutated":False,
            "native_v6_approval":False,
            "independent_semantic_gold_certified":False,
            "e2_final_pass":False,
            "e3_e4_e5_authorized":False,
            "knowledge_published":False,
        }

    def record_chat_repair(self,challenge,answer,plan,*,
                           expected_census_head,expected_repair_head):
        """One atomic repair commit only after an exact V206 cue review event."""
        need(type(challenge) is dict and type(answer) is dict and
             type(plan) is dict and
             type(expected_census_head) is str and
             type(expected_repair_head) is str,
             "REPAIR_INPUT_SCHEMA")
        # Audit before lock for informative failures, then replay under lock.
        projection=audit_e2_chat_repairs(
            self.owner,challenge,answer,plan,
            expected_owner_head=self.owner_head)
        need(projection["issues_reviewed"]>0,
             "EMPTY_REPAIR_WITHOUT_OPEN_SOURCE_ISSUE")
        with closing(self.census._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            head,census_head,saved,repaired,_=self._audit_repairs(db)
            need(census_head==expected_census_head,
                 "CENSUS_CHANGED_DURING_REPAIR")
            batch=[(digest,event) for _,(digest,event) in saved.items()
                   if event["challenge"]==challenge and
                      event["answer"]==answer]
            need(len(batch)==1,"REPAIR_NOT_LINKED_TO_SAVED_CUE_REVIEW")
            census_event_sha=batch[0][0]
            need(batch[0][1]["audit_status"]==
                     "HOLD_SEMANTIC_OR_EXTRACTION_LOSS",
                 "REPAIR_ONLY_FOR_SOURCE_HOLD")
            if census_event_sha in repaired:
                prev=repaired[census_event_sha]
                if prev["review_plan"]==plan:
                    db.rollback()
                    return {
                        "status":"IDEMPOTENT_E2_REPAIR_REPLAY",
                        "repair_head_sha256":head,
                        "census_head_sha256":census_head,
                        "issues_reviewed":projection["issues_reviewed"],
                        "e2_final_pass":False,
                        "e3_e4_e5_authorized":False,
                    }
                need(False,"CONFLICTING_SOURCE_REPAIR_NO_OVERWRITE")
            need(head==expected_repair_head,"EXPECTED_REPAIR_HEAD_STALE")
            self.census._check_owner()
            seq=len(repaired)+1
            event={
                "schema":SCHEMA,"seq":seq,"prev_sha256":head,
                "source_sha256":self.owner.source.source_sha256,
                "owner_head_sha256":self.owner_head,
                "census_event_sha256":census_event_sha,
                "census_head_sha256":census_head,
                "challenge_sha256":challenge["challenge_sha256"],
                "answer_sha256":json_digest(answer),
                "review_plan":plan,
                "unreleased_projection_sha256":json_digest(projection),
            }
            digest=json_digest(event)
            db.execute("INSERT INTO e2_repairs VALUES(?,?,?,?)",(
                seq,head,digest,canonical(event).decode("utf-8")))
            db.commit()
            return {
                "status":"E2_REPAIR_SAVED_UNRELEASED_PRIVATE",
                "repair_head_sha256":digest,
                "census_head_sha256":census_head,
                "issues_reviewed":projection["issues_reviewed"],
                "unreleased_draft_claims":projection["unreleased_draft_claims"],
                "e2_final_pass":False,
                "e3_e4_e5_authorized":False,
                "knowledge_published":False,
            }
