"""E1 CI preflight: catch test runner collisions before expensive native tests.

No network, model, private files or V123/E2 approval logic. The classic
unittest.TestCase.run collision caused an entire E1 CI run to crash *after*
hundreds of passing tests. A cheap AST check prevents that runtime failure.
"""
from __future__ import annotations

import ast
from pathlib import Path

HERE=Path(__file__).resolve().parent


def _testcase_class(tree: ast.AST) -> list[ast.ClassDef]:
    candidates=[]
    for node in ast.walk(tree):
        if not isinstance(node,ast.ClassDef):
            continue
        bases=[ast.unparse(b) for b in node.bases]
        if any(base in ("unittest.TestCase","TestCase") or
               base.endswith(".TestCase") for base in bases):
            candidates.append(node)
    return candidates


def find_testcase_run_override(source: str) -> list[str]:
    problems=[]
    for cls in _testcase_class(ast.parse(source)):
        for stmt in cls.body:
            if isinstance(stmt,(ast.FunctionDef,ast.AsyncFunctionDef)) and stmt.name=="run":
                problems.append(cls.name+".run")
    return problems


def validate_e1_test_runtime() -> dict:
    target=sorted({
        *HERE.glob("test_v201_e1*.py"),
        *HERE.glob("test_v202_e1*.py"),
        *HERE.glob("test_v203_e1*.py"),
        *HERE.glob("test_v204_e1*.py"),
        *HERE.glob("test_v205_e1*.py")})
    if len(target)<5:
        raise RuntimeError("E1_RUNTIME_TEST_HARNESS_CENSUS_MISSING")
    bad={}
    for file in target:
        if file.is_symlink() or file.stat().st_size>1024*1024:
            raise RuntimeError("E1_RUNTIME_UNSAFE_TEST_FILE:"+file.name)
        problems=find_testcase_run_override(file.read_text(encoding="utf-8"))
        if problems:
            bad[file.name]=problems
    if bad:
        raise RuntimeError("E1_RUNTIME_TESTCASE_RUN_SHADOWED:"+str(bad))
    return {"preflight":"PASS",
            "e1_test_files_checked":len(target),
            "unittest_run_overrides":0,
            "private_research_data_opened":False}


if __name__=="__main__":
    print(validate_e1_test_runtime())
