"""Generic semantic revision and native numeric span regression tests.

Invented examples only. Structural processing is not semantic gold.
"""
import copy
import unittest

from ire.v6.atomic_exchange import NUMBER, audit_host_atomic_exchange
from ire.v6.chat_revision import compile_chat_atom_revision
from ire.v6.codec import json_digest, sha256
from ire.v6.errors import InvalidInput
from ire.v6.source import parse_srt, verify_source


def fixture(lines):
    raw = '\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},700\n{line}'
                     for i,line in enumerate(lines,1)).encode()
    cues = parse_srt(raw)
    manifest = {'schema':'IRE_V6_SOURCE_PLAN_V1','video_id':'AbCdEf12345',
                'source_sha256':sha256(raw),'cue_count':len(cues),
                'scope':{'mode':'FULL_VIDEO','first_cue':1,'last_cue':len(cues)},
                'windows':[{'window_id':f'W{n:05d}','first_cue':i,
                            'last_cue':min(i+1,len(cues)),
                            'text_sha256':sha256(' '.join(c.text for c in cues[i-1:min(i+1,len(cues))]).encode())}
                           for n,i in enumerate(range(1,len(cues)+1,2),1)]}
    return verify_source(raw,manifest,expected_source_sha256=sha256(raw),
                         expected_manifest_sha256=json_digest(manifest))


def old_atom(src,cid,indices,proposition,*,context=None,conditions=None,exceptions=None,numeric=None):
    return {'claim_id':cid,'owner_window_id':src.owner(indices[0]),
            'proposition':proposition,'kind':'FACT','speaker':'UNKNOWN','stance':'UNRESOLVED',
            'source_refs':[{'cue_index':i,'quote':src.cues[i-1].text} for i in indices],
            'context_cue_indices':context or indices,'condition_cue_indices':conditions or [],
            'exception_cue_indices':exceptions or [],'numeric_references':numeric or [],'as_of':None}


def exchange(src,atoms):
    rows=[]
    for i,c in enumerate(src.cues,1):
        ids=sorted(a['claim_id'] for a in atoms if i in [r['cue_index'] for r in a['source_refs']])
        rows.append({'cue_index':i,'cue_text_sha256':sha256(c.text.encode()),
                     'disposition':'CANDIDATES' if ids else 'UNRESOLVED','claim_ids':ids,
                     'numeric_tokens':NUMBER.findall(c.text),'note':'' if ids else 'Source review remains open.'})
    return {'schema':'IRE_V6_HOST_ATOMIC_EXCHANGE_V1','video_id':src.video_id,
            'source_sha256':src.source_sha256,'manifest_sha256':src.manifest_sha256,
            'atoms':atoms,'cue_dispositions':rows}


def frame(atom,**updates):
    out={k:copy.deepcopy(v) for k,v in atom.items() if k not in {'claim_id','owner_window_id','speaker','stance'}}
    out.update(role='NARRATOR',attribution='DIRECT',polarity='AFFIRMED',modality='ASSERTED',
               correction=False,meaning_reason='Explicit source-clause meaning review; identity not verified.')
    out.update(updates)
    return out


def edit(ids,*frames,**updates):
    return {'prior_claim_ids':ids,'replacements':list(frames),'reason':'Explicit reviewer revision of the source claims.',**updates}


