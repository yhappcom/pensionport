"""V40 private-source semantic staging: V39 replay BEFORE atomic checkpoint.

This validates source and ChatGPT annotation custody. It does NOT certify
financial truth, independent gold or V6 atomic claim approval. No private
transcript or review prose is written to the SQLite checkpoint or receipt.
"""
from __future__ import annotations
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from .codec import IDENT, VIDEO, json_digest, require_hash, require_identifier
from .errors import ConcurrentHeadChanged, IdempotencyConflict, InvalidInput, LedgerCorrupted
from .host_semantic_custody_v39 import audit_host_semantic_custody_v39

ZERO_SHA = '0' * 64
SCHEMA = 'IRE_V6_V40_CHAT_SEMANTIC_CHECKPOINT_V1'
MAX_WINDOWS_PER_TURN = 4
MAX_CANDIDATES_PER_TURN = 160


def _commit_hash(r):
    return json_digest({
        'schema': SCHEMA,
        'video_id': r['video_id'],
        'original_source_sha256': r['original_source_sha256'],
        'run_id': r['run_id'],
        'sequence': r['sequence'],
        'expected_head_sha256': r['expected_head_sha256'],
        'semantic_receipt_sha256': r['semantic_receipt_sha256'],
        'window_scope_sha256': r['window_scope_sha256'],
        'window_ids_json': r['window_ids_json'],
        'reviewed_windows': r['reviewed_windows'],
        'reviewed_cues': r['reviewed_cues'],
        'reviewed_candidates': r['reviewed_candidates'],
        'semantic_notes_including_questions': r['semantic_notes_including_questions'],
    })


