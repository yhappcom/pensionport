"""Synthetic positive native formal transition, with real protected prior bytes.

No real investment fact or semantic accuracy certified by these tests.
"""
import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from ire.v6.codec import canonical, json_digest, sha256
from ire.v6.source import verify_source
from ire.v6.store import TransactionStore
from ire.v6.errors import InvalidInput, QualityNotProven, ConcurrentHeadChanged
from ire.v6.host_quarantine_preflight import TYPED_STAGING_SCHEMA, audit_host_quarantine_preflight
from ire.v6.semantic_authoring_protocol import compile_authoring
from ire.v6.tests.test_semantic_authoring_protocol import packet


def build_fixture(d, support=False):
    texts=['동일한 조건이라면','계획을 비교한다.'] if support else ['차분하게 계획을 세운다.']
    count=len(texts);body=texts[-1];prop=' '.join(texts)
    raw=('\n\n'.join(f'{i}\n00:00:0{i},000 --> 00:00:0{i},900\n{t}' for i,t in enumerate(texts,1))+'\n').encode()
    manifest=dict(schema='IRE_V6_SOURCE_PLAN_V1',video_id='AbCdEf12345',source_sha256=sha256(raw),cue_count=count,
        scope=dict(mode='FULL_VIDEO',first_cue=1,last_cue=count),windows=[dict(window_id='W00001',first_cue=1,last_cue=count,text_sha256=sha256(prop.encode()))])
    source=verify_source(raw,manifest,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(manifest))
    a=packet(source);t=a['atoms'][0];t['node']['predicate']=prop;t['quantities']=[]
    if support:
        t['node']['direct']=[[2,0,len(body)]]
        a['segments'][0]['status']='SUPPORT'
        t['relations']=[dict(type='CONDITION',premise=[[1,0,len(texts[0])]],consequent=[[2,0,len(body)]],reason='Exact synthetic premise.')]
    _,r=compile_authoring(source,a)
    n=dict(claim_id='C00001',owner_window_id='W00001',proposition=prop,kind='FACT',stance='CONDITIONAL' if support else 'AFFIRMED',speaker='NARRATOR',source_refs=[dict(cue_index=count,quote=body)],context_cue_indices=list(range(1,count+1)),condition_cue_indices=[1] if support else [],exception_cue_indices=[],numeric_references=[],as_of=None)
    e=dict(schema='IRE_V6_HOST_ATOMIC_EXCHANGE_V1',video_id=source.video_id,source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,atoms=[n],cue_dispositions=[dict(cue_index=i,cue_text_sha256=sha256(t.encode()),disposition='CANDIDATES' if i==count else 'NO_ATOM',claim_ids=['C00001'] if i==count else [],numeric_tokens=[],note='Synthetic source.') for i,t in enumerate(texts,1)])
    l=dict(schema=TYPED_STAGING_SCHEMA,source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,review_executor='CHATGPT_IN_CHAT',authored=a,authoring_receipt=r,exchange_sha256=json_digest(e),projection_rows=[dict(typed_id='A00001',claim_id='C00001',typed_sha256=json_digest(a['atoms'][0]),native_sha256=json_digest(n),note='Synthetic direct projection.')],support_rows=[dict(cue_index=1,cue_sha256=sha256(texts[0].encode()),claim_ids=['C00001'],reason='Entire premise is explicitly retained.')] if support else [],quarantine_cues=[],quarantine_atoms=[],p0_go=False)
    assert audit_host_quarantine_preflight(source,e,l)['open_numeric_occurrences']==0
    inventory=canonical(dict(schema='IRE_V6_OWNER_INVENTORY_V1',entries=[dict(video_id=source.video_id,source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,cue_census_sha256=source.cue_census_sha256)]))
    root=Path(__file__).resolve().parents[3];base=root/'ire/v5/advisory_knowledge'
    k=dict(master116_bytes=(root/'data/claims.jsonl').read_bytes(),p4_22_bytes=(base/'p4_integrated_scoped_education22_20261106.json').read_bytes(),p4_7_bytes=(base/'p4_p3_incremental_education29_20261106.json').read_bytes(),relations=[dict(claim_id='C00001',candidate_source_sha256=source.source_sha256,target_kind='NONE',target_id=None,target_content_sha256=None,relationship='NOVEL_PENDING',rationale='Synthetic candidate relation only.',independent_semantic_review_verified=False,personalized_action_approved=False)])
    model=dict(schema='IRE_V6_ATOMIC_MODEL_V1',claims=[{**{x:n[x] for x in ('claim_id','owner_window_id','proposition','kind','source_refs')},'context_first_cue':count,'context_last_cue':count}])
    wreview=dict(schema='IRE_V6_STRUCTURAL_REVIEW_V1',review_scope='SOURCE_ANCHORS_ONLY',reviewed_claim_ids=['C00001'],independent_gold_verified=False)
    store=TransactionStore(Path(d)/'state.db');sid='synthetic-scope'
    x=store.create_scope(scope_id=sid,video_id=source.video_id,source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,command_id='init')
    x=store.attest_source(scope_id=sid,command_id='source',expected_head=x['event_sha256'],raw=raw,manifest=manifest)
    x=store.attest_owner_inventory(scope_id=sid,command_id='owner',expected_head=x['event_sha256'],raw=raw,manifest=manifest,inventory_bytes=inventory,expected_inventory_sha256=sha256(inventory))
    kw=dict(scope_id=sid,raw=raw,manifest=manifest,inventory_bytes=inventory,expected_inventory_sha256=sha256(inventory),exchange=e,knowledge=k,window_models={'W00001':model},window_reviews={'W00001':wreview})
    h=store.submit_host_atomic_batch(**kw,run_id='typed',expected_head=x['event_sha256'],quarantine_preflight=l)
    return store,source,e,l,kw,h


