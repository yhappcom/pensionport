#!/usr/bin/env python3
"""V3.0 protected branch diff+privacy checks, separate from editable contract.

This enforces no writes to frozen V1/V2/V3/V4/V5 research files and checks
new public research documents for identifiers/secret strings. It is a repo
safety audit, NOT a substitute for branch protection or external human audit.
"""
import argparse
import re
import subprocess
from pathlib import Path
from v30_verified_core import TRUST_PINS,blob_sha,guard,policy_gate

ROOT=Path(__file__).resolve().parents[1]
FROZEN_PARENT="f978f5e70b166d4da6663566251aaa0084534932"
PUBLIC_ID=re.compile(r"(?<!\d)\d{6}[- ]?[1-4]\d{6}(?!\d)")
LIKELY_SECRET=re.compile(
    r"(?i)(?:-----BEGIN (?:RSA |EC )?PRIVATE KEY-----|"
    r"(?<![A-Za-z0-9_])(?:api_key|secret_key|client_secret|private_token)"
    r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{24,})")
FINANCIAL_PRIVATE=re.compile(
    r"(?i)(?:account_number|real_portfolio|personal_holdings|"
    r"owner_income|owner_balance)\s*[:=]\s*['\"]?\d{5,}")
ALLOWED=[
 re.compile(r"^v30/[A-Za-z0-9_./-]+\.(?:md|json)$"),
 re.compile(r"^scripts/v30_[a-z0-9_]+\.py$"),
 re.compile(r"^scripts/verify_v30_[a-z0-9_]+\.py$"),
 re.compile(r"^scripts/audit_v30_deep_readonly\.py$"),
 re.compile(r"^\.github/workflows/v30-integrated-research-gate\.yml$"),
]
def git(root,*args):
    p=subprocess.run(["git",*args],cwd=root,capture_output=True,text=True)
    guard(p.returncode==0,"GIT_REPOSITORY_VERIFICATION_FAILED_"+p.stderr[:100])
    return p.stdout.strip()

def audit(root):
    policy_gate(root)
    guard(git(root,"cat-file","-t",FROZEN_PARENT)=="commit",
          "FROZEN_PARENT_COMMIT_NOT_AVAILABLE_FETCH_FULL_HISTORY")
    changed=git(root,"diff","--name-only",FROZEN_PARENT,"HEAD").splitlines()
    guard(changed,"NO_V30_SOURCE_DIFF_TO_AUDIT")
    for f in changed:
        guard(not f.startswith("/") and ".." not in Path(f).parts
              and any(p.fullmatch(f) for p in ALLOWED),
              "MODIFIED_FROZEN_HISTORICAL_FILE_OR_UNAPPROVED_PATH_"+f)
        path=root/f
        guard(path.is_file(),"DELETED_OR_NONREGULAR_SOURCE_FILE_"+f)
        guard(path.stat().st_size<1_000_000,
              "OVERSIZED_PUBLIC_RESEARCH_ARTIFACT")
        if f.endswith((".md",".json")):
            body=path.read_text(encoding="utf-8")
            guard(not PUBLIC_ID.search(body) and
                  not LIKELY_SECRET.search(body) and
                  not FINANCIAL_PRIVATE.search(body),
                  "SUSPECTED_PERSONAL_OR_SECRET_DATA_IN_PUBLIC_ARTIFACT_"+f)
    for file,expected in TRUST_PINS.items():
        guard(blob_sha(root/file)==expected,
              "PROTECTED_SOURCE_OR_V5_POLICY_TAMPERED_"+file)
    return {
      "schema":"V30_REPO_DIFF_AND_PRIVACY_SAFETY_V1",
      "frozen_parent":FROZEN_PARENT,
      "changed_files_count":len(changed),
      "frozen_protected_sources_checked":len(TRUST_PINS),
      "changed_files_all_allowlisted":True,
      "public_markdown_json_scanned_for_sensitive_patterns":True,
      "history_overwritten":False,
      "branch_protection_enforced_by_this_script":False,
      "release_ready":False,
    }

if __name__=="__main__":
    try:
        x=audit(ROOT)
        import json
        print(json.dumps(x,sort_keys=True))
    except (ValueError,OSError) as e:
        import json
        print(json.dumps({"gate":"FAIL","error":str(e)}))
        raise SystemExit(1)
