"""V183 private E3 source-only second-pass audit; NO model API, NO E4 path.

This is a *comparison* engine: the first pass is a pinned V176 owner's journal,
while an active ChatGPT reviewer authors the separate source-only second pass.
It cannot prove cognitive independence, automatically decide semantic equivalence,
or certify E3/V123 approval. No first-pass claims are sent to the reviewer.
"""
from __future__ import annotations
import json
import os
import sqlite3
import stat
from contextlib import contextmanager
from pathlib import Path
from collections import Counter

from ire.v6.codec import sha256
from ire.v6.errors import InvalidInput
from ire.v6.atomic_exchange import NUMBER
from v176_chat_engine_loop import EngineChatSession, _canon, _digest, STATUS, ROLE, KIND, ZERO

PACKET_SCHEMA="IRE_V183_E3_SOURCE_ONLY_SECOND_PASS_PACKET_V1"
ANSWER_SCHEMA="IRE_V183_E3_CHAT_SOURCE_ONLY_SECOND_PASS_RESPONSE_V1"
EVENT_SCHEMA="IRE_V183_E3_SECOND_PASS_APPEND_ONLY_EVENT_V1"
CONFIG_SCHEMA="IRE_V183_E3_PINNED_FIRST_TURN_JOURNAL_V1"
RESPONSE_KEYS={"cue_index","source_text_sha256","disposition","analysis",
               "speaker_role","claims","limitations_checked"}
CLAIM_KEYS={"proposition","kind","quote","context_cue_indices","conditions",
            "exceptions","numeric_tokens","high_risk","needs_official_source"}


def _need(ok, reason):
    if not ok:
        raise InvalidInput("V183_E3_"+reason)