class FormalTransitionTests(unittest.TestCase):
    def setUp(self):
        self.d=tempfile.TemporaryDirectory();self.addCleanup(self.d.cleanup)
        self.store,self.s,self.e,self.l,self.kw,self.h=build_fixture(self.d.name)

    def promote(self,**changes):
        kw={**self.kw,'run_id':'formal','expected_head':self.h['event_sha256'],'typed_predecessor':self.h['event_sha256'],'formal_typed_transition':True};kw.update(changes)
        return self.store.submit_host_atomic_batch(**kw)

    def events(self):
        from contextlib import closing
        with closing(sqlite3.connect(self.store.path)) as c:
            return c.execute('select event_sha256,event_json from events order by sequence').fetchall()

    def test_native_transition_and_retry(self):
        old=self.events();h=self.promote();new=self.events()
        self.assertEqual(new[:len(old)],old);self.assertEqual(len(new),len(old)+3)
        self.assertTrue(h['formal_typed_transition_pin']['formal_input_only']);self.assertFalse(h['formal_typed_transition_pin']['research_export_authorized'])
        self.assertTrue(self.promote()['idempotent_replay']);self.assertEqual(new,self.events())

    def test_no_implicit_promotion(self):
        old=self.events()
        with self.assertRaisesRegex(InvalidInput,'TYPED_SUCCESSOR_PREDECESSOR_REQUIRED'):self.promote(formal_typed_transition=False)
        self.assertEqual(old,self.events())

    def test_prior_bundle_changed(self):
        k=copy.deepcopy(self.kw['knowledge']);k['relations'][0]['rationale']='A different synthetic relation rationale.'
        old=self.events()
        with self.assertRaisesRegex(InvalidInput,'FORMAL_PRIOR_BUNDLE_DRIFT'):self.promote(knowledge=k)
        self.assertEqual(old,self.events())

    def test_reserved_marker_not_generic_write(self):
        old=self.events()
        with self.assertRaisesRegex(InvalidInput,'HOST_BATCH_RESERVED_MARKER'):
            self.store.submit(scope_id=self.kw['scope_id'],command_id='forge',expected_head=self.h['event_sha256'],kind='REVIEW_PROPOSED',payload={'review':{'schema':'IRE_V6_HOST_BATCH_COMMIT_MARKER_V3'}})
        self.assertEqual(old,self.events())

    def test_wrong_predecessor(self):
        old=self.events()
        with self.assertRaisesRegex(InvalidInput,'HOST_FORMAL_PREDECESSOR_REQUIRED'):self.promote(typed_predecessor='0'*64)
        self.assertEqual(old,self.events())

    def test_crash_rolls_back_whole_batch(self):
        old=self.events();original=self.store._write_event
        def fail(*a,**kw):
            if kw['kind']=='REVIEW_PROPOSED':raise RuntimeError('synthetic crash')
            return original(*a,**kw)
        self.store._write_event=fail
        try:
            with self.assertRaisesRegex(RuntimeError,'synthetic crash'):self.promote()
        finally:self.store._write_event=original
        self.assertEqual(old,self.events());self.promote()
