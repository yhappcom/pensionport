"""V41 synthetic anti-leak and source-to-atom contract tests; no real gold."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from ire.v6.errors import InvalidInput, LedgerCorrupted
from ire.v6.atomic_exchange import NUMBER
from ire.v6.semantic_checkpoint_v40 import PrivateSemanticCheckpointV40,ZERO_SHA
from ire.v6.semantic_atom_handoff_v41 import audit_v40_to_v6_atom_handoff_v41
from ire.v6.source import parse_srt
from ire.v6.tests import test_host_semantic_custody_v39 as fixture_module


class SemanticAtomHandoffV41Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        f=fixture_module.SourceBoundSemanticReviewV39Tests(
            'test_all_source_bound_candidates_and_notes_replayed')
        f.setUp()
        self.source=copy.deepcopy(f.raws)
        self.pins=copy.deepcopy(f.sources)
        self.windows=copy.deepcopy(f.windows)
        self.host=copy.deepcopy(f.rows)
        self.vid=f.vid
        self.store=PrivateSemanticCheckpointV40(Path(self.tmp.name)/'owner-private.sqlite')
        self.saved=self.store.submit(
            run_id='first_checkpoint',expected_head=ZERO_SHA,
            original_srt_bytes=self.source,source_pins=self.pins,
            window_pins=self.windows,host_rows=self.host)
        cues=parse_srt(self.source[self.vid])
        self.target=[{'video_id':self.vid,'window_id':'W00001'}]
        self.atoms=[]
        self.links=[]
        for index,row in enumerate(self.host,1):
            aid=f'C{50000+index:05d}'
            cidx=row['cue_indices'][0]
            raw=cues[cidx-1].text
            self.atoms.append({
                'claim_id':aid,'owner_window_id':row['window_id'],
                'proposition':'해당 발화에 사용된 미확인 금융 가정의 설명입니다.',
                'kind':'HYPOTHETICAL','stance':'UNRESOLVED',
                'speaker':'UNKNOWN',
                'source_refs':[{'cue_index':cidx,'quote':raw}],
                'context_cue_indices':row['cue_indices'],
                'condition_cue_indices':[],'exception_cue_indices':[],
                'numeric_references':[],'as_of':None})
            self.links.append({
                'video_id':row['video_id'],'window_id':row['window_id'],
                'candidate_id':row['claim_id'],'note_index':0,
                'disposition':'PROPOSE_ATOMS','atom_ids':[aid],
                'reason':'출처가 고정된 잠정 발화를 사실 인증 없이 원자 제안에 대응시킨다.'})

    def audit(self,**updates):
        params=dict(v40_store=self.store, original_srt_bytes=self.source,
                    source_pins=self.pins,window_pins=self.windows,
                    host_rows=self.host,target_windows=self.target,
                    proposed_atoms=self.atoms,note_links=self.links)
        params.update(updates)
        return audit_v40_to_v6_atom_handoff_v41(**params)

    def test_normal_atom_note_mapping_all_selected_candidates(self):
        r=self.audit()
        self.assertEqual(r['source_v33_utterances_mapped'],len(self.host))
        self.assertEqual(r['all_v39_review_notes_dispositioned'],len(self.host))
        self.assertEqual(r['proposed_atomic_frames'],len(self.host))
        self.assertEqual(r['open_notes'],0)
        self.assertFalse(r['final_model_commit_authorized'])
        self.assertFalse(r['p0_go'])
        self.assertNotIn('proposition',r)

    def test_v40_checkpoint_required(self):
        blank=PrivateSemanticCheckpointV40(Path(self.tmp.name)/'not-committed.sqlite')
        with self.assertRaisesRegex(InvalidInput,'MISSING_V40_CHECKPOINT'):
            self.audit(v40_store=blank)

    def test_missing_note_link_blocks(self):
        with self.assertRaisesRegex(InvalidInput,'NOT_ALL_SEMANTIC_NOTES_DISPOSITIONED'):
            self.audit(note_links=self.links[:-1])

    def test_duplicate_note_link_blocks(self):
        with self.assertRaisesRegex(InvalidInput,'DUPLICATE_NOTE_LINK'):
            self.audit(note_links=self.links+[copy.deepcopy(self.links[0])])

    def test_unlinked_final_atom_blocks(self):
        new=copy.deepcopy(self.atoms[0]);new['claim_id']='C90001'
        with self.assertRaisesRegex(InvalidInput,'ORPHAN_ATOM'):
            self.audit(proposed_atoms=self.atoms+[new])

    def test_unowned_draft_candidate_blocks(self):
        links=copy.deepcopy(self.links);links[0]['candidate_id']='C99999'
        with self.assertRaisesRegex(InvalidInput,'UNEXPECTED_OR_DUPLICATE_NOTE_LINK'):
            self.audit(note_links=links)

    def test_wrong_v39_note_cannot_replay_v40_checkpoint(self):
        rows=copy.deepcopy(self.host)
        rows[0]['semantic_notes'][0]['meaning']='가정의 의미를 몰래 변경한 검토 설명입니다.'
        with self.assertRaisesRegex(InvalidInput,'NOT_SAME_CHAT_REVIEW_SOURCE'):
            self.audit(host_rows=rows)

    def test_question_must_stay_question(self):
        rows=copy.deepcopy(self.host)
        rows[0]['semantic_notes'][0]['kind']='Q'
        # Commit separately with changed host notes (V40 hash must match).
        store=PrivateSemanticCheckpointV40(Path(self.tmp.name)/'questions.sqlite')
        store.submit(run_id='question_checkpoint',expected_head=ZERO_SHA,
                     original_srt_bytes=self.source,source_pins=self.pins,
                     window_pins=self.windows,host_rows=rows)
        with self.assertRaisesRegex(InvalidInput,'STANCE_INVERTED'):
            self.audit(v40_store=store,host_rows=rows)

    def test_hypothesis_must_not_be_confirmed_fact(self):
        atoms=copy.deepcopy(self.atoms);atoms[0]['kind']='FACT';atoms[0]['stance']='AFFIRMED'
        with self.assertRaisesRegex(InvalidInput,'STANCE_INVERTED'):
            self.audit(proposed_atoms=atoms)

    def test_exact_quote_required(self):
        atoms=copy.deepcopy(self.atoms);atoms[0]['source_refs'][0]['quote']='허위 삽입 인용문'
        with self.assertRaisesRegex(InvalidInput,'QUOTE_NOT_IN_PRIVATE_SRT'):
            self.audit(proposed_atoms=atoms)

    def test_condition_requires_original_context(self):
        atoms=copy.deepcopy(self.atoms);atoms[0]['stance']='CONDITIONAL'
        with self.assertRaisesRegex(InvalidInput,'CONDITION_EXCEPTION_CONTEXT_NOT_GROUNDED'):
            self.audit(proposed_atoms=atoms)

    def test_numeric_not_in_original_blocks(self):
        atoms=copy.deepcopy(self.atoms);atoms[0]['proposition']='미확인 999%를 보장한다는 부정확한 진술입니다.'
        with self.assertRaisesRegex(InvalidInput,'PROPOSITION_NUMBER_UNGROUNDED'):
            self.audit(proposed_atoms=atoms)

    def test_open_source_note_counts_remain_open(self):
        atoms=copy.deepcopy(self.atoms[1:]);links=copy.deepcopy(self.links)
        links[0]['disposition']='OPEN_REQUIRES_REVIEW';links[0]['atom_ids']=[]
        result=self.audit(proposed_atoms=atoms,note_links=links)
        self.assertEqual(result['open_notes'],1)
        self.assertFalse(result['final_model_commit_authorized'])

    def test_fragment_must_not_generate_factual_atom(self):
        rows=copy.deepcopy(self.host)
        rows[0]['semantic_notes'][0]['kind']='F'
        store=PrivateSemanticCheckpointV40(Path(self.tmp.name)/'fragments.sqlite')
        store.submit(run_id='fragment_checkpoint',expected_head=ZERO_SHA,
                     original_srt_bytes=self.source,source_pins=self.pins,
                     window_pins=self.windows,host_rows=rows)
        with self.assertRaisesRegex(InvalidInput,'CONTEXT_FRAGMENT'):
            self.audit(v40_store=store,host_rows=rows)

    def test_fragment_context_only_allowed_not_fact_approval(self):
        rows=copy.deepcopy(self.host);rows[0]['semantic_notes'][0]['kind']='F'
        store=PrivateSemanticCheckpointV40(Path(self.tmp.name)/'fragment-accepted.sqlite')
        store.submit(run_id='fragment_checkpoint',expected_head=ZERO_SHA,
                     original_srt_bytes=self.source,source_pins=self.pins,
                     window_pins=self.windows,host_rows=rows)
        links=copy.deepcopy(self.links)
        links[0]['disposition']='CONTEXT_ONLY';links[0]['atom_ids']=[]
        result=self.audit(v40_store=store,host_rows=rows,
                          proposed_atoms=self.atoms[1:],note_links=links)
        self.assertEqual(result['all_v39_review_notes_dispositioned'],len(self.host))
        self.assertFalse(result['v6_atomic_exchange_complete_and_approved'])

    def test_checkpoint_window_ownership_tamper_blocks(self):
        import sqlite3
        with sqlite3.connect(self.store.db_path) as con:
            con.execute('UPDATE v40_window_ownership SET window_id=?',('W00002',))
        with self.assertRaisesRegex(LedgerCorrupted,'OWNERSHIP_CENSUS_DRIFT'):
            self.audit()

    def test_replay_private_source_modified_blocks(self):
        raw=copy.deepcopy(self.source)
        raw[self.vid]+=b' '
        with self.assertRaisesRegex(InvalidInput,'ORIGINAL_SRT_SHA_DRIFT'):
            self.audit(original_srt_bytes=raw)

    def test_duplicate_atom_usage_for_two_notes_blocks(self):
        rows=copy.deepcopy(self.host)
        rows[0]['semantic_notes'].append({'kind':'H','meaning':'별개의 두 번째 잠정 가정 설명이 추가되었다.'})
        store=PrivateSemanticCheckpointV40(Path(self.tmp.name)/'twonotes.sqlite')
        store.submit(run_id='twonotes_checkpoint',expected_head=ZERO_SHA,
                     original_srt_bytes=self.source,source_pins=self.pins,
                     window_pins=self.windows,host_rows=rows)
        links=copy.deepcopy(self.links)
        clone=copy.deepcopy(links[0]);clone['note_index']=1
        links.append(clone)
        with self.assertRaisesRegex(InvalidInput,'DUPLICATE_ATOM_NOTE_OWNERSHIP'):
            self.audit(v40_store=store,host_rows=rows,note_links=links)


if __name__=='__main__':unittest.main()
