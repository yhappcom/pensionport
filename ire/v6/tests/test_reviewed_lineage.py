"""Synthetic structure tests; no semantic or release certification."""
import copy, unittest
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.reviewed_lineage import compile_reviewed_lineage

class ReviewedLineageTests(unittest.TestCase):
    def setUp(self):
        def atom(i):return {'claim_id':f'C{i:05d}','kind':'FACT','speaker':'NARRATOR','stance':'AFFIRMED','as_of':None,'proposition':'synthetic original','context_cue_indices':[i], 'condition_cue_indices':[i], 'exception_cue_indices':[], 'source_refs':[{'cue_index':i,'quote':'synthetic'}], 'numeric_references':[]}
        self.a=[atom(i) for i in range(1,7)]
        self.record={'exchange':{'atoms':self.a},'ledger':{'quarantine_atoms':[{'claim_id':'C00006'}],'projection_rows':[{'claim_id':a['claim_id'],'typed_sha256':json_digest(a)} for a in self.a]}}
        self.review=[{'claim_id':a['claim_id'],'atom_sha256':json_digest(a),'status':s,'reason':'synthetic decision only'} for a,s in zip(self.a,['CORRECT','NON_KNOWLEDGE','SPLIT','MERGE','MERGE','QUARANTINE'])]
        self.changes=[{'claim_id':'C00001','operation':'CORRECT_SOURCE_CANDIDATE','source_atom_sha256':json_digest(self.a[0]),'proposed_proposition':'synthetic correction'}]
        self.ops=[{'operation':k,'parents':p,'propositions':v,'reason':'synthetic reason only'} for k,p,v in [('CORRECT',['C00001'],['synthetic correction']),('RETIRE',['C00002'],[]),('SPLIT',['C00003'],['synthetic part one','synthetic part two']),('MERGE',['C00004','C00005'],['synthetic combination'])]]
    def run_compile(self):return compile_reviewed_lineage(self.record,'a'*64,self.review,self.ops,self.changes)
    def test_four_operations(self):
        before=copy.deepcopy(self.record);r=self.run_compile();self.assertEqual(self.record,before);self.assertEqual(len(r['candidates']),4);self.assertEqual(r['unchanged_claim_ids'],['C00006']);self.assertFalse(r['formal_v123_input_authorized']);self.assertFalse(r['active_knowledge_changed']);self.assertEqual(r['candidates'][-1]['condition_cue_indices'],[4,5])
    def test_missing_review(self):
        self.review.pop();self.assertRaisesRegex(InvalidInput,'REVIEW_CENSUS',self.run_compile)
    def test_quarantine(self):
        self.review[-1]['status']='SOURCE_ONLY';self.assertRaisesRegex(InvalidInput,'QUARANTINE_DRIFT',self.run_compile)
    def test_duplicate(self):
        self.ops.append(self.ops[0]);self.assertRaisesRegex(InvalidInput,'OP_PARENTS',self.run_compile)
    def test_changed_correction(self):
        self.ops[0]['propositions']=['different correction'];self.assertRaisesRegex(InvalidInput,'CORRECTION_DRAFT_DRIFT',self.run_compile)
    def test_no_split(self):
        self.ops[2]['propositions'].pop();self.assertRaisesRegex(InvalidInput,'OP_CARDINALITY',self.run_compile)
    def test_missing_typed(self):
        self.record['ledger']['projection_rows'].pop();self.assertRaisesRegex(InvalidInput,'TYPED_CENSUS',self.run_compile)
    def test_missing_operation(self):
        self.ops.pop();self.assertRaisesRegex(InvalidInput,'OP_CENSUS',self.run_compile)