class ChatRevisionTests(unittest.TestCase):
    def test_role_revision_is_immutable_deterministic_and_native(self):
        src=fixture(['A speaker describes a diversified fund.','The introduction ends.'])
        old=old_atom(src,'C00001',[1],'A diversified fund is described.')
        before=exchange(src,[old]);saved=copy.deepcopy(before)
        out=compile_chat_atom_revision(src,before,edits=[edit(['C00001'],frame(old))])
        self.assertEqual(before,saved)
        self.assertEqual(out,compile_chat_atom_revision(src,before,edits=[edit(['C00001'],frame(old))]))
        new=out['exchange']['atoms'][0]
        self.assertEqual((new['claim_id'],new['speaker'],new['stance']),('C00002','NARRATOR','AFFIRMED'))
        self.assertEqual(out['typed_reviews'][0]['identity_status'],'NOT_AUDIO_AUTHENTICATED')
        self.assertEqual(audit_host_atomic_exchange(src,out['exchange'])['proposed_atomic_claims'],1)
        self.assertEqual(out['window_models']['W00001']['claims'][0]['claim_id'],'C00002')
        self.assertFalse(out['receipt']['publication_authorized'])

    def test_quoted_negative_is_not_presenter_negation(self):
        src=fixture(['The guest quotes a disputed negative statement.'])
        old=old_atom(src,'C00001',[1],'A negative statement is quoted.')
        out=compile_chat_atom_revision(src,exchange(src,[old]),edits=[edit(['C00001'],frame(old,role='GUEST',attribution='REPORTED',polarity='NEGATED'))])
        self.assertEqual(out['exchange']['atoms'][0]['stance'],'QUOTED')
        self.assertEqual(out['exchange']['atoms'][0]['speaker'],'QUOTED_SOURCE')
        self.assertEqual(out['typed_reviews'][0]['polarity'],'NEGATED')

    def test_question_not_native_affirmation(self):
        src=fixture(['Can an investor withdraw the funds?'])
        old=old_atom(src,'C00001',[1],'The investor asks about withdrawals.')
        out=compile_chat_atom_revision(src,exchange(src,[old]),edits=[edit(['C00001'],frame(old,kind='QUESTION',role='QUESTIONER',modality='QUESTION',polarity='UNRESOLVED'))])
        self.assertEqual(out['exchange']['atoms'][0]['stance'],'UNRESOLVED')
        self.assertEqual(out['typed_reviews'][0]['modality'],'QUESTION')

    def split_fixture(self):
        src=fixture(['A fund holds bonds.','Under specified conditions','it can lose value.'])
        old=old_atom(src,'C00001',[1,3],'The fund holds bonds and can lose value.',context=[1,2,3],conditions=[2])
        first=frame(old_atom(src,'C00002',[1],'The fund holds bonds.'))
        second=frame(old_atom(src,'C00003',[3],'The fund may lose value.',context=[2,3],conditions=[2]),modality='CONDITIONAL')
        return src,exchange(src,[old]),first,second

    def test_split_explicit_qualifier_exclusion_and_cross_window_owner(self):
        src,before,first,second=self.split_fixture()
        e=edit(['C00001'],first,second,qualifier_exclusions=[{'replacement_index':0,'field':'condition_cue_indices','cue_index':2,'reason':'Condition limits the loss clause rather than the holding description.'}])
        out=compile_chat_atom_revision(src,before,edits=[e])
        self.assertEqual(out['edit_lineage'][0]['operation'],'SPLIT')
        self.assertEqual([a['owner_window_id'] for a in out['exchange']['atoms']],['W00001','W00002'])
        self.assertEqual(out['exchange']['atoms'][1]['condition_cue_indices'],[2])

    def test_split_silent_condition_exclusion_rejected(self):
        src,before,first,second=self.split_fixture()
        with self.assertRaisesRegex(InvalidInput,'CHILD_QUALIFIER_SCOPE_UNREVIEWED'):
            compile_chat_atom_revision(src,before,edits=[edit(['C00001'],first,second)])

    def test_merge_preserves_context_and_records_lineage(self):
        src=fixture(['The product tracks an index.','It follows that same index.'])
        a=old_atom(src,'C00001',[1],'It tracks an index.')
        b=old_atom(src,'C00002',[2],'It follows the same index.')
        merged=frame(old_atom(src,'C00003',[1,2],'It tracks the specified index.'))
        out=compile_chat_atom_revision(src,exchange(src,[a,b]),edits=[edit(['C00001','C00002'],merged)])
        self.assertEqual(out['edit_lineage'][0]['operation'],'MERGE')
        self.assertEqual(out['receipt']['retired_atoms'],2)
        self.assertEqual(out['receipt']['after_atoms'],1)

    def test_add_keeps_existing_and_links_new_cue(self):
        src=fixture(['The fund holds bonds.','It also holds cash.'])
        a=old_atom(src,'C00001',[1],'The fund holds bonds.')
        b=old_atom(src,'C00002',[2],'The fund holds cash.')
        out=compile_chat_atom_revision(src,exchange(src,[a]),edits=[edit([],frame(b))])
        self.assertEqual(out['edit_lineage'][0]['operation'],'ADD')
        self.assertEqual(out['exchange']['atoms'][0],a)
        self.assertEqual(out['exchange']['cue_dispositions'][1]['claim_ids'],['C00002'])

    def test_full_unit_compatibility_and_unchanged_old_cue_census(self):
        src=fixture(['The hypothetical fund holds 271주.'])
        old=old_atom(src,'C00001',[1],'The fund holds 271주.',numeric=[{'cue_index':1,'token':'271'}])
        before=exchange(src,[old]);old_audit=audit_host_atomic_exchange(src,before)
        out=compile_chat_atom_revision(src,before,edits=[edit(['C00001'],frame(old,numeric_references=[{'cue_index':1,'token':'271주'}]))])
        self.assertEqual(before['cue_dispositions'][0]['numeric_tokens'],out['exchange']['cue_dispositions'][0]['numeric_tokens'])
        self.assertEqual(old_audit['proposed_atomic_claims'],audit_host_atomic_exchange(src,out['exchange'])['proposed_atomic_claims'])
        self.assertEqual(out['exchange']['atoms'][0]['numeric_references'][0]['token'],'271주')

    def test_changed_unit_and_partial_numeric_token_block(self):
        src=fixture(['The reported balance is 71억.'])
        old=old_atom(src,'C00001',[1],'The balance is 71억.',numeric=[{'cue_index':1,'token':'71'}])
        before=exchange(src,[old])
        for bad in (frame(old,proposition='The balance is 71만.',numeric_references=[{'cue_index':1,'token':'71억'}]),frame(old)):
            with self.subTest(bad=bad),self.assertRaises(InvalidInput):
                compile_chat_atom_revision(src,before,edits=[edit(['C00001'],bad)])

    def test_normalizing_transcribed_mixed_count_is_not_exact(self):
        src=fixture(['The count is 2천000개.'])
        old=old_atom(src,'C00001',[1],'The count is 2천 개.',numeric=[{'cue_index':1,'token':'2'},{'cue_index':1,'token':'000'}])
        before=exchange(src,[old])
        with self.assertRaisesRegex(InvalidInput,'COMPLETE_PROPOSITION_NUMBER_UNGROUNDED'):
            compile_chat_atom_revision(src,before,edits=[edit(['C00001'],frame(old,numeric_references=[{'cue_index':1,'token':'2천000개'}]))])

    def test_forged_source_and_context_drop_rejected(self):
        src,before,first,second=self.split_fixture()
        with self.assertRaisesRegex(InvalidInput,'PRIOR_CONTEXT_LOST'):
            compile_chat_atom_revision(src,before,edits=[edit(['C00001'],first)])
        forged=copy.deepcopy(first);forged['source_refs'][0]['quote']='Invented phrase.'
        with self.assertRaisesRegex(InvalidInput,'VERBATIM_REFS'):
            compile_chat_atom_revision(src,before,edits=[edit([],forged)])

    def test_review_cannot_hide_context_as_nonclaim(self):
        src=fixture(['The fund holds cash.','This is the surrounding context.'])
        a=old_atom(src,'C00001',[1],'The fund holds cash.',context=[1,2])
        before=exchange(src,[a]);reviews=[{'cue_index':2,'status':'NO_ATOM','reason':'Incorrectly classified as unrelated.'}]
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_SILENCED_AS_NONCLAIM'):
            compile_chat_atom_revision(src,before,edits=[edit(['C00001'],frame(a))],cue_reviews=reviews)
        reviews[0]['status']='CONTEXT_ONLY'
        out=compile_chat_atom_revision(src,before,edits=[edit(['C00001'],frame(a))],cue_reviews=reviews)
        self.assertEqual(out['cue_review_lineage'][0]['context_claim_ids'],['C00002'])


    def test_compiled_revision_enters_actual_native_host_transaction(self):
        from ire.v6.tests.test_prior_knowledge import PriorKnowledgeTests
        fixture_case=PriorKnowledgeTests(methodName="test_116_and_p4_29_are_replayed_without_approval")
        fixture_case.setUp()
        self.addCleanup(fixture_case.doCleanups)
        fx=fixture_case.fx
        owner,pin=fx.attest()
        base=fx.store.snapshot("host_scope")
        old=fx.exchange["atoms"][0]
        result=compile_chat_atom_revision(
            fx.source,fx.exchange,edits=[edit([old["claim_id"]],frame(
                old,kind="HYPOTHETICAL",modality="HYPOTHETICAL",
                meaning_reason="Expected rather than guaranteed return; source-only review."))])
        revised_id=result["edit_lineage"][0]["new_claim_ids"][0]
        knowledge=copy.deepcopy(fixture_case.inputs)
        for row in knowledge["relations"]:
            if row["claim_id"]==old["claim_id"]:
                row.update(claim_id=revised_id,target_kind="NONE",target_id=None,
                           target_content_sha256=None,relationship="NOVEL_PENDING",
                           rationale="Revised candidate requires fresh prior-knowledge review.")
        args=dict(scope_id="host_scope",run_id="chat_revision_native",
                  expected_head=base["ledger_head_sha256"],raw=fx.raw,manifest=fx.manifest,
                  inventory_bytes=owner,expected_inventory_sha256=pin,
                  exchange=result["exchange"],knowledge=knowledge,
                  window_models=result["window_models"],window_reviews=result["window_reviews"])
        first=fx.store.submit_host_atomic_batch(**args)
        self.assertTrue(first["atomic_batch_committed"])
        self.assertFalse(first["research_complete"])
        snap=fx.store.snapshot("host_scope")
        self.assertEqual(snap["progress"]["model_windows_recorded"],2)
        self.assertEqual(snap["progress"]["current_revision_structural_proof_records"],2)
        second=fx.store.submit_host_atomic_batch(**args)
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(first["event_sha256"],second["event_sha256"])
        self.assertEqual(snap["ledger_head_sha256"],fx.store.snapshot("host_scope")["ledger_head_sha256"])


if __name__=='__main__':unittest.main()
