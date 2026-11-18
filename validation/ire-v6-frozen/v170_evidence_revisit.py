"""V170: evidence-triggered follow-up for V169 KEEP_OPEN research atoms.

V169 intentionally commits a source-pinned first PASS over each OPEN atom.
That means the queue cursor alone does not mean the atom is resolved. This
private append-only supplement permits further ChatGPT review *only when a
new original evidence body is provided*. Repeated identical evidence cannot
manufacture progress. Original owner and native V123 states never change.

The chat host supplies evidence/review callbacks during the active turn; this
module has no API/model invocation or automatic claim-approval authority.
"""
from __future__ import annotations

import copy
import json
from contextlib import closing

from v166_e4_full_video_readiness import digest
from v167_chat_research_loop import _evidence_summary, execute_chat_review_round
from v169_chat_research_journal import ChatReviewJournal, _canonical, ZERO

SCHEMA = "IRE_V170_NEW_EVIDENCE_REVISIT_JOURNAL_V1"


def _need(ok, reason):
    if not ok:
        raise ValueError("V170_REVISIT_" + reason)


class EvidenceRevisitJournal:
    """A separate, append-only private event chain for old KEEP_OPEN items."""

    def __init__(self, journal: ChatReviewJournal):
        _need(isinstance(journal, ChatReviewJournal), "SOURCE_JOURNAL_REQUIRED")
        self.journal = journal
        with closing(journal._connect()) as con:
            con.execute("""CREATE TABLE IF NOT EXISTS revisit_receipts (
                seq INTEGER PRIMARY KEY, claim_id TEXT NOT NULL,
                original_proposal_sha TEXT NOT NULL,
                preceding_proposal_sha TEXT NOT NULL,
                previous_head TEXT NOT NULL,
                proposal_json TEXT NOT NULL,
                head TEXT NOT NULL,
                UNIQUE (claim_id, preceding_proposal_sha)
            )""")
            con.commit()
        self.status()

    def _base(self):
        receipt = self.journal.export_unreleased_proposals()
        tasks = {x["claim_id"]: x for x in self.journal.docket["items"]}
        base = {p["claim_id"]:p for p in receipt["proposals"]}
        _need(len(base) == receipt["proposals_created"] and
              set(base).issubset(tasks), "ORIGINAL_PROPOSAL_CENSUS")
        return receipt, tasks, base

    def _read(self, con, tasks, initial):
        rows = con.execute("SELECT seq,claim_id,original_proposal_sha,"
                           "preceding_proposal_sha,previous_head,proposal_json,head "
                           "FROM revisit_receipts ORDER BY seq").fetchall()
        head, effective, count = ZERO, dict(initial), 0
        seen_evidence = {cid:{x["body_sha256"] for x in p["source_evidence"]}
                         for cid,p in initial.items()}
        for index, (seq,cid,base_sha,before_sha,old_head,pjson,new_head) in enumerate(rows,1):
            _need(seq == index and cid in initial and
                  base_sha == digest(initial[cid]) and
                  before_sha == digest(effective[cid]) and old_head == head and
                  effective[cid]["proposed_decision"] == "KEEP_OPEN",
                  "EVENT_OR_ORIGINAL_PROPOSAL_DRIFT")
            try:
                proposal=json.loads(pjson)
            except (TypeError,ValueError) as exc:
                raise ValueError("V170_REVISIT_PRIVATE_RECEIPT_NOT_JSON") from exc
            task=tasks[cid]
            _need(type(proposal) is dict and
                  proposal.get("claim_id") == cid and
                  proposal.get("segment_id") == task["segment_id"] and
                  proposal.get("atom_sha256") == task["atom_sha256"] and
                  proposal.get("prior_review_sha256") == task["prior_review_sha256"] and
                  proposal.get("prior_status") == "OPEN" and
                  proposal.get("proposed_decision") in {
                      "KEEP_OPEN", "CANDIDATE_NEEDS_NATIVE_REVIEW",
                      "QUARANTINE_PROPOSAL", "REJECT_PROPOSAL"} and
                  proposal.get("applied_to_native_v123") is False and
                  proposal.get("approved_by_e4") is False and
                  proposal.get("knowledge_released") is False and
                  type(proposal.get("source_evidence")) is list,
                  "REVISIT_UNPINNED_OR_FALSE_RELEASE")
            new_body_hashes={x["body_sha256"] for x in proposal["source_evidence"]}
            _need(bool(new_body_hashes - seen_evidence[cid]), "EVIDENCE_NOT_NEW")
            seen_evidence[cid].update(new_body_hashes)
            event={"schema":SCHEMA,"seq":seq,"root_docket_sha256":
                   self.journal.docket["docket_sha256"],
                   "claim_id":cid,"original_proposal_sha":base_sha,
                   "preceding_proposal_sha":before_sha,"previous_head":head,
                   "proposal":proposal}
            head=digest(event)
            _need(head == new_head, "REVISIT_CHAIN_HASH_DRIFT")
            effective[cid]=proposal
            count+=1
        return effective,head,count

    def status(self):
        r,t,b=self._base()
        with closing(self.journal._connect()) as con:
            effective,head,n=self._read(con,t,b)
        statuses=[p["proposed_decision"] for p in effective.values()]
        return {"schema":SCHEMA,
                "root_docket_sha256":self.journal.docket["docket_sha256"],
                "owner_source_sha256":self.journal.docket["owner_source_sha256"],
                "initial_ever_open_count":r["original_open_count"],
                "never_researched_count":r["unprocessed_open_count"],
                "latest_still_open_count":statuses.count("KEEP_OPEN"),
                "quarantine_proposal_not_native_approved":statuses.count("QUARANTINE_PROPOSAL"),
                "candidate_not_native_approved":statuses.count("CANDIDATE_NEEDS_NATIVE_REVIEW"),
                "revisit_events":n,"revisit_head_sha256":head,
                "native_v123_approved":False,"e4_approved":False,"e5_authorized":False}

    def run_revisit(self, claim_id, *, evidence_retriever, chat_reviewer,
                    _failure_injector=None):
        """Revisit one old KEEP_OPEN only if fresh original bytes were supplied.

        A callback exception or any stale concurrent journal update leaves
        the new chain unchanged. E4 must independently authenticate all bytes.
        """
        _need(callable(evidence_retriever) and callable(chat_reviewer),
              "IN_CHAT_CALLBACKS_REQUIRED")
        receipt,tasks,base=self._base()
        initial_first_pass_head=self.journal.status()["journal_head_sha256"]
        _need(claim_id in base, "ONLY_PREVIOUSLY_RESEARCHED_OPEN")
        with closing(self.journal._connect()) as con:
            effective,head,n=self._read(con,tasks,base)
        old=effective[claim_id]
        _need(old["proposed_decision"] == "KEEP_OPEN", "NOT_STILL_OPEN")
        task=tasks[claim_id]
        body_rows=evidence_retriever(copy.deepcopy(task))
        evidence=_evidence_summary(body_rows)
        old_sha={x["body_sha256"] for x in old["source_evidence"]}
        _need(any(x["body_sha256"] not in old_sha for x in evidence),
              "EVIDENCE_NOT_NEW")
        all_items=self.journal.docket["items"]
        index=next(i for i,x in enumerate(all_items) if x["claim_id"]==claim_id)
        before_item=all_items[index-1]["claim_id"] if index else None
        proposed=execute_chat_review_round(self.journal.docket,
             evidence_retriever=lambda _:body_rows,chat_reviewer=chat_reviewer,
             start_after=before_item,limit=1)
        _need(proposed["proposals_created"]==1 and
              proposed["proposals"][0]["claim_id"]==claim_id and
              proposed["knowledge_publication_authorized"] is False,
              "REVISIT_RESPONSE_MISMATCH")
        proposal=proposed["proposals"][0]
        # Keep serialized V167 source pins; never overwrite original history.
        event={"schema":SCHEMA,"seq":n+1,
               "root_docket_sha256":self.journal.docket["docket_sha256"],
               "claim_id":claim_id,"original_proposal_sha":digest(base[claim_id]),
               "preceding_proposal_sha":digest(old),"previous_head":head,
               "proposal":proposal}
        new_head=digest(event)
        con=self.journal._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            # Detect a concurrent V169 first-pass advance or a concurrent
            # V170 reopen before committing a new event.
            _need(self.journal.status()["journal_head_sha256"] ==
                  initial_first_pass_head,
                  "FIRST_PASS_ADVANCED_DURING_REVIEW")
            current,db_head,db_n=self._read(con,tasks,base)
            _need(db_head==head and db_n==n and
                  digest(current[claim_id])==digest(old),
                  "CONCURRENT_REVISIT")
            con.execute("INSERT INTO revisit_receipts VALUES(?,?,?,?,?,?,?)",
                        (n+1,claim_id,digest(base[claim_id]),digest(old),head,
                         _canonical(proposal),new_head))
            if _failure_injector:
                _failure_injector(n+1)
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()
        return self.status()

    def export_effective_unreleased_proposals(self):
        """V168-compatible *draft* with latest per-claim evidence proposal.

        Replaces no native row and authorizes no knowledge release. V168 still
        demands a secondary ChatGPT review and a full frozen V123/E4 replay.
        """
        receipt,tasks,base=self._base()
        with closing(self.journal._connect()) as con:
            effective,head,n=self._read(con,tasks,base)
        items=[effective[p["claim_id"]] for p in receipt["proposals"]]
        updated={**receipt,"proposals":items,
                 "candidate_proposals":sum(x["proposed_decision"]==
                     "CANDIDATE_NEEDS_NATIVE_REVIEW" for x in items),
                 "proposed_quarantines":sum(x["proposed_decision"]==
                     "QUARANTINE_PROPOSAL" for x in items)}
        updated.pop("proposal_receipt_sha256")
        _need(updated["native_v123_status_changed"] is False and
              updated["e5_authorized"] is False and
              updated["knowledge_publication_authorized"] is False,
              "FALSE_RELEASE")
        return {**updated,"proposal_receipt_sha256":digest(updated)}
