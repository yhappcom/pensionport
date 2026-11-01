"""Private checkpoint interrupt/resume integrity regression (new synthetic content)."""
from pathlib import Path
import tempfile
import unittest
from ire.semantics import InferenceConfig,interpret_original
from ire.checkpoint import SemanticCheckpointLedger
from ire.source import sha256
from test_engine import VID

def source_many():
    blocks=[]
    for n in range(1,32):
        second=(n-1)*2
        hh=second//3600;mm=(second%3600)//60;ss=second%60
        end=second+1; eh=end//3600;em=(end%3600)//60;es=end%60
        blocks.append(
          f"{n}\n{hh:02d}:{mm:02d}:{ss:02d},000 --> "
          f"{eh:02d}:{em:02d}:{es:02d},500\n"
          f"새로운 합성 비금융 안내 문장 {n}입니다.")
    return ("\n\n".join(blocks)+"\n").encode("utf-8")


def nonclaim_response(window):
    return {
        "claims":[],
        "cue_dispositions":[
            {"cue_index":c["cue_index"],"status":"NONCLAIM_CANDIDATE",
             "reason":"검증용 합성 데이터의 비금융 발언으로 미확정 분류"}
            for c in window["primary_cues"]]
    }


class PrivateResumeTests(unittest.TestCase):
    def test_retry_uses_validated_previous_model_outputs(self):
        raw=source_many()
        model=InferenceConfig(model="development-injected-mock-02")
        with tempfile.TemporaryDirectory() as temporary:
            first=[]
            def interrupted(data):
                first.append(data["window_id"])
                if len(first)==2:raise ValueError("SIMULATED_MODEL_FAILURE")
                return nonclaim_response(data)
            with self.assertRaisesRegex(ValueError,"SIMULATED_MODEL_FAILURE"):
                interpret_original(raw,VID,model,interrupted,
                                   private_checkpoint_directory=temporary)
            second=[]
            def restart(data):
                second.append(data["window_id"])
                return nonclaim_response(data)
            report=interpret_original(raw,VID,model,restart,
                                      private_checkpoint_directory=temporary)
            self.assertEqual(report["validation"]["source_cues"],31)
            self.assertEqual(report["validation"]["proposed_atomic_claims"],0)
            self.assertEqual(report["previously_cached_window_count"],1)
            self.assertEqual(report["completed_window_count"],4)
            self.assertEqual(second,["W00002","W00003","W00004"])
            self.assertFalse(report["research_complete"])
            self.assertTrue(list(Path(temporary).rglob("manifest.json")))
            for file in Path(temporary).rglob("*.json"):
                self.assertEqual(file.stat().st_mode & 0o077,0)

    def test_model_drift_does_not_reuse_prior_response(self):
        raw=source_many()
        with tempfile.TemporaryDirectory() as temporary:
            a=interpret_original(raw,VID,InferenceConfig(model="mock-first"),
                                 nonclaim_response,
                                 private_checkpoint_directory=temporary)
            self.assertEqual(a["previously_cached_window_count"],0)
            b=interpret_original(raw,VID,InferenceConfig(model="mock-second"),
                                 nonclaim_response,
                                 private_checkpoint_directory=temporary)
            self.assertEqual(b["previously_cached_window_count"],0)
            self.assertEqual(len(list(Path(temporary).glob("*/manifest.json"))),2)

    def test_private_repository_boundary(self):
        from ire.cli import REPOSITORY
        raw=source_many()
        with self.assertRaisesRegex(ValueError,"CHECKPOINT_INSIDE_REPOSITORY_FORBIDDEN"):
            interpret_original(raw,VID,InferenceConfig(model="mock"),
                               nonclaim_response,
                               private_checkpoint_directory=str(REPOSITORY/"unallowed"))


if __name__=="__main__":
    unittest.main()
