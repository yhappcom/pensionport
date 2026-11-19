"""V176 source-first engine ↔ active ChatGPT collaboration (NO model API).

Engine owns work queue, original source, state, retry rules and idempotence.
ChatGPT in the currently running chat must explicitly author review responses;
this module never synthesizes semantic judgments, financial evidence or E4 PASS.

Private SQLite is source-pinned and append only. The program stops safely when
host interaction is missing rather than pretending to run an LLM in Python.
Final V123/V166 E4 remain separate frozen native approval authorities.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from collections import Counter

from ire.v6.source import parse_srt, verify_source
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.errors import InvalidInput

SCHEMA = "IRE_V176_ENGINE_CHAT_WORK_ITEM_V1"
COMMIT = "IRE_V176_CHAT_RETURNED_SOURCE_DECISION_V1"
REVISION = "IRE_V176_CHAT_RETURNED_CONTEXT_REVISION_V1"
EVIDENCE = "IRE_V176_CHAT_RETURNED_EVIDENCE_CANDIDATE_V1"
STATUS = {"ASSERTION", "QUESTION", "QUOTE", "NON_RESEARCH", "OPEN"}
KIND = {"FACT", "OPINION", "QUESTION", "HYPOTHETICAL", "RECOMMENDATION", "MATH", "ANECDOTE"}
ROLE = {"HOST", "GUEST", "NARRATOR", "SOURCE_BOOK_QUOTE", "UNKNOWN"}
ZERO = "0"*64


def _need(ok, code):
    if not ok:
        raise InvalidInput("V176_CHAT_ENGINE_"+code)


def _canon(obj):
    return canonical(obj)


def _digest(obj):
    return sha256(_canon(obj))


def make_original_plan(raw, video_id, *, expected_source_sha256, window_size=120):
    """Construct a complete 13-part technical plan, never source-derived approval."""
    _need(type(raw) is bytes and sha256(raw)==expected_source_sha256,
          "PINNED_OWNER_SRT_CHANGED")
    cues=parse_srt(raw)
    _need(1 <= window_size <= 1000, "WINDOW_SIZE")
    windows=[]
    for start in range(1,len(cues)+1,window_size):
        stop=min(len(cues),start+window_size-1)
        text=" ".join(c.text for c in cues[start-1:stop])
        windows.append({"window_id":f"W{len(windows)+1:05d}","first_cue":start,
                        "last_cue":stop,"text_sha256":sha256(text.encode("utf-8"))})
    manifest={"schema":"IRE_V6_SOURCE_PLAN_V1","video_id":video_id,
              "source_sha256":expected_source_sha256,"cue_count":len(cues),
              "scope":{"mode":"FULL_VIDEO","first_cue":1,"last_cue":len(cues)},
              "windows":windows}
    source=verify_source(raw,manifest,expected_source_sha256=expected_source_sha256,
                         expected_manifest_sha256=json_digest(manifest))
    return source,manifest


class EngineChatSession:
    """Hash-chained, private, source-pinned research coordinator."""
    def __init__(self, db_path, raw, video_id, *, owner_source_sha256,
                 window_size=120, expected_window_count=None):
        self.raw=raw
        self.source,self.manifest=make_original_plan(
            raw,video_id,expected_source_sha256=owner_source_sha256,
            window_size=window_size)
        if expected_window_count is not None:
            _need(len(self.source.primary_windows)==expected_window_count,
                  "OWNER_COMPLETE_WINDOW_CENSUS")
        self.path=Path(db_path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if not self.path.exists():
            fd=os.open(str(self.path),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
        self._init()

    def _connect(self):
        con=sqlite3.connect(self.path, timeout=20, isolation_level=None)
        con.row_factory=sqlite3.Row
        con.execute("PRAGMA busy_timeout=20000")
        return con

    def _init(self):
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute("CREATE TABLE IF NOT EXISTS config(k TEXT PRIMARY KEY, v TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, prev_sha TEXT NOT NULL, event_sha TEXT NOT NULL, payload TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS cue_reviews(cue_index INTEGER PRIMARY KEY, event_sha TEXT NOT NULL, disposition TEXT NOT NULL, record TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS cue_revisions(cue_index INTEGER PRIMARY KEY, prior_event_sha TEXT NOT NULL, event_sha TEXT NOT NULL, record TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS evidence_reviews(claim_key TEXT PRIMARY KEY, event_sha TEXT NOT NULL, record TEXT NOT NULL)")
            cfg={"schema":"IRE_V176_OWNER_PINNED_SESSION_V1",
                 "video_id":self.source.video_id,
                 "source_sha256":self.source.source_sha256,
                 "manifest_sha256":self.source.manifest_sha256,
                 "cue_census_sha256":self.source.cue_census_sha256,
                 "cues":len(self.source.cues),
                 "windows":len(self.source.primary_windows),"e5_enabled":False}
            old=con.execute("SELECT v FROM config WHERE k='owner'").fetchone()
            if old:
                _need(json.loads(old[0])==cfg,"WRONG_SOURCE_OR_PLAN_ON_RESUME")
            else:
                con.execute("INSERT INTO config VALUES('owner',?)",(_canon(cfg).decode("utf8"),))
            con.commit()
        except BaseException:
            con.rollback();raise
        finally:
            con.close()

    def _audit(self,con):
        prev=ZERO
        rows=con.execute("SELECT seq,prev_sha,event_sha,payload FROM events ORDER BY seq").fetchall()
        expected=1
        for row in rows:
            _need(row["seq"]==expected and row["prev_sha"]==prev,
                  "PRIVATE_JOURNAL_SEQUENCE_DRIFT")
            frame=json.loads(row["payload"])
            _need(_canon(frame).decode("utf8")==row["payload"] and
                  frame["seq"]==expected and frame["prev_sha"]==prev and
                  _digest(frame)==row["event_sha"], "PRIVATE_JOURNAL_TAMPER")
            prev=row["event_sha"];expected+=1
        reviewed=con.execute("SELECT cue_index,event_sha,disposition,record FROM cue_reviews ORDER BY cue_index").fetchall()
        revisions=con.execute("SELECT cue_index,prior_event_sha,event_sha,record FROM cue_revisions ORDER BY cue_index").fetchall()
        evidence_stored=con.execute("SELECT claim_key,event_sha,record FROM evidence_reviews ORDER BY claim_key").fetchall()
        source_rows={}
        revised_rows={}
        evidence_rows={}
        for event in rows:
            frame=json.loads(event["payload"])
            _need(frame.get("schema") in {COMMIT,REVISION,EVIDENCE} and
                  frame.get("source_sha256")==self.source.source_sha256 and
                  frame.get("manifest_sha256")==self.source.manifest_sha256 and
                  frame.get("review_executor")=="CHATGPT_IN_CHAT" and
                  frame.get("final_semantic_approval") is False and
                  frame.get("e4_approval") is False and
                  frame.get("e5_published") is False,
                  "UNRELEASED_EVIDENCE_FRAME_DRIFT")
            if frame["schema"]==COMMIT:
                for item in frame["responses"]:
                    i=item["cue_index"]
                    _need(type(i) is int and 1<=i<=len(self.source.cues) and
                          item["source_text_sha256"]==sha256(self.source.cues[i-1].text.encode("utf8")) and
                          i not in source_rows,"REPLAY_ORIGINAL_CUE_MISMATCH")
                    source_rows[i]=(event["event_sha"],item)
            elif frame["schema"]==REVISION:
                for item in frame["revisions"]:
                    i=item["cue_index"]
                    _need(i in source_rows and i not in revised_rows and
                          source_rows[i][1]["disposition"]=="OPEN" and
                          item["prior_review_event_sha256"]==source_rows[i][0] and
                          item["source_text_sha256"]==sha256(self.source.cues[i-1].text.encode("utf8")),
                          "REVISIT_PRIOR_SOURCE_DRIFT")
                    revised_rows[i]=(event["event_sha"],item)
            else:
                for item in frame["evidence_responses"]:
                    key=f"{item['cue_index']}:{item['claim_index']}"
                    _need(key not in evidence_rows and
                          item["final_financial_truth_certified"] is False,
                          "REPLAY_FALSE_FINANCE_APPROVAL_OR_DUPLICATE")
                    evidence_rows[key]=(event["event_sha"],item)
        _need(len(reviewed)==len(source_rows) and len(revisions)==len(revised_rows) and
              len(evidence_stored)==len(evidence_rows),
              "REVIEW_COUNT_DRIFT")
        for row in reviewed:
            idx=row["cue_index"]
            _need(idx in source_rows and row["event_sha"]==source_rows[idx][0] and
                  json.loads(row["record"])==source_rows[idx][1] and
                  row["disposition"]==source_rows[idx][1]["disposition"],
                  "REVIEW_ROW_DRIFT")
        for row in revisions:
            idx=row["cue_index"]
            _need(idx in revised_rows and row["prior_event_sha"]==source_rows[idx][0] and
                  row["event_sha"]==revised_rows[idx][0] and
                  json.loads(row["record"])==revised_rows[idx][1],
                  "REVISIT_ROW_DRIFT")
        for row in evidence_stored:
            key=row["claim_key"]
            _need(key in evidence_rows and
                  row["event_sha"]==evidence_rows[key][0] and
                  json.loads(row["record"])==evidence_rows[key][1],
                  "EVIDENCE_ROW_DRIFT")
        return prev,{**source_rows,**revised_rows}

    def progress(self):
        con=self._connect()
        try:
            head,reviewed=self._audit(con)
            count=Counter(x[1]["disposition"] for x in reviewed.values())
            per=[]
            for i,(wid,first,last) in enumerate(self.source.primary_windows,1):
                n=sum(first<=x<=last for x in reviewed)
                per.append({"segment_id":f"B{i:04d}","first_cue":first,"last_cue":last,
                            "reviewed":n,"total":last-first+1,
                            "complete":n==last-first+1})
            remaining=len(self.source.cues)-len(reviewed)
            evidence_count=con.execute("SELECT COUNT(*) FROM evidence_reviews").fetchone()[0]
            return {"schema":"IRE_V176_CHAT_ENGINE_PROGRESS_V1",
                    "source_sha256":self.source.source_sha256,
                    "manifest_sha256":self.source.manifest_sha256,
                    "checkpoint_head_sha256":head,
                    "cue_total":len(self.source.cues),"cue_reviewed":len(reviewed),
                    "cue_remaining":remaining,"dispositions":dict(count),
                    "segment_progress":per,"source_first_review_complete":remaining==0,
                    "unresolved_open_cues":count["OPEN"],
                    "source_evidence_proposals_recorded":evidence_count,
                    "v123_pass_claimed":False,"e4_pass_claimed":False,
                    "e5_knowledge_written":False}
        finally:
            con.close()

    def prepare(self, *, limit=6, context_radius=3):
        _need(type(limit) is int and 1<=limit<=20 and
              type(context_radius) is int and 0<=context_radius<=12,
              "CHALLENGE_SIZE")
        con=self._connect()
        try:
            head,reviewed=self._audit(con)
        finally:
            con.close()
        unreviewed=[i for i in range(1,len(self.source.cues)+1) if i not in reviewed]
        # After an entire segment's first pass, ask ChatGPT to revisit its
        # unresolved fragments with larger source context before proceeding.
        con=self._connect()
        try:
            revisited={r[0] for r in con.execute("SELECT cue_index FROM cue_revisions")}
        finally:
            con.close()
        for wid,seg_start,seg_end in self.source.primary_windows:
            pending=[i for i in unreviewed if seg_start<=i<=seg_end]
            if pending:
                break
            open_source=[i for i in range(seg_start,seg_end+1) if
                         i in reviewed and reviewed[i][1]["disposition"]=="OPEN" and
                         i not in revisited]
            if open_source:
                return self.prepare_context_revisit(open_source[:limit],
                                                    context_radius=max(6,context_radius))
            # Evidence verification is requested by the ENGINE at this stage.
            # ChatGPT must actively search; no fake URL/body SHA is supplied.
            evidence_task=self.prepare_evidence_request(wid, limit=limit)
            if evidence_task is not None:
                return evidence_task
        if not unreviewed:
            return {"schema":SCHEMA,"type":"SOURCE_FIRST_REVIEW_COMPLETE",
                    "owner_source_sha256":self.source.source_sha256,
                    "checkpoint_head_sha256":head,
                    "blocked_reason":"V123_AND_E4_SEPARATE_NATIVE_REPLAY_REQUIRED",
                    "e5_authorized":False}
        # Keep one contiguous segment in each turn; no accidental seam crossing.
        first=unreviewed[0];wid=self.source.owner(first)
        target=[i for i in unreviewed if self.source.owner(i)==wid][:limit]
        idxs=set()
        for i in target:
            idxs.update(range(max(1,i-context_radius),
                              min(len(self.source.cues),i+context_radius)+1))
        def view(i):
            c=self.source.cues[i-1]
            return {"cue_index":i,"text":c.text,
                    "source_text_sha256":sha256(c.text.encode("utf8"))}
        prepared={"schema":SCHEMA,"type":"CLASSIFY_SOURCE_CUES",
                  "owner_source_sha256":self.source.source_sha256,
                  "manifest_sha256":self.source.manifest_sha256,
                  "checkpoint_head_sha256":head,
                  "window_id":wid,"request_limit":limit, "context_radius":context_radius,
                  "target_cues":[view(i) for i in target],
                  "surrounding_context":[view(i) for i in sorted(idxs)],
                  "response_requirements":{
                    "every_target_exactly_once":True,
                    "disposition_values":sorted(STATUS),
                    "semantic_provenance_not_assumed":True,
                    "financial_evidence_must_be_separately_verified":True,
                    "no_auto_accept_or_e5":True}}
        return {**prepared,"challenge_sha256":_digest(prepared)}

    def prepare_context_revisit(self, cue_indices, *, context_radius=8):
        """Request explicit one-time repair of prior OPEN cues; no fake answers."""
        _need(type(context_radius) is int and 4<=context_radius<=20,
              "CONTEXT_REVISIT_RADIUS")
        con=self._connect()
        try:
            head,reviewed=self._audit(con)
            revisited={r[0] for r in con.execute("SELECT cue_index FROM cue_revisions")}
        finally:
            con.close()
        _need(type(cue_indices) is list and len(cue_indices)>0 and
              cue_indices==sorted(set(cue_indices)) and
              all(i in reviewed and reviewed[i][1]["disposition"]=="OPEN" and
                  i not in revisited for i in cue_indices),
              "REVISIT_REQUIRES_PENDING_OPEN")
        ix=set()
        for i in cue_indices:
            ix.update(range(max(1,i-context_radius),
                            min(len(self.source.cues),i+context_radius)+1))
        def cue(i):
            c=self.source.cues[i-1]
            return {"cue_index":i,"text":c.text,
                    "source_text_sha256":sha256(c.text.encode("utf8"))}
        obj={"schema":SCHEMA,"type":"RESOLVE_CONTEXT_CUES",
             "owner_source_sha256":self.source.source_sha256,
             "manifest_sha256":self.source.manifest_sha256,
             "checkpoint_head_sha256":head,
             "window_id":self.source.owner(cue_indices[0]),
             "context_radius":context_radius,
             "target_cues":[{**cue(i),
                             "prior_review_event_sha256":reviewed[i][0],
                             "prior_analysis":reviewed[i][1]["analysis"]}
                            for i in cue_indices],
             "surrounding_context":[cue(i) for i in sorted(ix)],
             "response_requirements":{
                 "new_context_evidence_required":True,
                 "one_revision_per_open_cue":True,
                 "if_still_unresolved_keep_open":True,
                 "never_auto_approve_financial_facts":True}}
        return {**obj,"challenge_sha256":_digest(obj)}

    def submit_context_revisit(self, challenge, answer):
        """Append one source-pinned CHATGPT correction per previously OPEN cue."""
        _need(type(challenge) is dict and challenge.get("type")=="RESOLVE_CONTEXT_CUES" and
              challenge.get("schema")==SCHEMA and
              challenge.get("challenge_sha256")==_digest({k:v for k,v in challenge.items()
                                                            if k!="challenge_sha256"}),
              "CONTEXT_CHALLENGE_TAMPER")
        _need(type(answer) is dict and set(answer)=={
                  "schema","challenge_sha256","review_executor","responses"} and
              answer["schema"]==REVISION and
              answer["review_executor"]=="CHATGPT_IN_CHAT" and
              answer["challenge_sha256"]==challenge["challenge_sha256"] and
              type(answer["responses"]) is list and
              len(answer["responses"])==len(challenge["target_cues"]),
              "CONTEXT_RESPONSE_SCHEMA")
        checked=[]
        valid_context={r["cue_index"] for r in challenge["surrounding_context"]}
        for expected,r in zip(challenge["target_cues"],answer["responses"]):
            base={"cue_index","source_text_sha256","disposition","analysis",
                  "speaker_role","claims","limitations_checked"}
            _need(type(r) is dict and set(r)==base|{
                      "prior_review_event_sha256","new_context_cue_indices","change_reason"} and
                  r["cue_index"]==expected["cue_index"] and
                  r["source_text_sha256"]==expected["source_text_sha256"] and
                  r["prior_review_event_sha256"]==expected["prior_review_event_sha256"] and
                  r["disposition"] in STATUS and r["speaker_role"] in ROLE and
                  type(r["claims"]) is list and type(r["limitations_checked"]) is bool and
                  type(r["analysis"]) is str and len(r["analysis"].strip())>=18 and
                  type(r["change_reason"]) is str and len(r["change_reason"].strip())>=20 and
                  type(r["new_context_cue_indices"]) is list and
                  r["new_context_cue_indices"]==sorted(set(r["new_context_cue_indices"])) and
                  set(r["new_context_cue_indices"])<=valid_context and
                  len(r["new_context_cue_indices"])>=2 and
                  (r["claims"]==[] if r["disposition"]!="ASSERTION" else
                   len(r["claims"])>=1),
                  "CONTEXT_REVISION_NOT_GROUNDED")
            if r["disposition"]=="ASSERTION":
                # Claim revisions still need normal cue/quote grounding; these
                # cannot be turned into native PASS by a context correction.
                for atom in r["claims"]:
                    _need(type(atom) is dict and
                          atom.get("kind") in KIND and
                          type(atom.get("quote")) is str and
                          atom["quote"] in self.source.cues[r["cue_index"]-1].text and
                          r["cue_index"] in atom.get("context_cue_indices",[]),
                          "CONTEXT_CLAIM_QUOTE_NOT_IN_SOURCE")
            checked.append(r)
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            head,effective=self._audit(con)
            _need(head==challenge["checkpoint_head_sha256"],"CONTEXT_HEAD_STALE")
            # Untrusted challenge hash alone is not enough. Rebuild from DB.
            expected_current=self.prepare_context_revisit(
                [r["cue_index"] for r in checked],
                context_radius=challenge["context_radius"])
            _need(challenge==expected_current,"CONTEXT_NOT_ENGINE_ISSUED")
            seq=con.execute("SELECT COUNT(*) FROM events").fetchone()[0]+1
            frame={"schema":REVISION,"seq":seq,"prev_sha":head,
                   "source_sha256":self.source.source_sha256,
                   "manifest_sha256":self.source.manifest_sha256,
                   "challenge_sha256":challenge["challenge_sha256"],
                   "review_executor":"CHATGPT_IN_CHAT","revisions":checked,
                   "final_semantic_approval":False,"e4_approval":False,
                   "e5_published":False}
            digest=_digest(frame)
            con.execute("INSERT INTO events VALUES(?,?,?,?)",
                        (seq,head,digest,_canon(frame).decode("utf8")))
            for row in checked:
                con.execute("INSERT INTO cue_revisions VALUES(?,?,?,?)",
                            (row["cue_index"],row["prior_review_event_sha256"],
                             digest,_canon(row).decode("utf8")))
            con.commit()
            return {"status":"CHAT_CONTEXT_REVISIT_COMMITTED_UNRELEASED",
                    "checkpoint_head_sha256":digest,
                    "cues_revisited":len(checked),"e4_approved":False,
                    "e5_published":False}
        except BaseException:
            if con.in_transaction:con.rollback()
            raise
        finally:
            con.close()

    def prepare_evidence_request(self, window_id, *, limit=6):
        """Issue ChatGPT a source-pinned official/publisher evidence search.

        This is never a primary-source verification or E4 approval itself.
        """
        con=self._connect()
        try:
            head,reviewed=self._audit(con)
            completed={r[0] for r in con.execute("SELECT claim_key FROM evidence_reviews")}
        finally:
            con.close()
        selected=[]
        for cue_index in sorted(reviewed):
            if self.source.owner(cue_index)!=window_id:continue
            row=reviewed[cue_index][1]
            if row["disposition"]!="ASSERTION":continue
            for claim_index,claim in enumerate(row["claims"]):
                key=f"{cue_index}:{claim_index}"
                if key in completed or not claim["needs_official_source"]:
                    continue
                selected.append({"cue_index":cue_index,
                                 "claim_index":claim_index,
                                 "claim_sha256":_digest(claim),
                                 "proposition":claim["proposition"],
                                 "source_original_quote":claim["quote"],
                                 "source_cue_sha256":row["source_text_sha256"],
                                 "high_risk":claim["high_risk"],
                                 "original_source_video_sha256":self.source.source_sha256})
                if len(selected)>=limit:break
            if len(selected)>=limit:break
        if not selected:return None
        frame={"schema":SCHEMA,"type":"SEARCH_ORIGINAL_PRIMARY_EVIDENCE",
               "checkpoint_head_sha256":head,
               "owner_source_sha256":self.source.source_sha256,
               "manifest_sha256":self.source.manifest_sha256,
               "window_id":window_id,
               "claim_evidence_tasks":selected,
               "response_requirements":{
                  "use_actual_chat_research_not_generated_fake_links":True,
                  "prefer_current_primary_issuer_and_dated_source":True,
                  "no_official_source_means_open":True,
                  "e4_must_independently_refetch_primary_bytes":True,
                  "e5_knowledge_release_blocked":True}}
        return {**frame,"challenge_sha256":_digest(frame)}

    def submit_evidence_proposals(self, challenge, answer):
        """Record unverified ChatGPT research metadata, never authoritative E4."""
        _need(type(challenge) is dict and
              challenge.get("type")=="SEARCH_ORIGINAL_PRIMARY_EVIDENCE" and
              challenge.get("schema")==SCHEMA and
              challenge.get("challenge_sha256")==_digest({k:v for k,v in challenge.items()
                                                            if k!="challenge_sha256"}),
              "OFFICIAL_EVIDENCE_CHALLENGE_TAMPER")
        _need(type(answer) is dict and set(answer)=={
               "schema","review_executor","challenge_sha256","responses"} and
              answer["schema"]==EVIDENCE and
              answer["review_executor"]=="CHATGPT_IN_CHAT" and
              answer["challenge_sha256"]==challenge["challenge_sha256"] and
              type(answer["responses"]) is list and
              len(answer["responses"])==len(challenge["claim_evidence_tasks"]),
              "OFFICIAL_EVIDENCE_RESPONSE_SCHEMA")
        for expected,row in zip(challenge["claim_evidence_tasks"],answer["responses"]):
            _need(type(row) is dict and set(row)=={
                "cue_index","claim_index","claim_sha256","evidence_state",
                "official_source_url","source_excerpt","effective_as_of",
                "context_and_counterexamples","original_body_sha256",
                "final_financial_truth_certified"} and
                row["cue_index"]==expected["cue_index"] and
                row["claim_index"]==expected["claim_index"] and
                row["claim_sha256"]==expected["claim_sha256"] and
                row["final_financial_truth_certified"] is False and
                row["evidence_state"] in {
                 "NOT_FOUND_KEEP_OPEN","SOURCE_FOUND_NEEDS_NATIVE_E4",
                 "CONTRADICTED_KEEP_OPEN","PUBLISHER_ATTRIBUTION_ONLY"} and
                type(row["context_and_counterexamples"]) is str and
                len(row["context_and_counterexamples"].strip())>=35,
                "OFFICIAL_EVIDENCE_NOT_GROUNDED")
            if row["evidence_state"]=="NOT_FOUND_KEEP_OPEN":
                _need(all(row[k] is None for k in
                          ("official_source_url","source_excerpt",
                           "effective_as_of","original_body_sha256")),
                      "MISSING_SOURCE_FAKED")
            else:
                from urllib.parse import urlsplit
                _need(type(row["official_source_url"]) is str and
                      urlsplit(row["official_source_url"]).scheme=="https" and
                      urlsplit(row["official_source_url"]).hostname is not None and
                      type(row["source_excerpt"]) is str and
                      len(row["source_excerpt"].strip())>=15 and
                      (row["effective_as_of"] is None or
                       type(row["effective_as_of"]) is str) and
                      (row["original_body_sha256"] is None or
                       type(row["original_body_sha256"]) is str and
                       len(row["original_body_sha256"])==64),
                      "INCOMPLETE_PRIMARY_SOURCE_CANDIDATE")
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            head,reviewed=self._audit(con)
            _need(head==challenge["checkpoint_head_sha256"],
                  "OFFICIAL_EVIDENCE_HEAD_STALE")
            current=self.prepare_evidence_request(challenge["window_id"],
                                                  limit=len(answer["responses"]))
            _need(current==challenge,"OFFICIAL_EVIDENCE_NOT_ENGINE_ISSUED")
            seq=con.execute("SELECT COUNT(*) FROM events").fetchone()[0]+1
            frame={"schema":EVIDENCE,"seq":seq,"prev_sha":head,
                   "source_sha256":self.source.source_sha256,
                   "manifest_sha256":self.source.manifest_sha256,
                   "challenge_sha256":challenge["challenge_sha256"],
                   "review_executor":"CHATGPT_IN_CHAT",
                   "evidence_responses":answer["responses"],
                   "final_semantic_approval":False,"e4_approval":False,
                   "e5_published":False}
            digest=_digest(frame)
            con.execute("INSERT INTO events VALUES(?,?,?,?)",
                        (seq,head,digest,_canon(frame).decode("utf8")))
            for r in answer["responses"]:
                con.execute("INSERT INTO evidence_reviews VALUES(?,?,?)",
                            (f"{r['cue_index']}:{r['claim_index']}",digest,
                             _canon(r).decode("utf8")))
            con.commit()
            return {"status":"CHAT_EVIDENCE_PROPOSAL_RECORDED_NOT_E4_APPROVED",
                    "checkpoint_head_sha256":digest,
                    "evidence_tasks_recorded":len(answer["responses"]),
                    "native_primary_bytes_verified":False,
                    "e4_approved":False,"e5_published":False}
        except BaseException:
            if con.in_transaction:con.rollback()
            raise
        finally:
            con.close()

    def submit(self,challenge,answer):
        _need(type(challenge) is dict and challenge.get("schema")==SCHEMA and
              challenge.get("type")=="CLASSIFY_SOURCE_CUES" and
              type(challenge.get("challenge_sha256")) is str and
              challenge["challenge_sha256"]==_digest({k:v for k,v in challenge.items()
                                                      if k!="challenge_sha256"}),
              "CHALLENGE_TAMPER")
        _need(type(answer) is dict and set(answer)=={
                "schema","challenge_sha256","review_executor","responses"} and
              answer["schema"]==COMMIT and
              answer["review_executor"]=="CHATGPT_IN_CHAT" and
              answer["challenge_sha256"]==challenge["challenge_sha256"] and
              type(answer["responses"]) is list,
              "CHAT_RESPONSE_SCHEMA")
        target=challenge["target_cues"]
        _need(len(answer["responses"])==len(target),"BATCH_RESPONSE_INCOMPLETE")
        checked=[]
        for expected,r in zip(target,answer["responses"]):
            _need(type(r) is dict and set(r)=={
                "cue_index","source_text_sha256","disposition","analysis",
                "speaker_role","claims","limitations_checked"},
                "CUE_RESPONSE_FIELDS")
            idx=r["cue_index"]
            c=self.source.cues[idx-1] if type(idx) is int and 1<=idx<=len(self.source.cues) else None
            _need(c is not None and idx==expected["cue_index"] and
                  r["source_text_sha256"]==expected["source_text_sha256"] and
                  r["source_text_sha256"]==sha256(c.text.encode("utf8")) and
                  r["disposition"] in STATUS and r["speaker_role"] in ROLE and
                  type(r["limitations_checked"]) is bool and
                  type(r["analysis"]) is str and len(r["analysis"].strip())>=18 and
                  type(r["claims"]) is list,
                  "REVIEW_NOT_SOURCE_BOUND")
            if r["disposition"]=="ASSERTION":
                _need(len(r["claims"])>=1,"ASSERTION_WITHOUT_ATOM")
            else:
                _need(r["claims"]==[],"NON_ASSERTION_HAS_ATOMS")
            for claim in r["claims"]:
                _need(type(claim) is dict and set(claim)=={
                    "proposition","kind","quote","context_cue_indices",
                    "conditions","exceptions","numeric_tokens","high_risk",
                    "needs_official_source"},"ATOMIC_CLAIM_FIELDS")
                _need(type(claim["proposition"]) is str and len(claim["proposition"].strip())>=8 and
                      claim["kind"] in KIND and type(claim["quote"]) is str and
                      len(claim["quote"].strip())>=3 and
                      " ".join(claim["quote"].split()) in " ".join(c.text.split()) and
                      type(claim["context_cue_indices"]) is list and
                      idx in claim["context_cue_indices"] and
                      claim["context_cue_indices"]==sorted(set(claim["context_cue_indices"])) and
                      all(type(n) is int and 1<=n<=len(self.source.cues)
                          for n in claim["context_cue_indices"]) and
                      all(type(claim[z]) is list and all(type(v) is str for v in claim[z])
                          for z in ("conditions","exceptions","numeric_tokens")) and
                      all(type(claim[z]) is bool for z in ("high_risk","needs_official_source")),
                      "ATOM_NOT_GROUNDED_IN_ORIGINAL")
                for tok in claim["numeric_tokens"]:
                    _need(tok in c.text,"ATOM_NUMBER_NOT_IN_CUE")
            checked.append(r)
        _need(challenge["owner_source_sha256"]==self.source.source_sha256 and
              challenge["manifest_sha256"]==self.source.manifest_sha256 and
              challenge["window_id"]==self.source.owner(target[0]["cue_index"]) and
              type(challenge.get("request_limit")) is int and
              type(challenge.get("context_radius")) is int,
              "CHALLENGE_OWNER_DRIFT")
        # The hash included in the challenge is not an HMAC. Rebuild a real
        # engine-issued challenge from pinned original bytes and live state;
        # otherwise a forged client may self-hash arbitrary target/context.
        live_head=self.progress()["checkpoint_head_sha256"]
        if live_head==challenge["checkpoint_head_sha256"]:
            _need(self.prepare(limit=challenge["request_limit"],
                               context_radius=challenge["context_radius"]) == challenge,
                  "CHALLENGE_NOT_ENGINE_ISSUED")
        con=self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            head,reviewed=self._audit(con)
            # An identical already committed response returns its receipt safely.
            # Other stale, concurrent or changed responses fail closed.
            if head!=challenge["checkpoint_head_sha256"]:
                prior=con.execute("SELECT event_sha,payload FROM events WHERE seq=?",
                                  (len(con.execute("SELECT seq FROM events").fetchall()),)).fetchone()
                if prior is not None:
                    p=json.loads(prior["payload"])
                    if (p["challenge_sha256"]==answer["challenge_sha256"] and
                        p["responses"]==checked):
                        con.rollback()
                        return {"status":"IDEMPOTENT_CHAT_REVIEW_REPLAY",
                                "checkpoint_head_sha256":prior["event_sha"],
                                "cues_committed":len(checked),"e4_approved":False}
                _need(False,"STALE_OR_CONFLICTING_CHAT_REVIEW")
            _need(all(r["cue_index"] not in reviewed for r in checked),
                  "CUE_ALREADY_REVIEWED")
            seq=con.execute("SELECT COUNT(*) FROM events").fetchone()[0]+1
            frame={"seq":seq,"prev_sha":head,"schema":COMMIT,
                   "source_sha256":self.source.source_sha256,
                   "manifest_sha256":self.source.manifest_sha256,
                   "challenge_sha256":answer["challenge_sha256"],
                   "review_executor":answer["review_executor"],
                   "responses":checked,"final_semantic_approval":False,
                   "e4_approval":False,"e5_published":False}
            digest=_digest(frame)
            con.execute("INSERT INTO events VALUES(?,?,?,?)",
                        (seq,head,digest,_canon(frame).decode("utf8")))
            for row in checked:
                con.execute("INSERT INTO cue_reviews VALUES(?,?,?,?)",
                            (row["cue_index"],digest,row["disposition"],
                             _canon(row).decode("utf8")))
            con.commit()
            return {"status":"CHAT_SOURCE_REVIEW_COMMITTED_UNRELEASED",
                    "checkpoint_head_sha256":digest,
                    "cues_committed":len(checked),"e4_approved":False,
                    "e5_published":False}
        except BaseException:
            if con.in_transaction:con.rollback()
            raise
        finally:
            con.close()

    def compile_native_v6_stage(self):
        """Replay the ORIGINAL frozen V6 audit over active-chat decisions.

        Unreviewed cues stay UNRESOLVED and no item is accepted by V123/E4.
        The native audit is structural only, never a quality or recall score.
        """
        from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
        con=self._connect()
        try:
            head,reviewed=self._audit(con)
        finally:
            con.close()
        cue_rows=[]
        atoms=[]
        unsafely_typed=[]
        next_id=1
        for cue in self.source.cues:
            idx=cue.index
            current=reviewed.get(idx)
            text_hash=sha256(cue.text.encode("utf8"))
            if current is None or current[1]["disposition"]=="OPEN":
                disposition="UNRESOLVED"
                note="ChatGPT 의미 검토 대기; 원문 자동 승인 금지"
                ids=[]
            elif current[1]["disposition"] in {"QUESTION","QUOTE","NON_RESEARCH"}:
                disposition="NO_ATOM"
                note="ChatGPT 비주장 또는 질문 예비 분류; 사실 승인 아님"
                ids=[]
            else:
                record=current[1]
                safe=all(c["kind"]!="ANECDOTE" for c in record["claims"])
                if not safe:
                    unsafely_typed.append(idx)
                    disposition="UNRESOLVED"
                    note="사례 발화를 동결 V6의 정식 유형으로 단정할 수 없음"
                    ids=[]
                else:
                    disposition="CANDIDATES"
                    note="ChatGPT 신규 주장 후보; V123/E4 아직 미승인"
                    ids=[]
                    for claim in record["claims"]:
                        cid=f"C{next_id:05d}";next_id+=1
                        ids.append(cid)
                        context=claim["context_cue_indices"]
                        number_refs=[]
                        for j in context:
                            for tok in NUMBER.findall(self.source.cues[j-1].text):
                                number_refs.append({"cue_index":j,"token":tok})
                        # Unknown stance is deliberate: the submitted text
                        # is not a valid final ChatGPT source meaning review.
                        atoms.append({
                            "claim_id":cid,"owner_window_id":self.source.owner(idx),
                            "proposition":claim["proposition"],
                            "kind":claim["kind"],"stance":"UNRESOLVED",
                            "speaker":"UNKNOWN",
                            "source_refs":[{"cue_index":idx,"quote":claim["quote"]}],
                            "context_cue_indices":context,
                            "condition_cue_indices":[],"exception_cue_indices":[],
                            "numeric_references":number_refs,"as_of":None,
                        })
            cue_rows.append({"cue_index":idx,"cue_text_sha256":text_hash,
                             "disposition":disposition,"claim_ids":ids,
                             "numeric_tokens":NUMBER.findall(cue.text),"note":note})
        exchange={"schema":"IRE_V6_HOST_ATOMIC_EXCHANGE_V1",
                  "video_id":self.source.video_id,
                  "source_sha256":self.source.source_sha256,
                  "manifest_sha256":self.source.manifest_sha256,
                  "cue_dispositions":cue_rows,"atoms":atoms}
        audit=audit_host_atomic_exchange(self.source,exchange)
        summary={"schema":"IRE_V176_NATIVE_V6_STAGED_UNRELEASED_V1",
                 "source_sha256":self.source.source_sha256,
                 "checkpoint_head_sha256":head,
                 "native_v6_audit":audit,
                 "pending_original_cues":audit["unresolved_cues"],
                 "unsupported_claim_cues":unsafely_typed,
                 "v123_invoked":False,"e4_invoked":False,"e5_invoked":False,
                 "final_approval":False}
        return exchange, summary

    def run_host_cycle(self, chat_host, *, max_batches=50, batch_size=8,
                       context_radius=3):
        """One live host invocation can drive multiple engine↔ChatGPT rounds.

        `chat_host` MUST be supplied by an interactive ChatGPT host. This
        function does not call a model or fake responses. When the host cannot
        keep running, the private journal keeps the exact continuation point.
        """
        _need(callable(chat_host),"NO_CHAT_HOST_CONNECTED")
        _need(type(max_batches) is int and 1<=max_batches<=10000,
              "HOST_BATCH_BUDGET")
        transcripts=[]
        for _ in range(max_batches):
            challenge=self.prepare(limit=batch_size,
                                   context_radius=context_radius)
            if challenge["type"]=="SOURCE_FIRST_REVIEW_COMPLETE":
                break
            answer=chat_host(challenge)
            _need(type(answer) is dict,"HOST_CHAT_RESULT_NOT_SUPPLIED")
            if challenge["type"]=="RESOLVE_CONTEXT_CUES":
                receipt=self.submit_context_revisit(challenge,answer)
                n=receipt["cues_revisited"]
            elif challenge["type"]=="SEARCH_ORIGINAL_PRIMARY_EVIDENCE":
                receipt=self.submit_evidence_proposals(challenge,answer)
                n=receipt["evidence_tasks_recorded"]
            else:
                receipt=self.submit(challenge,answer)
                n=receipt["cues_committed"]
            transcripts.append({"challenge_sha256":challenge["challenge_sha256"],
                                "commit_head_sha256":receipt["checkpoint_head_sha256"],
                                "cues_processed":n,"task_type":challenge["type"]})
        progress=self.progress()
        return {"schema":"IRE_V176_REAL_CHAT_HOST_CYCLE_V1",
                "calls_completed":len(transcripts),"receipts":transcripts,
                "reviewed_original_cues":progress["cue_reviewed"],
                "remaining_original_cues":progress["cue_remaining"],
                "all_source_cues_reviewed":progress["source_first_review_complete"],
                "all_meaning_approved":False,"e4_approved":False,
                "e5_published":False}

    def work_summary(self):
        p=self.progress()
        p["next_required_step"]=("CHAT_SOURCE_REVIEW" if p["cue_remaining"] else
                                  "FINAL_NATIVE_V6_V123_E4_REVIEW_REQUIRED")
        p["research_finished"]=False
        return p