"""Synthetic real V6 snapshot replay, no owner DB or SRT in public CI."""
import copy
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from ire.v6.codec import json_digest, sha256
from ire.v6.source import parse_srt
from ire.v6.store import TransactionStore
from ire.v6.errors import QualityNotProven,InvalidInput
from v131_owner_db_readonly_acceptance import audit_readonly_owner_v6_snapshot,_file_hash

RAW=b'1\n00:00:00,000 --> 00:00:01,000\nFinancial education example only.\n'

def manifest():
    cues=parse_srt(RAW)
    return {'schema':'IRE_V6_SOURCE_PLAN_V1','video_id':'Lmnopqrstuv',
            'source_sha256':sha256(RAW),'cue_count':1,
            'scope':{'mode':'FULL_VIDEO','first_cue':1,'last_cue':1},
            'windows':[{'window_id':'W00001','first_cue':1,'last_cue':1,
                        'text_sha256':sha256(cues[0].text.encode())}]}

class V131OwnerReadonlySnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)/'private'
        self.folder.mkdir(mode=0o700)
        os.chmod(self.folder,0o700)
        self.path=self.folder/'test_operational.db'
        self.manifest=manifest()
        self.store=TransactionStore(self.path)
        result=self.store.create_scope(scope_id='scope_v131_test',video_id='Lmnopqrstuv',
                   source_sha256=sha256(RAW),manifest_sha256=json_digest(self.manifest),
                   command_id='genesis_v131_test')
        self.anchor={'schema':'IRE_V131_EXTERNAL_DB_SOURCE_ANCHOR_V1',
                 'source_kind':'OWNER_OPERATIONAL_CLOSED_SNAPSHOT',
                 'video_id':'Lmnopqrstuv','scope_id':'scope_v131_test',
                 'db_sha256':_file_hash(self.path),'head_sha256':result['event_sha256'],
                 'source_sha256':sha256(RAW),'manifest_sha256':json_digest(self.manifest)}
    def _check(self,**kw):
        args={'owner_external_anchor':self.anchor,'original_srt':RAW,
              'source_manifest':self.manifest}
        args.update(kw)
        return audit_readonly_owner_v6_snapshot(self.path,**args)
    def test_real_v6_genesis_replayed_without_mutating_db(self):
        before=_file_hash(self.path)
        result=self._check()
        self.assertEqual(result['scopes_replayed'],1)
        self.assertEqual(result['events_replayed'],1)
        self.assertFalse(result['operational_owner_identity_cryptographically_verified'])
        self.assertEqual(_file_hash(self.path),before)
    def test_synthetic_attested_flag_never_becomes_identity_certification(self):
        d=self._check(independently_attested_owner_signature=True)
        self.assertFalse(d['operational_owner_identity_cryptographically_verified'])
        self.assertFalse(d['owner_signature_accepted_as_evidence'])
        self.assertFalse(d['p0_go'])
    def test_missing_operational_snapshot_is_hold(self):
        with self.assertRaisesRegex(QualityNotProven,'OPERATIONAL_SNAPSHOT_MISSING'):
            audit_readonly_owner_v6_snapshot(self.folder/'missing.db',
                owner_external_anchor=self.anchor,original_srt=RAW,source_manifest=self.manifest)
    def test_isolated_staging_cannot_appear_operational(self):
        fake=copy.deepcopy(self.anchor);fake['source_kind']='ISOLATED_STAGING_V123'
        with self.assertRaisesRegex(QualityNotProven,'ISOLATED_STAGING_DB_NOT_OPERATIONAL'):
            self._check(owner_external_anchor=fake)
    def test_external_db_hash_forgery_blocked(self):
        a=copy.deepcopy(self.anchor);a['db_sha256']='0'*64
        with self.assertRaisesRegex(QualityNotProven,'DB_BYTES_MISMATCH'):
            self._check(owner_external_anchor=a)
    def test_external_head_drift_blocked(self):
        a=copy.deepcopy(self.anchor);a['head_sha256']='0'*64
        with self.assertRaisesRegex(QualityNotProven,'OWNER_EXPORTED_HEAD_MISMATCH'):
            self._check(owner_external_anchor=a)
    def test_wrong_original_bytes_blocked(self):
        with self.assertRaises((InvalidInput,QualityNotProven)):
            self._check(original_srt=RAW.replace(b'example',b'misleading'))
    def test_wal_sidecar_blocks_inconsistent_snapshot(self):
        (self.folder/'test_operational.db-wal').write_bytes(b'pending')
        with self.assertRaisesRegex(QualityNotProven,'LIVE_WAL_SNAPSHOT_NOT_STABLE'):
            self._check()
    def test_missing_anchors_blocked(self):
        with self.assertRaisesRegex(QualityNotProven,'INDEPENDENT_ANCHOR_REQUIRED'):
            self._check(owner_external_anchor={})
    def test_database_sha_changes_are_detected(self):
        with sqlite3.connect(self.path) as con:
            con.execute('CREATE TABLE dummy(v INTEGER)')
        with self.assertRaisesRegex(QualityNotProven,'LIVE_WAL_SNAPSHOT|DB_BYTES_MISMATCH'):
            self._check()

if __name__=='__main__': unittest.main()
