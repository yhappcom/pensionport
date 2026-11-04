"""Run the deterministic 20-claim / 5-video intake integrity gate."""
from pathlib import Path
import argparse
import json
from .advisory_knowledge_gate import verify_core20
from .new_video_gate import verify_five
from .legacy_lineage_audit import audit

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=Path("."))
    args=p.parse_args()
    out={"schema":"IRE_V5_20_PLUS_5_DEVELOPMENT_GATE_V1",
         "legacy_claims":verify_core20(args.root),
         "new_videos":verify_five(args.root),
         "original_video_lineage":audit(args.root),
         "independent_approval_granted":False,
         "investment_advice_release":"NO_GO"}
    print(json.dumps(out,sort_keys=True,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
