from __future__ import annotations
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from ire.v5.engine import ResearchRun
from ire.v5.tests.test_engine import SRT, MAN, TEXT
from ire.v5_app.server import AppCore, create_server

TOKEN='TEST_ACCESS_TOKEN_ONLY_0123456789'

class AppServerTests(unittest.TestCase):
 def setUp(self):
  self.d=tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
  store=Path(self.d.name)/'store'
  run=ResearchRun(SRT,MAN,store)
  (store/'private_source.srt').write_bytes(SRT)
  (store/'source_manifest.json').write_text(json.dumps(MAN))
  self.app=AppCore(store)
  self.server=create_server(self.app,TOKEN,0)
  self.addCleanup(self.server.server_close)
  self.thread=Thread(target=self.server.serve_forever,daemon=True)
  self.thread.start();self.addCleanup(self.server.shutdown)
  self.base=f'http://127.0.0.1:{self.server.server_address[1]}'
 def request(self,path,body=None,token=TOKEN):
  headers={'Authorization':'Bearer '+token}
  data=None
  if body is not None:
   data=json.dumps(body).encode();headers['Content-Type']='application/json'
  return urlopen(Request(self.base+path,data=data,headers=headers),timeout=2)
 def test_server_binds_loopback_only(self):
  self.assertEqual(self.server.server_address[0],'127.0.0.1')
  h=json.load(urlopen(self.base+'/health',timeout=2))
  self.assertFalse(h['model_inference_in_server'])
 def test_auth_required_for_next(self):
  with self.assertRaises(HTTPError) as e:self.request('/v1/next',token='BADTOKEN')
  self.assertEqual(e.exception.code,401)
 def test_real_next_phase_from_private_v5_ledger(self):
  nxt=json.load(self.request('/v1/next'))
  self.assertEqual(nxt['phase'],'MODEL_ANALYSIS_REQUIRED')
  self.assertEqual(nxt['window_id'],'W00001')
  self.assertEqual(len(nxt['packet']['cues']),2)
 def test_submit_source_bound_model_and_advance(self):
  nxt=json.load(self.request('/v1/next'))
  claim='V5C0001'
  payload={"schema":"IRE_V5_MODEL_WINDOW_V1","window_id":"W00001",
   "claimed_author":"CURRENT_CHATGPT_CONVERSATION","independent_human_verified":False,
   "packet_sha256":nxt['packet']['packet_sha256'],
   "claims":[{"claim_id":claim,"proposition":"Personal pension income depends on conditions.",
    "kind":"HYPOTHETICAL","requires_external_verification":True,
    "fact_verified":False,"advisory_approved":False,
    "source_refs":[{"cue_index":i,"quote":TEXT[i]} for i in (1,2)]}],
   "cue_dispositions":[{"cue_index":i,"status":"LINKED",
    "claim_ids":[claim],"reason":None} for i in (1,2)]}
  head=self.app.state()['research']['event_chain_head_sha256']
  cmd={'event_type':'MODEL_ANALYSIS','payload':payload,'expected_chain_head':head,
       'expected_task_sha256':nxt['task_sha256']}
  r=json.load(self.request('/v1/receipt',cmd))
  self.assertEqual(r['receipt_sequence'],1)
  self.assertEqual(r['next_phase'],'OFFICIAL_EVIDENCE_REVIEW_REQUIRED')
  with self.assertRaises(HTTPError) as e:self.request('/v1/receipt',cmd)
  self.assertEqual(e.exception.code,409)
 def test_refuse_to_seal_before_review(self):
  nxt=json.load(self.request('/v1/next'))
  with self.assertRaises(HTTPError) as e:
   self.request('/v1/seal',{'expected_chain_head':'0'*64,
                            'expected_task_sha256':nxt['task_sha256']})
  self.assertEqual(e.exception.code,409)
 def test_reject_unexpected_or_huge_request(self):
  with self.assertRaises(HTTPError) as e:self.request('/v1/receipt',{'action':'anything'})
  self.assertEqual(e.exception.code,409)

if __name__=='__main__': unittest.main()