class E3TwoTurnAudit:
    """Second-pass evidence journal, isolated from V176 primary journal."""
    def __init__(self, engine: EngineChatSession, audit_db, *,
                 expected_owner_head, create=False):
        self.engine=engine
        self.path=Path(audit_db)
        self.expected_owner_head=expected_owner_head
        _need(type(expected_owner_head) is str and len(expected_owner_head)==64
              and all(c in '0123456789abcdef' for c in expected_owner_head),
              "OWNER_HEAD_PIN_REQUIRED")
        owner_progress=engine.progress()
        _need(owner_progress["checkpoint_head_sha256"]==expected_owner_head,
              "OWNER_ORIGINAL_JOURNAL_CHANGED")
        _need(owner_progress["source_first_review_complete"],
              "FIRST_TURN_SOURCE_CENSUS_NOT_COMPLETE")
        _need(not engine.path.is_symlink() and engine.path.is_file() and
              not (stat.S_IMODE(engine.path.stat().st_mode)&0o077),
              "FIRST_TURN_OWNER_DB_PERMISSIONS")
        self.config={"schema":CONFIG_SCHEMA,"source_sha256":engine.source.source_sha256,
                     "manifest_sha256":engine.source.manifest_sha256,
                     "video_id":engine.source.video_id,
                     "cue_total":len(engine.source.cues),
                     "original_journal_head_sha256":expected_owner_head,
                     "e4_approved":False,"e5_published":False}
        _need(not self.path.is_symlink(),"AUDIT_DB_SYMLINK_REJECTED")
        if self.path.exists():
            _need(not create,"EXISTING_AUDIT_DB_MUST_RESUME")
            _need(self.path.is_file() and not (stat.S_IMODE(self.path.stat().st_mode)&0o077),
                  "AUDIT_DB_PRIVATE_PERMISSIONS_REQUIRED")
        else:
            _need(create,"NO_AUDIT_DB_AUTO_RESET")
            self.path.parent.mkdir(parents=True,exist_ok=True)
            fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            os.close(fd)
        with self._db() as db:
            db.execute("CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, prev_sha TEXT NOT NULL, event_sha TEXT NOT NULL, payload TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS judgments (cue_index INTEGER PRIMARY KEY, event_sha TEXT NOT NULL, record TEXT NOT NULL)")
            row=db.execute("SELECT value FROM config WHERE id=1").fetchone()
            if row:
                _need(json.loads(row[0])==self.config,"FIRST_TURN_PIN_CHANGED_ON_RESUME")
            else:
                db.execute("INSERT INTO config VALUES (1,?)",(_canon(self.config).decode(),))

    @contextmanager
    def _db(self):
        con=sqlite3.connect(self.path,timeout=20)
        con.row_factory=sqlite3.Row
        try:
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def _owner_snapshot(self):
        _need(self.engine.progress()["checkpoint_head_sha256"]==self.expected_owner_head,
              "STALE_ORIGINAL_SOURCE_JOURNAL")
        with self.engine._connect() as con:
            _, rows=self.engine._audit(con)
        return rows

    def _audit(self, db):
        previous=ZERO
        from_events={}
        for index,r in enumerate(db.execute("SELECT * FROM events ORDER BY seq"),1):
            frame=json.loads(r['payload'])
            _need(r['seq']==index and r['prev_sha']==previous
                  and _canon(frame).decode()==r['payload'] and
                  r['event_sha']==_digest(frame) and frame['seq']==index
                  and frame['prev_sha']==previous
                  and frame['schema']==EVENT_SCHEMA
                  and frame['source_sha256']==self.engine.source.source_sha256
                  and frame['owner_journal_head_sha256']==self.expected_owner_head
                  and frame['e3_semantic_approval'] is False
                  and frame['e4_approval'] is False
                  and frame['e5_published'] is False,
                  "AUDIT_CHAIN_TAMPER_OR_AUTHORITY_FORGERY")
            for ans in frame['responses']:
                idx=ans['cue_index']
                _need(idx not in from_events and 1<=idx<=len(self.engine.source.cues)
                      and ans['source_text_sha256']==sha256(self.engine.source.cues[idx-1].text.encode()),
                      "SECOND_TURN_SOURCE_OR_DUPLICATE")
                from_events[idx]=(r['event_sha'],ans)
            previous=r['event_sha']
        rows=db.execute("SELECT * FROM judgments").fetchall()
        _need(len(rows)==len(from_events),"SECOND_PASS_ROW_COUNT_TAMPER")
        for r in rows:
            _need(r['cue_index'] in from_events and
                  r['event_sha']==from_events[r['cue_index']][0] and
                  json.loads(r['record'])==from_events[r['cue_index']][1],
                  "SECOND_PASS_ROW_TAMPER")
        return previous,from_events

    def _cue(self, i):
        cue=self.engine.source.cues[i-1]
        return {"cue_index":i,"text":cue.text,
                "source_text_sha256":sha256(cue.text.encode())}

    def prepare(self, *, cue_indices=None,limit=12,context_radius=6):
        """No prior decisions, first-pass atoms, E4 evidence, or source-derived hints."""
        _need(type(limit) is int and 1<=limit<=20 and
              type(context_radius) is int and 2<=context_radius<=12,
              "SECOND_PASS_PACKET_SIZE")
        self._owner_snapshot()
        with self._db() as db:
            audit_head,stored=self._audit(db)
        if cue_indices is None:
            # Deterministic sequential census; no cherry-picked quality score.
            pending=[i for i in range(1,len(self.engine.source.cues)+1) if i not in stored]
            if not pending:
                return {"schema":PACKET_SCHEMA,"type":"E3_SECOND_PASS_SOURCE_CENSUS_COMPLETE_UNAPPROVED",
                        "source_sha256":self.engine.source.source_sha256,
                        "owner_journal_head_sha256":self.expected_owner_head,
                        "audit_head_sha256":audit_head,"e3_quality_certified":False,
                        "e4_approved":False,"e5_published":False}
            selected=[]
            first_segment=self.engine.source.owner(pending[0])
            for i in pending:
                if self.engine.source.owner(i)!=first_segment or len(selected)>=limit:
                    break
                selected.append(i)
            mode="SEQUENTIAL_CENSUS"
        else:
            _need(type(cue_indices) is list and len(cue_indices)>0 and
                  len(cue_indices)<=limit and
                  all(type(i) is int for i in cue_indices) and
                  cue_indices==sorted(set(cue_indices)) and
                  all(1<=i<=len(self.engine.source.cues) and i not in stored for i in cue_indices),
                  "SOURCE_TARGET_SELECTION_INVALID")
            selected=cue_indices
            mode="TARGETED_NONREPRESENTATIVE"
        ctx=set()
        for i in selected:
            ctx.update(range(max(1,i-context_radius),min(len(self.engine.source.cues),i+context_radius)+1))
        packet={"schema":PACKET_SCHEMA,"type":"E3_SECOND_PASS_SOURCE_ONLY",
                "owner_source_sha256":self.engine.source.source_sha256,
                "manifest_sha256":self.engine.source.manifest_sha256,
                "owner_journal_head_sha256":self.expected_owner_head,
                "audit_head_sha256":audit_head,"selection_mode":mode,
                "cue_indices":selected,"context_radius":context_radius,
                "target_cues":[self._cue(i) for i in selected],
                "surrounding_context":[self._cue(i) for i in sorted(ctx)],
                "first_pass_decisions_in_packet":False,
                "independent_chat_identity_proven":False,
                "response_requirements":{"all_targets_reviewed_once":True,
                     "source_quote_and_number_pinned":True,
                     "no_prior_claims_or_disposition_visible":True,
                     "not_independent_gold":True,
                     "no_e3_e4_automatic_approval":True}}
        return {**packet,"challenge_sha256":_digest(packet)}

    def _validate(self, packet, answer):
        _need(type(answer) is dict and set(answer)=={
                "schema","challenge_sha256","review_executor","responses"} and
              answer.get("schema")==ANSWER_SCHEMA and
              answer.get("review_executor")=="CHATGPT_IN_CHAT" and
              answer.get("challenge_sha256")==packet["challenge_sha256"] and
              type(answer.get("responses")) is list and
              len(answer["responses"])==len(packet["target_cues"]),
              "SECOND_TURN_ANSWER_SCHEMA")
        context={x['cue_index'] for x in packet['surrounding_context']}
        for expected,r in zip(packet['target_cues'],answer['responses']):
            _need(type(r) is dict and set(r)==RESPONSE_KEYS and
                  type(r.get('cue_index')) is int and
                  r['cue_index']==expected['cue_index'] and
                  r['source_text_sha256']==expected['source_text_sha256'] and
                  r['disposition'] in STATUS and r['speaker_role'] in ROLE and
                  type(r['analysis']) is str and len(r['analysis'].strip())>=18 and
                  type(r['limitations_checked']) is bool and
                  type(r['claims']) is list and
                  (len(r['claims'])>=1 if r['disposition']=='ASSERTION' else not r['claims']),
                  "SECOND_TURN_CUE_SEMANTIC_SCHEMA")
            cue=self.engine.source.cues[r['cue_index']-1]
            if r['disposition']=='ASSERTION':
                for atom in r['claims']:
                    _need(type(atom) is dict and set(atom)==CLAIM_KEYS and
                          type(atom['proposition']) is str and len(atom['proposition'].strip())>=8 and
                          atom['kind'] in KIND and
                          type(atom['quote']) is str and len(atom['quote'].strip())>=3 and
                          ' '.join(atom['quote'].split()) in ' '.join(cue.text.split()) and
                          type(atom['context_cue_indices']) is list and
                          atom['context_cue_indices']==sorted(set(atom['context_cue_indices'])) and
                          r['cue_index'] in atom['context_cue_indices'] and
                          set(atom['context_cue_indices'])<=context and
                          all(type(atom[k]) is list and
                              all(type(s) is str for s in atom[k])
                              for k in ('conditions','exceptions','numeric_tokens')) and
                          type(atom['high_risk']) is bool and
                          type(atom['needs_official_source']) is bool and
                          all(n in cue.text for n in atom['numeric_tokens']) and
                          set(NUMBER.findall(atom['proposition']))<=set(
                              x for n in atom['context_cue_indices']
                              for x in NUMBER.findall(self.engine.source.cues[n-1].text)),
                          "SECOND_TURN_UNGROUNDED_CLAIM_OR_NUMERIC")

    @staticmethod
    def _compare(original,second):
        disagreements=[]
        if original['disposition']!=second['disposition']:
            disagreements.append('DISPOSITION')
        if original['speaker_role']!=second['speaker_role']:
            disagreements.append('SPEAKER_ROLE')
        aa=original['claims'];bb=second['claims']
        if len(aa)!=len(bb):
            disagreements.append('ATOMIC_CLAIM_COUNT')
        for key in ('kind','proposition','quote','context_cue_indices','conditions',
                    'exceptions','numeric_tokens','high_risk','needs_official_source'):
            if [x[key] for x in aa]!=[x[key] for x in bb]:
                disagreements.append('CLAIM_'+key.upper())
        # Spelling/paraphrase differences are review cues, NOT proven errors.
        return disagreements

    def submit(self, packet,answer):
        _need(type(packet) is dict and packet.get('type')=='E3_SECOND_PASS_SOURCE_ONLY'
              and packet.get('schema')==PACKET_SCHEMA and
              packet.get('challenge_sha256')==_digest({k:v for k,v in packet.items()
                                                       if k!='challenge_sha256'}),
              'SOURCE_ONLY_PACKET_TAMPER')
        # Self-hash is forgeable: rebuild the entire packet against current bytes.
        current=self.prepare(cue_indices=packet['cue_indices'] if
                  packet['selection_mode']=='TARGETED_NONREPRESENTATIVE' else None,
                  limit=len(packet['cue_indices']),context_radius=packet['context_radius'])
        _need(current==packet,'PACKET_NOT_ISSUED_BY_ENGINE_OR_STALE')
        self._validate(packet,answer)
        first=self._owner_snapshot()
        comparisons=[]
        for item in answer['responses']:
            initial=first[item['cue_index']][1]
            differences=self._compare(initial,item)
            comparisons.append({'cue_index':item['cue_index'],
                                'difference_codes':differences,
                                'exact_semantic_field_match':not differences,
                                'adjudication_required':bool(differences) or item['disposition']=='OPEN'})
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            head,stored=self._audit(db)
            _need(head==packet['audit_head_sha256'] and
                  all(i not in stored for i in packet['cue_indices']),
                  'SECOND_TURN_STALE_OR_ALREADY_REVIEWED')
            seq=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]+1
            frame={'schema':EVENT_SCHEMA,'seq':seq,'prev_sha':head,
                   'source_sha256':self.engine.source.source_sha256,
                   'owner_journal_head_sha256':self.expected_owner_head,
                   'challenge_sha256':packet['challenge_sha256'],
                   'selection_mode':packet['selection_mode'],
                   'review_executor':'CHATGPT_IN_CHAT','responses':answer['responses'],
                   'comparisons':comparisons,'e3_semantic_approval':False,
                   'e4_approval':False,'e5_published':False}
            digest=_digest(frame)
            db.execute('INSERT INTO events VALUES(?,?,?,?)',
                       (seq,head,digest,_canon(frame).decode()))
            for r in answer['responses']:
                db.execute('INSERT INTO judgments VALUES (?,?,?)',
                           (r['cue_index'],digest,_canon(r).decode()))
            db.commit()
        return {'schema':'IRE_V183_E3_SECOND_PASS_COMPARE_UNAPPROVED_V1',
                'reviewed':len(comparisons),'exact_field_matches':sum(
                    x['exact_semantic_field_match'] for x in comparisons),
                'disagreement_or_open_cues':[x['cue_index'] for x in comparisons
                                               if x['adjudication_required']],
                'comparison_items':comparisons,'audit_head_sha256':digest,
                'e3_quality_certified':False,'e4_approved':False,'e5_published':False}

    def status(self):
        original=self._owner_snapshot()
        with self._db() as db:
            head,reviews=self._audit(db)
            n=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        issues={};counts=Counter()
        for idx,(_,second) in reviews.items():
            codes=self._compare(original[idx][1],second)
            for code in codes:counts[code]+=1
            if codes or second['disposition']=='OPEN':
                issues[idx]=codes or ['OPEN_REMAINS_UNRESOLVED']
        stage=self.engine.compile_native_v6_stage()[1]['semantic_projection_gate']
        return {'schema':'IRE_V183_E3_SECOND_TURN_QUALITY_HOLD_V1',
                'original_source_sha256':self.engine.source.source_sha256,
                'pinned_original_journal_head_sha256':self.expected_owner_head,
                'second_review_audit_head_sha256':head,
                'second_review_events':n,
                'second_reviewed_cues':len(reviews),
                'total_cues':len(self.engine.source.cues),
                'unreviewed_cues':len(self.engine.source.cues)-len(reviews),
                'exact_field_matches':sum(not self._compare(original[i][1],r[1])
                                          for i,r in reviews.items()),
                'adjudication_required_count':len(issues),
                'disagreement_codes_count':dict(counts),
                'adjudication_queue':[{"cue_index":i,"reasons":issues[i]}
                                       for i in sorted(issues)],
                'selection_is_independent_gold':False,
                'separate_chat_identity_verified':False,
                'semantics_complete':False,
                'source_qualifier_unmapped_claims':stage['unprojected_claims'],
                'e3_quality_certified':False,'v123_approved':False,
                'e4_approved':False,'e5_published':False}