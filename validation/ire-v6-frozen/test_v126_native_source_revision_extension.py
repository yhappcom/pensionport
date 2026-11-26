"""Real SQLite synthetic full-source successor tests; never certify research truth."""
import copy
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from ire.v6.atomic_exchange import audit_host_atomic_exchange
from ire.v6.codec import canonical, json_digest, sha256, ZERO_SHA
from ire.v6.errors import QualityNotProven
from ire.v6.source import verify_source
from ire.v6.store import TransactionStore
from v123_chat_final_gate import SCHEMA, _is_finance
from v126_chat_approved_knowledge_store import PrivateKnowledgeStore

class NativeSourceExtensionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.d=Path(tmp.name)
        texts=['계획을 세운다.','기록을 보관한다.'];raw=('\n\n'.join(f'{i}\n00:00:0{i},000 --> 00:00:0{i},900\n{t}' for i,t in enumerate(texts,1))+'\n').encode()
        manifest=dict(schema='IRE_V6_SOURCE_PLAN_V1',video_id='ExtTest1234',source_sha256=sha256(raw),cue_count=2,scope=dict(mode='FULL_VIDEO',first_cue=1,last_cue=2),windows=[dict(window_id='W00001',first_cue=1,last_cue=2,text_sha256=sha256(' '.join(texts).encode()))])
        self.s=source=verify_source(raw,manifest,expected_source_sha256=sha256(raw),expected_manifest_sha256=json_digest(manifest))
        atoms=[dict(claim_id=f'C{i:05d}',owner_window_id='W00001',proposition=t,kind='FACT',stance='AFFIRMED',speaker='NARRATOR',source_refs=[dict(cue_index=i,quote=t)],context_cue_indices=[i],condition_cue_indices=[],exception_cue_indices=[],numeric_references=[],as_of=None) for i,t in enumerate(texts,1)]
        assert not any(_is_finance(a,source) for a in atoms)
        self.e=dict(schema='IRE_V6_HOST_ATOMIC_EXCHANGE_V1',video_id=source.video_id,source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,atoms=atoms,cue_dispositions=[dict(cue_index=i,cue_text_sha256=sha256(t.encode()),disposition='CANDIDATES',claim_ids=[f'C{i:05d}'],numeric_tokens=[],note='Synthetic source') for i,t in enumerate(texts,1)])
        self.audit=audit_host_atomic_exchange(source,self.e)
        # The repository has protected, immutable existing prior input bytes.
        root=next(p for p in [Path(__file__).resolve().parent,*Path(__file__).resolve().parents] if (p/'data/claims.jsonl').is_file() and (p/'ire/v5/advisory_knowledge').is_dir());base=root/'ire/v5/advisory_knowledge'
        self.k=dict(master116_bytes=(root/'data/claims.jsonl').read_bytes(),p4_22_bytes=(base/'p4_integrated_scoped_education22_20261106.json').read_bytes(),p4_7_bytes=(base/'p4_p3_incremental_education29_20261106.json').read_bytes(),relations=[dict(claim_id=a['claim_id'],candidate_source_sha256=source.source_sha256,target_kind='NONE',target_id=None,target_content_sha256=None,relationship='NOVEL_PENDING',rationale='Synthetic candidate.',independent_semantic_review_verified=False,personalized_action_approved=False) for a in atoms])
        inventory=canonical(dict(schema='IRE_V6_OWNER_INVENTORY_V1',entries=[dict(video_id=source.video_id,source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,cue_census_sha256=source.cue_census_sha256)]))
        self.store=TransactionStore(self.d/'source.db');self.ks=PrivateKnowledgeStore(self.d/'knowledge.db');sid='synthetic-scope'
        h=self.store.create_scope(scope_id=sid,video_id=source.video_id,source_sha256=source.source_sha256,manifest_sha256=source.manifest_sha256,command_id='init')
        h=self.store.attest_source(scope_id=sid,command_id='source',expected_head=h['event_sha256'],raw=raw,manifest=manifest)
        h=self.store.attest_owner_inventory(scope_id=sid,command_id='owner',expected_head=h['event_sha256'],raw=raw,manifest=manifest,inventory_bytes=inventory,expected_inventory_sha256=sha256(inventory))
        self.base=dict(scope_id=sid,raw=raw,manifest=manifest,inventory_bytes=inventory,expected_inventory_sha256=sha256(inventory),exchange=self.e,knowledge=self.k,window_models={'W00001':dict(schema='IRE_V6_ATOMIC_MODEL_V1',claims=[{**{x:a[x] for x in ('claim_id','owner_window_id','proposition','kind','source_refs')},'context_first_cue':i,'context_last_cue':i} for i,a in enumerate(atoms,1)])},window_reviews={'W00001':dict(schema='IRE_V6_STRUCTURAL_REVIEW_V1',review_scope='SOURCE_ANCHORS_ONLY',reviewed_claim_ids=['C00001','C00002'],independent_gold_verified=False)})
        self.first_args={**self.base,'run_id':'first','expected_head':h['event_sha256']};self.first=self.store.submit_host_atomic_batch(**self.first_args)
        self.relations=[dict(claim_id=a['claim_id'],atom_sha256=json_digest(a),relation='NEW',target_kind='NONE',target_id=None,private_chat_relation_review_sha256=sha256(a['claim_id'].encode())) for a in atoms]
        self.initial=self.ks.add_chat_final_batch(source,self.e,self.k,host_receipt=self.first,chat_review=self.review(self.first,{1}),source_store=self.store,official_evidence_bodies={},relation_decisions=self.relations,expected_knowledge_head=ZERO_SHA,original_host_batch_replay_args=self.first_args)
        self.oldrows=self.rows(); self.second_args={**self.base,'run_id':'second','expected_head':self.first['event_sha256']};self.second=self.store.submit_host_atomic_batch(**self.second_args)
        self.args=dict(host_receipt=self.second,chat_review=self.review(self.second,{1,2}),source_store=self.store,official_evidence_bodies={},relation_decisions=self.relations,expected_knowledge_head=self.initial['knowledge_head_sha256'],original_host_batch_replay_args=self.second_args)
    def review(self,h,accepted):
        s=self.s;note=sha256(b'synthetic review note');q=[];a=[];c=[]
        for i,atom in enumerate(self.e['atoms'],1):
            yes=i in accepted;ch=sha256(s.cues[i-1].text.encode())
            c.append(dict(cue_index=i,cue_text_sha256=ch,status='REVIEWED' if yes else 'EXCLUDED_FROM_RESEARCH',review_note_sha256=note))
            a.append(dict(claim_id=atom['claim_id'],atom_sha256=json_digest(atom),status='ACCEPT_FOR_RESEARCH' if yes else 'EXCLUDE_FROM_RESEARCH',speaker_stance_checked=yes,conditions_exceptions_checked=yes,numeric_period_checked=yes,counterexample_checked=yes,high_risk=False,financial_claim=False,finance_evidence_status='NOT_APPLICABLE',official_body_sha256=None,official_effective_as_of=None,financial_scope_checked=False,private_review_note_sha256=note))
            if not yes:q.append((dict(cue_index=i,cue_text_sha256=ch,reason_code='CONTEXT_INSUFFICIENT',private_review_note_sha256=note,source_first_context_checked=True),dict(claim_id=atom['claim_id'],atom_sha256=json_digest(atom),reason_code='CONTEXT_INSUFFICIENT',private_review_note_sha256=note,context_dependencies_checked=True)))
        r=dict(schema=SCHEMA,review_executor='CHATGPT_IN_CHAT',as_of='2026-11-26',source_sha256=s.source_sha256,manifest_sha256=s.manifest_sha256,host_event_sha256=h['event_sha256'],host_bundle_sha256=h['bundle_sha256'],atom_candidate_digest=self.audit['atom_candidate_digest'],cue_disposition_digest=self.audit['cue_disposition_digest'],blindness='PRIOR_EXPOSED',source_first_pass_completed=True,counterexample_pass_completed=True,disagreements_adjudicated=True,source_cues=c,atom_verdicts=a,unresolved_high_risk_omissions=0,unresolved_audio_visual=0,external_independent_certified=False,personalized_advice_approved=False,p0_go=False,review_private_evidence_sha256=note)
        if q:r['quarantine']=dict(schema='IRE_V123_SOURCE_PINNED_QUARANTINE_V1',source_sha256=s.source_sha256,manifest_sha256=s.manifest_sha256,review_executor='CHATGPT_IN_CHAT',cue_rows=[x[0] for x in q],atom_rows=[x[1] for x in q],audio_unverified_cue_indices=[],private_chat_quarantine_review_sha256=note)
        return r
    def rows(self):
        with closing(sqlite3.connect(self.ks.path)) as con:return (con.execute('select * from knowledge order by knowledge_id').fetchall(),con.execute('select * from events order by seq').fetchall())
    def add(self,**overrides):return self.ks.add_chat_final_batch(self.s,self.e,self.k,**{**self.args,'source_revision_extension':True,**overrides})
    def test_append_and_retry_keep_old_bytes(self):
        result=self.add();self.assertEqual(result['entries'],1);self.assertEqual(result['retained_entries'],1);self.assertFalse(result['p0_go']);rows,events=self.rows();self.assertIn(self.oldrows[0][0],rows);self.assertEqual(events[:1],self.oldrows[1]);self.assertEqual(len(events),2);self.assertTrue(self.add()['idempotent_replay']);self.assertEqual(self.rows(),(rows,events))
    def test_default_remains_strict(self):
        with self.assertRaisesRegex(QualityNotProven,'PARTIAL_OR_CHANGED_BATCH_NOT_ALLOWED'):self.add(source_revision_extension=False)
        self.assertEqual(self.rows(),self.oldrows)
    def test_drop_old_approval_fails(self):
        with self.assertRaisesRegex(QualityNotProven,'EXTENSION_PRIOR_APPROVAL_DROPPED_OR_CHANGED'):self.add(chat_review=self.review(self.second,{2}))
        self.assertEqual(self.rows(),self.oldrows)
    def test_changed_relation_note_fails(self):
        rd=copy.deepcopy(self.relations);rd[0]['private_chat_relation_review_sha256']='1'*64
        with self.assertRaisesRegex(QualityNotProven,'EXTENSION_PRIOR_ROW_OR_LINEAGE_DRIFT'):self.add(relation_decisions=rd)
        self.assertEqual(self.rows(),self.oldrows)
    def test_stale_knowledge_head_fails(self):
        with self.assertRaisesRegex(QualityNotProven,'KNOWLEDGE_EXPECTED_HEAD_CHANGED'):self.add(expected_knowledge_head=ZERO_SHA)
        self.assertEqual(self.rows(),self.oldrows)
    def test_revoked_claim_cannot_reactivate(self):
        self.ks.revoke(self.oldrows[0][0][0],chat_review_sha256='2'*64,expected_knowledge_head=self.ks.audit()['head_sha256']);old=self.rows()
        with self.assertRaisesRegex(QualityNotProven,'EXTENSION_PRIOR_APPROVAL_DROPPED_OR_CHANGED'):self.add(expected_knowledge_head=self.ks.audit()['head_sha256'])
        self.assertEqual(self.rows(),old)
    def test_extension_write_failure_rolls_back(self):
        original=self.ks._event
        def crash(*a,**kw):raise RuntimeError('injected write failure')
        self.ks._event=crash
        try:
            with self.assertRaisesRegex(RuntimeError,'injected write failure'):self.add()
        finally:self.ks._event=original
        self.assertEqual(self.rows(),self.oldrows);self.add()

    def revision_case(self):
        from ire.v6.chat_revision import compile_chat_atom_revision
        prior = copy.deepcopy(self.e)
        frame = {k:copy.deepcopy(prior['atoms'][1][k]) for k in (
            'proposition','kind','source_refs','context_cue_indices','condition_cue_indices',
            'exception_cue_indices','numeric_references','as_of')}
        frame.update(proposition='화자는 기록을 보관한다고 설명한다.',role='NARRATOR',
                     attribution='DIRECT',polarity='AFFIRMED',modality='ASSERTED',
                     correction=False,meaning_reason='Synthetic explicit source attribution.')
        change=dict(before=prior,edits=[dict(prior_claim_ids=['C00002'],
            replacements=[frame],reason='Synthetic source meaning revision.')],cue_reviews=[])
        revised=compile_chat_atom_revision(self.s,prior,edits=change['edits'],cue_reviews=[])
        self.e=revised['exchange'];self.audit=audit_host_atomic_exchange(self.s,self.e)
        self.k=copy.deepcopy(self.k);self.k['relations'][1]['claim_id']='C00003'
        self.relations=copy.deepcopy(self.relations);self.relations[1].update(
            claim_id='C00003',atom_sha256=json_digest(self.e['atoms'][1]))
        replay={**self.second_args,'run_id':'revision','expected_head':self.second['event_sha256'],
            'exchange':self.e,'knowledge':self.k,'window_models':revised['window_models'],
            'window_reviews':revised['window_reviews'],'chat_revision':change}
        host=self.store.submit_host_atomic_batch(**replay)
        self.args.update(host_receipt=host,chat_review=self.review(host,{1,2}),
            relation_decisions=self.relations,original_host_batch_replay_args={**replay,
                'revision_predecessor_replay_args':self.second_args})
        return host
    def test_exact_revision_predecessor_allows_additive_store(self):
        self.revision_case();got=self.add();self.assertEqual(got['entries'],1)
        self.assertEqual(got['retained_entries'],1);self.assertTrue(self.add()['idempotent_replay'])
        rows,events=self.rows();self.assertIn(self.oldrows[0][0],rows)
        self.assertEqual(events[:1],self.oldrows[1]);self.assertEqual(len(events),2)
    def test_exact_revision_predecessor_allows_fresh_staging(self):
        self.revision_case();d=self.d/'v128_staging_synthetic';d.mkdir()
        staging=PrivateKnowledgeStore(d/'staging.db',parent_staging_only=True)
        args={**self.args,'expected_knowledge_head':ZERO_SHA}
        self.assertEqual(staging.add_chat_final_batch(self.s,self.e,self.k,**args)['entries'],2)
        self.assertTrue(staging.add_chat_final_batch(self.s,self.e,self.k,**args)['idempotent_replay'])
    def test_revision_requires_predecessor(self):
        self.revision_case();args=copy.deepcopy(self.args['original_host_batch_replay_args'])
        del args['revision_predecessor_replay_args']
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_REVISION_REPLAY_INPUT_DRIFT'):
            self.add(original_host_batch_replay_args=args)
        self.assertEqual(self.rows(),self.oldrows)
    def test_revision_rejects_wrong_native_predecessor(self):
        self.revision_case();args=copy.deepcopy(self.args['original_host_batch_replay_args'])
        args['revision_predecessor_replay_args']=self.first_args
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_REVISION_PREDECESSOR_NOT_EXACT_REPLAY'):
            self.add(original_host_batch_replay_args=args)
        self.assertEqual(self.rows(),self.oldrows)
    def test_revision_rejects_changed_before(self):
        self.revision_case();args=copy.deepcopy(self.args['original_host_batch_replay_args'])
        args['chat_revision']['before']['atoms'][1]['proposition']+=' 변조'
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_REVISION_PREDECESSOR_INPUT_DRIFT'):
            self.add(original_host_batch_replay_args=args)
        self.assertEqual(self.rows(),self.oldrows)
    def test_revision_rejects_changed_review_reason(self):
        self.revision_case();args=copy.deepcopy(self.args['original_host_batch_replay_args'])
        args['chat_revision']['edits'][0]['reason']+=' 변조'
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_REVISION_NOT_EXACT_REPLAY'):
            self.add(original_host_batch_replay_args=args)
        self.assertEqual(self.rows(),self.oldrows)

    def second_revision_case(self):
        from ire.v6.chat_revision import compile_chat_atom_revision
        first_revision=self.revision_case()
        parent=self.args['original_host_batch_replay_args']
        prior=copy.deepcopy(self.e)
        frame={k:copy.deepcopy(prior['atoms'][1][k]) for k in (
            'proposition','kind','source_refs','context_cue_indices',
            'condition_cue_indices','exception_cue_indices','numeric_references','as_of')}
        frame.update(proposition='화자는 기록 보관을 설명한다.',role='NARRATOR',
            attribution='DIRECT',polarity='AFFIRMED',modality='ASSERTED',
            correction=False,meaning_reason='Synthetic second explicit source attribution.')
        change=dict(before=prior,edits=[dict(prior_claim_ids=['C00003'],
            replacements=[frame],reason='Synthetic second source revision.')],cue_reviews=[])
        revised=compile_chat_atom_revision(self.s,prior,edits=change['edits'],cue_reviews=[])
        self.e=revised['exchange'];self.audit=audit_host_atomic_exchange(self.s,self.e)
        self.k=copy.deepcopy(self.k);self.k['relations'][1]['claim_id']='C00004'
        self.relations=copy.deepcopy(self.relations);self.relations[1].update(
            claim_id='C00004',atom_sha256=json_digest(self.e['atoms'][1]))
        replay={**self.second_args,'run_id':'revision2','expected_head':first_revision['event_sha256'],
            'exchange':self.e,'knowledge':self.k,'window_models':revised['window_models'],
            'window_reviews':revised['window_reviews'],'chat_revision':change}
        host=self.store.submit_host_atomic_batch(**replay)
        self.args.update(host_receipt=host,chat_review=self.review(host,{1,2}),
            relation_decisions=self.relations,original_host_batch_replay_args={**replay,
                'revision_predecessor_replay_args':parent})
        return host
    def test_revision_of_revision_allows_additive_store_and_exact_retry(self):
        self.second_revision_case();got=self.add();self.assertEqual(got['entries'],1)
        self.assertEqual(got['retained_entries'],1);self.assertTrue(self.add()['idempotent_replay'])
        rows,events=self.rows();self.assertIn(self.oldrows[0][0],rows)
        self.assertEqual(events[:1],self.oldrows[1]);self.assertEqual(len(events),2)
    def test_revision_of_revision_allows_fresh_staging(self):
        self.second_revision_case();d=self.d/'v128_staging_synthetic_chain';d.mkdir()
        staging=PrivateKnowledgeStore(d/'staging.db',parent_staging_only=True)
        args={**self.args,'expected_knowledge_head':ZERO_SHA}
        self.assertEqual(staging.add_chat_final_batch(self.s,self.e,self.k,**args)['entries'],2)
        self.assertTrue(staging.add_chat_final_batch(self.s,self.e,self.k,**args)['idempotent_replay'])
    def test_revision_chain_rejects_missing_root_and_never_writes_source(self):
        self.second_revision_case();args=copy.deepcopy(self.args['original_host_batch_replay_args'])
        root=args['revision_predecessor_replay_args']['revision_predecessor_replay_args']
        root['run_id']='uncommitted'
        before=self.store.snapshot(self.base['scope_id'])
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_REVISION_PREDECESSOR_NOT_EXACT_REPLAY'):
            self.add(original_host_batch_replay_args=args)
        self.assertEqual(self.store.snapshot(self.base['scope_id']),before)
        self.assertEqual(self.rows(),self.oldrows)
    def test_revision_chain_rejects_tampered_historical_revision(self):
        self.second_revision_case();args=copy.deepcopy(self.args['original_host_batch_replay_args'])
        args['revision_predecessor_replay_args']['chat_revision']['edits'][0]['reason']+=' 변조'
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_REVISION_NOT_EXACT_REPLAY'):
            self.add(original_host_batch_replay_args=args)
        self.assertEqual(self.rows(),self.oldrows)
    def test_revision_chain_rejects_truncated_history(self):
        self.second_revision_case();args=copy.deepcopy(self.args['original_host_batch_replay_args'])
        del args['revision_predecessor_replay_args']['revision_predecessor_replay_args']
        with self.assertRaisesRegex(QualityNotProven,'SOURCE_HOST_REVISION_PREDECESSOR_INPUT_DRIFT'):
            self.add(original_host_batch_replay_args=args)
        self.assertEqual(self.rows(),self.oldrows)

if __name__=='__main__':unittest.main()
