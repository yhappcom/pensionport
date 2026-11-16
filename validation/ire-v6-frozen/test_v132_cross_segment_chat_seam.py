"""Source-bound synthetic negative controls for the 120→121 boundary gate."""
import copy
import unittest
from ire.v6.source import parse_srt, verify_source
from ire.v6.codec import sha256,json_digest
from ire.v6.errors import QualityNotProven
from v132_cross_segment_chat_seam import audit_explicit_cross_segment_question

texts=[
    "첫 발언을 이어갑니다.",
    "앞의 투자 방식에는 위험 가능성이 있습니다.",
    ">> 어 수익률을 높이기 위해서.",
    "저는 그런 생각해 봅니다. 선생님",
    "아직 살아 계시지만 이분을 추종하는",
    "사람들도 모두 성공하지 않았을까?",
    "그것은 확정된 투자 실적이 아닙니다.",
    "추종자들도 다양한 성과를 경험했겠죠.",
    "다른 근거 없이 단정할 수 없습니다.",
]
RAW='\n\n'.join(f'{i}\n00:00:{i:02d},000 --> 00:00:{i:02d},900\n{t}' for i,t in enumerate(texts,1)).encode()

def fixture():
    cues=parse_srt(RAW)
    def src(first,last,wid):
        manifest={"schema":"IRE_V6_SOURCE_PLAN_V1","video_id":"Abcdefghijk",
                  "source_sha256":sha256(RAW),"cue_count":len(cues),
                  "scope":{"mode":"PARTIAL","first_cue":first,"last_cue":last},
                  "windows":[{"window_id":wid,"first_cue":first,"last_cue":last,
                  "text_sha256":sha256(' '.join(c.text for c in cues[first-1:last]).encode())}]}
        return verify_source(RAW,manifest,expected_source_sha256=sha256(RAW),expected_manifest_sha256=json_digest(manifest))
    a,b=src(1,4,"W00001"),src(5,9,"W00002")
    rows=[]
    for i in range(1,5):
        role="OPEN" if i in (3,4) else "ASSERTION" if i==2 else "CONTEXT"
        rows.append({"cue_index":i,"cue_text_sha256":sha256(cues[i-1].text.encode()),
                     "role":role,"atom_ids":["ATOM_001"] if role=="ASSERTION" else [],
                     "rationale":"분리해서 문맥을 검토해야 하는 원문 주장 상태로 기록합니다.",
                     "risk_checked":True,"review_state":"OPEN" if role=="OPEN" else "REVIEWED"})
    atom={"atom_id":"ATOM_001","proposition":"투자에는 수익과 손실이 모두 발생할 수 있습니다.",
          "source_cues":[2],"speech_act":"ASSERTION","context_constraints":["수익을 보장하지 않음"],
          "chat_private_review_sha256":sha256(b'atom')}
    old={"schema":"IRE_V131_CHAT_EXPLICIT_CUE_DISPOSITIONS_V1",
         "source_sha256":a.source_sha256,"manifest_sha256":a.manifest_sha256,
         "reviewer":"CHATGPT_IN_CHAT","cue_rows":rows,"atoms":[atom]}
    revised=copy.deepcopy(old)
    revised["cue_rows"][-1].update({"role":"CONTEXT","review_state":"REVIEWED",
        "rationale":"다음 구간에 이어지는 질문의 도입부이며 확인된 투자 수익률 사실이 아닙니다."})
    why="이 발화는 누군가를 따라 투자한 사람들이 성공했을까 묻는 가정적 의문문입니다."
    counter="다른 사람이 실제로 높은 수익을 냈다는 자료는 제시되지 않아 확정할 수 없습니다."
    seam={"schema":"IRE_V132_CHAT_BOUNDARY_QUESTION_DISPOSITION_V1",
          "reviewer":"CHATGPT_IN_CHAT", "video_id":a.video_id,
          "parent_source_sha256":a.source_sha256,"left_manifest_sha256":a.manifest_sha256,
          "right_manifest_sha256":b.manifest_sha256,"cue_indices":[4,5,6,7,8,9],
          "cue_text_sha256":[sha256(cues[i-1].text.encode()) for i in range(4,10)],
          "discourse_kind":"SPECULATIVE_QUESTION_NOT_ESTABLISHED_RETURN",
          "semantic_interpretation":why,"source_based_counterexample":counter,
          "literal_spoken_question_confirmed":True,
          "financial_success_fact_verified":False,
          "independent_audio_speaker_verified":False,
          "chat_private_review_sha256":sha256((why+'\n'+counter).encode())}
    return a,b,old,revised,seam

