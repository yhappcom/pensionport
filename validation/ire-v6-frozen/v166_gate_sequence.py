"""V166 E1->E7 ordered verification status gate.

Enforces phase order only. Not a financial/semantic success certificate.
"""
from __future__ import annotations

import json
from pathlib import Path

STEP_NAMES = ("E1", "E2", "E3", "E4", "E5", "E6", "E7")
TARGETS = (
    ("엔진 전체 구조", "입력·검토·승인·저장 경로가 하나로 연결"),
    ("원자 주장 처리", "질문·의견·가설·금융 사실을 구분하고 조건·예외 보존"),
    ("ChatGPT 최종 검증", "승인·보류·격리 결과가 정확히 전달"),
    ("승인 관문", "적법한 승인 입력은 통과하고 부적합 입력은 차단"),
    ("지식 통합", "승인된 13개 구간만 원자적으로 저장"),
    ("오류·재실행 검증", "중복 저장·부분 발행·원문 변조 방지"),
    ("실제 자문 연결", "저장된 지식을 검색하고 원문 근거까지 역추적"),
)
VALID_STATES = {"NOT_RUN", "IN_PROGRESS", "FAIL", "BLOCKED", "PASS"}
STATUS_SCHEMA = "IRE_V166_E1_E7_ORDERED_ENGINE_VERIFICATION_STATUS_V1"


class PhaseOrderViolation(ValueError):
    pass


def _guard(condition: bool, name: str) -> None:
    if not condition:
        raise PhaseOrderViolation("V166_PHASE_" + name)


def check_phase_order(doc: dict) -> dict:
    """Reject skipped steps or claimed passes without a separately linked record.

    A proof path is necessary but NEVER sufficient for semantic accuracy; this
    function does not inspect any test logs, private sources or quality gold.
    """
    _guard(type(doc) is dict and doc.get("schema") == STATUS_SCHEMA, "SCHEMA")
    steps = doc.get("sequence")
    _guard(type(steps) is list and len(steps) == 7, "CENSUS")
    first_unpassed = None
    for i, (step, target) in enumerate(zip(steps, TARGETS)):
        _guard(type(step) is dict, "ROW")
        _guard(step.get("step") == STEP_NAMES[i], "ORDER")
        _guard((step.get("target"), step.get("criterion")) == target, "CRITERIA_DRIFT")
        state = step.get("status")
        _guard(state in VALID_STATES, "STATUS")
        _guard(type(step.get("evidence_paths")) is list, "EVIDENCE")
        _guard(type(step.get("blockers")) is list, "BLOCKERS")
        _guard(type(step.get("retest_required")) is bool, "RETEST_FLAG")
        if state == "PASS":
            _guard(first_unpassed is None, "SKIPPED_PREVIOUS")
            _guard(type(step.get("completed_at")) is str and
                   bool(step["completed_at"].strip()), "PASS_WITHOUT_TIMESTAMP")
            _guard(bool(step["evidence_paths"]), "PASS_WITHOUT_EVIDENCE_POINTER")
            _guard(not step["blockers"] and not step["retest_required"],
                   "PASS_WITH_OPEN_DEFECT")
        else:
            _guard(step.get("completed_at") is None, "UNPASSED_COMPLETE_DATE")
            if first_unpassed is None:
                first_unpassed = i
            else:
                _guard(state == "NOT_RUN", "LATER_STEP_STARTED_EARLY")
                _guard(not step["evidence_paths"] and not step["blockers"]
                       and step["retest_required"] is False, "LATER_STEP_EVIDENCE_BEFORE_TURN")
        if state in ("FAIL", "BLOCKED"):
            _guard(bool(step["blockers"]) and step["retest_required"],
                   "FAILED_WITHOUT_BLOCKER_AND_RETEST")
    expected = "COMPLETE" if first_unpassed is None else STEP_NAMES[first_unpassed]
    _guard(doc.get("current_step") == expected, "WRONG_CURRENT_STEP")
    _guard(doc.get("pending_advance_approval") is False, "AUTOMATIC_ADVANCE_FORBIDDEN")
    _guard(doc.get("independent_gold_certified") is False or expected == "COMPLETE",
           "PREMATURE_INDEPENDENT_GOLD_CLAIM")
    _guard(doc.get("one_video_poc_pass") is False or expected == "COMPLETE",
           "PREMATURE_VIDEO_COMPLETION")
    return {"current_step": expected, "passed_steps": first_unpassed if first_unpassed is not None else 7,
            "next_step_may_start": expected != "COMPLETE"
            and steps[first_unpassed]["status"] == "NOT_RUN",
            "semantic_or_financial_success_certified": False}


def read_and_check(path: str | Path) -> dict:
    return check_phase_order(json.loads(Path(path).read_text(encoding="utf-8")))


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    result = read_and_check(here / "V166_E1_E7_STATUS.json")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
