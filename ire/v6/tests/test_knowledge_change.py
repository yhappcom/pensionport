import copy
import unittest
from ire.v6.atomic_exchange import _digest_rows
from ire.v6.codec import json_digest
from ire.v6.errors import InvalidInput
from ire.v6.knowledge_change import audit_knowledge_change


class KnowledgeChangeTests(unittest.TestCase):
    def setUp(self):
        self.atom = {'claim_id':'C00001','proposition':'original'}
        self.record = {'exchange':{'atoms':[self.atom]},'ledger':{'quarantine_atoms':[]}}
        self.rows = [{'claim_id':'C00001','relationship':'OPEN','target_id':'prior'}]
        self.head = 'a'*64
        self.plan = {'schema':'IRE_V6_KNOWLEDGE_CHANGE_PLAN_V1','predecessor_event_sha256':self.head,'rows':[{'prior_row_sha256':json_digest(self.rows[0]),'native_atom_sha256':json_digest(self.atom),'operation':'CORRECT_SOURCE_CANDIDATE','reason':'A scoped correction proposal.','evidence_urls':['https://example.org/source']}]}

    def audit(self, current=None, plan=None, rows=None):
        return audit_knowledge_change(self.record,self.record if current is None else current,self.head,_digest_rows(self.rows),self.rows if rows is None else rows,self.plan if plan is None else plan)

    def test_unapproved_receipt(self):
        r = self.audit()
        self.assertEqual(r['counts']['CORRECT_SOURCE_CANDIDATE'],1)
        for k in ('finance_evidence_authenticated','active_knowledge_changed','formal_v123_input_authorized','p0_go'):
            self.assertIs(r[k],False)

    def test_cannot_rewrite_original(self):
        record = copy.deepcopy(self.record)
        record['exchange']['atoms'][0]['proposition']='rewritten'
        with self.assertRaisesRegex(InvalidInput,'SOURCE_RECORD_CHANGED'):
            self.audit(current=record)

    def test_cannot_rewrite_prior(self):
        rows = copy.deepcopy(self.rows)
        rows[0]['target_id']='other'
        with self.assertRaisesRegex(InvalidInput,'PRIOR_ROWS_CHANGED'):
            self.audit(rows=rows)

    def test_cannot_self_approve(self):
        self.plan['rows'][0]['approved']=True
        with self.assertRaisesRegex(InvalidInput,'ROW_SCHEMA'):
            self.audit()

    def test_cannot_release_quarantine(self):
        self.record['ledger']['quarantine_atoms']=[{'claim_id':'C00001'}]
        with self.assertRaisesRegex(InvalidInput,'QUARANTINE_OR_EVIDENCE'):
            self.audit()

    def test_cannot_omit_evidence(self):
        self.plan['rows'][0]['evidence_urls']=[]
        with self.assertRaisesRegex(InvalidInput,'QUARANTINE_OR_EVIDENCE'):
            self.audit()

    def test_cannot_duplicate_row(self):
        self.plan['rows'].append(copy.deepcopy(self.plan['rows'][0]))
        with self.assertRaisesRegex(InvalidInput,'ROW_IDENTITY'):
            self.audit()