class V132CrossChildQuestionSeamTests(unittest.TestCase):
    def setUp(self):self.a,self.b,self.old,self.new,self.seam=fixture()
    def gate(self):return audit_explicit_cross_segment_question(self.a,self.b,self.old,self.new,self.seam)
    def test_recheck_original_question_link_but_keep_open(self):
        r=self.gate()
        self.assertEqual(r['status'],'QUESTION_SEAM_CONTEXT_RESOLVED_V123_STILL_HOLD')
        self.assertEqual(r['original_unresolved_open_cues'],2)
        self.assertEqual(r['remaining_unresolved_open_cues'],1)
        self.assertFalse(r['knowledge_export_authorized'])
        self.assertFalse(r['historical_followers_success_claim_accepted'])
    def test_other_open_cue_must_remain(self):
        self.new['cue_rows'][2]['role']='CONTEXT'
        self.new['cue_rows'][2]['review_state']='REVIEWED'
        with self.assertRaises(QualityNotProven):self.gate()
    def test_old_atoms_not_silently_rewritten(self):
        self.new['atoms'][0]['proposition']='잘못된 성과를 사실로 변경'
        with self.assertRaisesRegex(QualityNotProven,'OTHER_CUE_OR_ATOM_REWRITTEN'):self.gate()
    def test_forged_source_cue_hash_blocked(self):
        self.seam['cue_text_sha256'][1]='f'*64
        with self.assertRaisesRegex(QualityNotProven,'BOUNDARY_SOURCE_OR_MEANING_CONTRADICTION'):self.gate()
    def test_financial_success_claim_not_upgraded(self):
        self.seam['financial_success_fact_verified']=True
        with self.assertRaisesRegex(QualityNotProven,'BOUNDARY_SOURCE_OR_MEANING_CONTRADICTION'):self.gate()
    def test_forged_chat_note_sha_blocked(self):
        self.seam['semantic_interpretation']+=' 추가된 문구'
        with self.assertRaisesRegex(QualityNotProven,'PRIVATE_CHAT_EVIDENCE_HASH_DRIFT'):self.gate()
    def test_no_fake_audio_speaker_verification(self):
        self.seam['independent_audio_speaker_verified']=True
        with self.assertRaisesRegex(QualityNotProven,'BOUNDARY_SOURCE_OR_MEANING_CONTRADICTION'):self.gate()
    def test_missing_chat_question_confirmation(self):
        self.seam['literal_spoken_question_confirmed']=False
        with self.assertRaisesRegex(QualityNotProven,'BOUNDARY_SOURCE_OR_MEANING_CONTRADICTION'):self.gate()
    def test_other_row_modification_cannot_hide_missing_claim(self):
        self.new['cue_rows'][1]['role']='CONTEXT'
        self.new['cue_rows'][1]['atom_ids']=[]
        with self.assertRaisesRegex(QualityNotProven,'OTHER_CUE_OR_ATOM_REWRITTEN'):self.gate()
    def test_overwritten_boundary_note_without_reason_blocked(self):
        self.new['cue_rows'][-1]['rationale']='검토함'
        with self.assertRaisesRegex(QualityNotProven,'UNJUSTIFIED_BOUNDARY_ROLE_REVISION'):self.gate()

if __name__=='__main__':unittest.main()
