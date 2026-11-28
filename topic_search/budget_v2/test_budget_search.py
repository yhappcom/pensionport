import unittest
from budget_search import select

def row(s,a,b,score):return dict(source_sha=s,first_cue=a,last_cue=b,score=score)
class BudgetTests(unittest.TestCase):
 def test_source_diversity(self):
  rows=[row('a',1,48,10),row('a',49,96,9),row('b',1,48,1)];self.assertEqual([r['source_sha'] for r in select({'results':rows},2)],['a','b'])
 def test_overlap(self):
  rows=[row('a',1,48,10),row('a',12,59,9),row('a',60,107,8)];self.assertEqual([r['first_cue'] for r in select({'results':rows},3)],[1,60])
 def test_empty(self):self.assertEqual(select({'results':[]}),[])
 def test_invalid_limit(self):
  with self.assertRaises(ValueError):select({'results':[]},0)
 def test_deterministic_and_unmutated(self):
  rows=[row('b',1,48,1),row('a',1,48,1)];self.assertEqual(select({'results':rows}),select({'results':list(reversed(rows))}));self.assertEqual(rows[0]['source_sha'],'b')