class PrivateSemanticCheckpointV40:
    """Owner-private SQLite staging ledger, separate from V6 atomic-model ledger.

    The source and per-window SHA pins MUST be independent V37 commitments.
    Never store the private database in a public Git checkout.
    """
    def __init__(self, db_path):
        self.db_path = str(Path(db_path))
        with closing(self._connect()) as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS v40_checkpoints(
                    run_id TEXT PRIMARY KEY,
                    video_id TEXT NOT NULL,
                    original_source_sha256 TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    expected_head_sha256 TEXT NOT NULL,
                    new_head_sha256 TEXT NOT NULL,
                    semantic_receipt_sha256 TEXT NOT NULL,
                    window_scope_sha256 TEXT NOT NULL,
                    window_ids_json TEXT NOT NULL,
                    reviewed_windows INTEGER NOT NULL,
                    reviewed_cues INTEGER NOT NULL,
                    reviewed_candidates INTEGER NOT NULL,
                    semantic_notes_including_questions INTEGER NOT NULL,
                    UNIQUE(video_id,original_source_sha256,sequence)
                );
                CREATE TABLE IF NOT EXISTS v40_window_ownership(
                    video_id TEXT NOT NULL,
                    original_source_sha256 TEXT NOT NULL,
                    window_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    PRIMARY KEY(video_id,original_source_sha256,window_id),
                    FOREIGN KEY(run_id) REFERENCES v40_checkpoints(run_id)
                );
            """)

    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=5, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA busy_timeout=5000')
        return con

    def _before_commit(self, stage):
        """Test-only deterministic rollback injection hook."""
        return None

    def snapshot(self, video_id, original_source_sha256):
        video_id = require_identifier(video_id, VIDEO, 'V40_VIDEO_ID')
        require_hash(original_source_sha256, 'V40_ORIGINAL_SHA')
        with closing(self._connect()) as con:
            row = con.execute("""SELECT sequence,new_head_sha256 FROM v40_checkpoints
                WHERE video_id=? AND original_source_sha256=?
                ORDER BY sequence DESC LIMIT 1""",
                (video_id,original_source_sha256)).fetchone()
            count = con.execute("""SELECT COUNT(*) FROM v40_window_ownership
                WHERE video_id=? AND original_source_sha256=?""",
                (video_id,original_source_sha256)).fetchone()[0]
        return {'schema':SCHEMA, 'video_id':video_id,
                'original_source_sha256':original_source_sha256,
                'head_sha256':row['new_head_sha256'] if row else ZERO_SHA,
                'checkpoint_count':row['sequence'] if row else 0,
                'reviewed_window_count':count,
                'financial_truth_independently_verified':False,
                'research_complete':False,'p0_go':False}

    def submit(self, *, run_id, expected_head, original_srt_bytes,
               source_pins, window_pins, host_rows):
        """Single bounded semantic-review turn: V39 audit then SQLite ACID.

        Legacy V6 host_batch is intentionally NOT called: its atom schemas
        represent different work from provisional V33 speech candidates.
        """
        require_identifier(run_id, IDENT, 'V40_RUN_ID')
        if len(run_id)>48:
            raise InvalidInput('V40_RUN_ID_TOO_LONG')
        require_hash(expected_head, 'V40_EXPECTED_HEAD')
        if (type(source_pins) is not list or len(source_pins)!=1 or
            type(window_pins) is not list or
            not 1<=len(window_pins)<=MAX_WINDOWS_PER_TURN):
            raise InvalidInput('V40_EXACT_ONE_VIDEO_BOUNDED_WINDOWS_REQUIRED')
        vid = source_pins[0].get('video_id') if type(source_pins[0]) is dict else None
        if (type(original_srt_bytes) is not dict or
            set(original_srt_bytes)!={vid} or
            any(type(w) is not dict or w.get('video_id')!=vid for w in window_pins)):
            raise InvalidInput('V40_SINGLE_OWNER_SOURCE_VIDEO_SCOPE_REQUIRED')
        audited = audit_host_semantic_custody_v39(
            original_srt_bytes,source_pins,window_pins,host_rows)
        if (audited['original_video_count']!=1 or
            audited['selected_original_window_count']!=len(window_pins) or
            audited['exact_v33_candidates_source_pinned']>MAX_CANDIDATES_PER_TURN or
            audited['host_reviewed_candidates']!=audited['exact_v33_candidates_source_pinned'] or
            any(audited[k] is not False for k in (
                'financial_fact_truth_certified','reviewer_independence_verified',
                'true_precision_recall_measured','p0_go'))):
            raise InvalidInput('V40_UNBOUNDED_OR_FALSELY_CERTIFIED_SEMANTIC_REVIEW')
        source_sha = source_pins[0]['original_srt_sha256']
        windows = sorted(p['window_id'] for p in window_pins)
        if len(set(windows))!=len(windows):
            raise InvalidInput('V40_DUPLICATE_WINDOW_IDS')
        meta = {'video_id':vid, 'original_source_sha256':source_sha,
                'run_id':run_id,'expected_head_sha256':expected_head,
                'semantic_receipt_sha256':audited['receipt_sha256'],
                'window_scope_sha256':json_digest(audited['selected_window_pins']),
                'window_ids_json':json.dumps(windows,separators=(',',':')),
                'reviewed_windows':len(windows),
                'reviewed_cues':audited['selected_original_cues'],
                'reviewed_candidates':audited['host_reviewed_candidates'],
                'semantic_notes_including_questions':audited['chat_review_items_including_questions']}
        con=self._connect()
        try:
            con.execute('BEGIN IMMEDIATE')
            prior=con.execute('SELECT * FROM v40_checkpoints WHERE run_id=?',
                              (run_id,)).fetchone()
            if prior is not None:
                if any(prior[k]!=v for k,v in meta.items()):
                    raise IdempotencyConflict('V40_REUSED_RUN_ID_WITH_DIFFERENT_SEMANTIC_REVIEW')
                if prior['new_head_sha256']!=_commit_hash(dict(prior)):
                    raise LedgerCorrupted('V40_PREVIOUS_CHECKPOINT_HASH_CHANGED')
                owned=con.execute('SELECT window_id FROM v40_window_ownership WHERE run_id=?',
                                  (run_id,)).fetchall()
                if sorted(x['window_id'] for x in owned)!=windows:
                    raise LedgerCorrupted('V40_PREVIOUS_WINDOW_OWNERSHIP_CHANGED')
                con.rollback()
                return self._public_receipt(dict(prior),idempotent=True)
            latest=con.execute("""SELECT sequence,new_head_sha256 FROM v40_checkpoints
                WHERE video_id=? AND original_source_sha256=?
                ORDER BY sequence DESC LIMIT 1""",(vid,source_sha)).fetchone()
            head=latest['new_head_sha256'] if latest else ZERO_SHA
            if head!=expected_head:
                raise ConcurrentHeadChanged('V40_SEMANTIC_CHECKPOINT_EXPECTED_HEAD_STALE')
            seen=con.execute("""SELECT window_id FROM v40_window_ownership
                WHERE video_id=? AND original_source_sha256=?""",
                (vid,source_sha)).fetchall()
            if set(windows)&{x['window_id'] for x in seen}:
                raise IdempotencyConflict('V40_SOURCE_WINDOW_ALREADY_CHECKPOINTED')
            meta['sequence']=latest['sequence']+1 if latest else 1
            meta['new_head_sha256']=_commit_hash(meta)
            con.execute("""INSERT INTO v40_checkpoints(
                run_id,video_id,original_source_sha256,sequence,
                expected_head_sha256,new_head_sha256,semantic_receipt_sha256,
                window_scope_sha256,window_ids_json,reviewed_windows,reviewed_cues,
                reviewed_candidates,semantic_notes_including_questions)
                VALUES (:run_id,:video_id,:original_source_sha256,:sequence,
                :expected_head_sha256,:new_head_sha256,:semantic_receipt_sha256,
                :window_scope_sha256,:window_ids_json,:reviewed_windows,:reviewed_cues,
                :reviewed_candidates,:semantic_notes_including_questions)""",meta)
            for wid in windows:
                con.execute("""INSERT INTO v40_window_ownership
                    (video_id,original_source_sha256,window_id,run_id)
                    VALUES (?,?,?,?)""",(vid,source_sha,wid,run_id))
            self._before_commit('AFTER_CHECKPOINT_INSERT')
            con.commit()
            return self._public_receipt(meta,idempotent=False)
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    @staticmethod
    def _public_receipt(row, *, idempotent):
        return {'schema':SCHEMA,'video_id':row['video_id'],
                'source_sha256':row['original_source_sha256'],
                'run_id':row['run_id'],'sequence':row['sequence'],
                'event_sha256':row['new_head_sha256'],
                'semantic_custody_sha256':row['semantic_receipt_sha256'],
                'reviewed_windows':row['reviewed_windows'],
                'reviewed_cues':row['reviewed_cues'],
                'reviewed_candidates':row['reviewed_candidates'],
                'chat_review_notes':row['semantic_notes_including_questions'],
                'idempotent_replay':idempotent,
                'atomic_checkpoint_committed':True,
                'structural_custody_only':True,
                'financial_truth_independently_verified':False,
                'knowledge_auto_merge':False,
                'personal_advice_approved':False,
                'p0_go':False}

    def verify_chain(self,video_id,original_source_sha256):
        """Recheck hash-chain and exact per-run source-window ownership."""
        video_id=require_identifier(video_id,VIDEO,'V40_VIDEO_ID')
        require_hash(original_source_sha256,'V40_ORIGINAL_SHA')
        with closing(self._connect()) as con:
            rows=[dict(r) for r in con.execute("""SELECT * FROM v40_checkpoints
                WHERE video_id=? AND original_source_sha256=?
                ORDER BY sequence""",(video_id,original_source_sha256))]
            own=[dict(r) for r in con.execute("""SELECT * FROM v40_window_ownership
                WHERE video_id=? AND original_source_sha256=?""",
                (video_id,original_source_sha256))]
        head=ZERO_SHA
        counted=0
        for number,row in enumerate(rows,1):
            if (row['sequence']!=number or
                row['expected_head_sha256']!=head or
                row['new_head_sha256']!=_commit_hash(row)):
                raise LedgerCorrupted('V40_SEMANTIC_CHECKPOINT_CHAIN_TAMPERED')
            used=[x for x in own if x['run_id']==row['run_id']]
            if (len(used)!=row['reviewed_windows'] or
                sorted(x['window_id'] for x in used)!=json.loads(row['window_ids_json'])):
                raise LedgerCorrupted('V40_SEMANTIC_WINDOW_OWNERSHIP_CENSUS_DRIFT')
            head=row['new_head_sha256']
            counted+=len(used)
        if counted!=len(own):
            raise LedgerCorrupted('V40_ORPHAN_SEMANTIC_WINDOW_OWNERSHIP')
        return {'schema':SCHEMA,'video_id':video_id,
                'original_source_sha256':original_source_sha256,
                'head_sha256':head,'checkpoint_count':len(rows),
                'reviewed_window_count':counted,
                'all_window_receipts_integrity_passed':True,
                'semantic_truth_certified':False,'research_complete':False,'p0_go':False}
