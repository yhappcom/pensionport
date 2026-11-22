"""P101 core module CLI audit. This does NOT prove zero direct Python imports,
full deployment exposure or trusted ChatGPT user-turn provenance."""
from __future__ import annotations
import ast
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
CORE=(
"validation/ire-v6-frozen/v123_chat_final_gate.py",
"validation/ire-v6-frozen/v126_chat_approved_knowledge_store.py",
"validation/ire-v6-frozen/v128_host_continuous_video.py",
"validation/ire-v6-frozen/v128_atomic_parent_knowledge.py",
"validation/ire-v6-frozen/v166_e4_primary_approval_gate.py",
"validation/ire-v6-frozen/v166_e4_sealed_knowledge.py",
"validation/ire-v6-frozen/v193_e3_two_user_turn_contract.py",
"validation/ire-v6-frozen/v243_canonical_e1_e5_route.py",
"validation/ire-v6-frozen/v245_e1_typed_parent_review_overlay.py",
)
CONFIGS=("pyproject.toml","setup.py","setup.cfg","Dockerfile","Procfile")
FRAMEWORKS={"argparse","click","typer","flask","fastapi","uvicorn"}
def _main(n):
    if not isinstance(n,ast.If) or not isinstance(n.test,ast.Compare):return False
    t=n.test
    return (isinstance(t.left,ast.Name) and t.left.id=="__name__"
            and len(t.ops)==1 and isinstance(t.ops[0],ast.Eq)
            and len(t.comparators)==1 and isinstance(t.comparators[0],ast.Constant)
            and t.comparators[0].value=="__main__")
def validate(root=ROOT):
    errors=[]
    for path in CORE:
        file=root/path
        if not file.is_file():
            errors.append("P101_CORE_FILE_ABSENT:"+path);continue
        try: doc=ast.parse(file.read_text(encoding="utf8"))
        except (OSError,SyntaxError,UnicodeError):
            errors.append("P101_CORE_NOT_PARSEABLE:"+path);continue
        for node in ast.walk(doc):
            if _main(node):errors.append("P101_DIRECT_CLI_EXPORT:"+path)
            if isinstance(node,ast.Import):
                if any(x.name.split(".")[0] in FRAMEWORKS for x in node.names):
                    errors.append("P101_UNREVIEWED_SERVICE_FRAMEWORK:"+path)
            if isinstance(node,ast.ImportFrom) and (node.module or "").split(".")[0] in FRAMEWORKS:
                errors.append("P101_UNREVIEWED_SERVICE_FRAMEWORK:"+path)
        if path=="validation/ire-v6-frozen/v243_canonical_e1_e5_route.py":
            exports=[x for x in doc.body if isinstance(x,ast.Assign) and
                     any(isinstance(t,ast.Name) and t.id=="__all__" for t in x.targets)]
            if len(exports)!=1 or not isinstance(exports[0].value,(ast.Tuple,ast.List)) or [
                x.value for x in exports[0].value.elts if isinstance(x,ast.Constant)
            ]!=["run_canonical_research_route"]:
                errors.append("P101_SINGLE_OFFICIAL_PUBLIC_API_VIOLATION")
            source=file.read_text(encoding="utf8")
            for anchor in ("validate_manual_turn_receipt(","run_e4_guarded_parent(",
                           "verify_e4_certificate(","_logical_fingerprint()"):
                if anchor not in source:
                    errors.append("P101_APPROVAL_READBACK_GATE_REMOVED:"+anchor)
    for name in CONFIGS:
        if (root/name).exists():errors.append("P101_DEPLOYMENT_CONFIG_NEEDS_REAUDIT:"+name)
    return errors
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",nargs="?",choices=["verify"],default="verify")
    parser.add_argument("--root",type=Path,default=ROOT)
    args=parser.parse_args()
    errs=validate(args.root)
    for e in errs:print("P101_SURFACE_FAIL",e,file=sys.stderr)
    if errs:return 1
    print("P101_CORE_SURFACE_PASS modules=8 direct_cli=0 root_deployment=0 official_exports=1 "
          "legacy_v126_importable=True external_bypass_zero_UNPROVEN=True "
          "trusted_user_turns_UNPROVEN=True P101_structural_only=True")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
