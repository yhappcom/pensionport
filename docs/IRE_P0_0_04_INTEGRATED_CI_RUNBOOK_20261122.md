# P0-0-04 — Python 3.11.18 단일 HEAD 전체 소프트웨어 통합 CI 종료 보고 (2026-11-22)

**판정:** 소프트웨어 정합성 CI PASS / 실제 E1~E5 금융 연구 최종 승인 HOLD / 개인 투자자문 GO 아님.

기준 커밋: `f94fb5c8d59527abf531b5e774ffdaa7c5648b97`. [GitHub Actions 실행 44982460084](https://github.com/yhappcom/pensionport/actions/runs/44982460084) — **6개 작업 모두 success**. 저장소는 `audit/full-repository-snapshot-20261122` 단일 연구 브랜치와 `main` 두 브랜치만 유지하며, `main`은 `d613fd201f4bb077f1ccc74d28dee937b11bfcb2`로 불변.

## 수행 범위와 실제 결과

| 단일 SHA 검증 묶음 | 실측 결과 |
|---|---:|
| 브랜치·98역사 HEAD·연구 HOLD·상태·27 Actions 정책 | 59 PASS |
| V60~V99 frozen source/semantic tests | 871 PASS |
| V100~V199 E3/E4/E5·의미·근거·V123/V126 tests | 2,692 PASS |
| V200~V242 E1/E2 최신 원자·연계 tests | 836 PASS |
| version 미부여 공식자료·독립평가 프로토콜 9개 파일 | 89 PASS |
| **정책 및 frozen 그룹 소계** | **4,547 PASS** |
| V6 커널(엄격 prepush) | 647 PASS |
| IRE/V3 기반 시험 | 310 PASS |
| V5 코어 시험 | 855 수행, 2 SKIPPED |
| V5 앱 시험 | 59 PASS |
| V5 사전검사 및 결정론적 1턴 연구 안전검문 | 59 단계 PASS / one_turn PASS, **실제 투자 연구 완료 아님** |

엄격 드라이버는 위 V5 검사를 일부 반복 실행하므로 전체 시험 숫자를 단순 합산해 '독립 수천 건 정확도'라고 주장하면 안 된다. 각 작업은 `actions/checkout@v4`, Python `3.11.18`, 동일 GitHub `GITHUB_SHA`를 사용하며, 기존 V6 `prepush --strict --expected-sha "$GITHUB_SHA"`의 전체 checkout 검사를 통과했다. 25개 퇴역 워크플로를 통합 브랜치 push에 다시 묶지 않았다.

## 실제 실패와 근본 원인·해결

1. [초기 RED CI](https://github.com/yhappcom/pensionport/actions/runs/44982311913): V202 테스트 2개는 V228에서 E2가 원본 검토 중 HOLD로 이동했는데도 `E2_READY_NOT_STARTED`를 정답으로 요구. **원장 값은 수정하지 않고** 테스트가 E2 진행·보류와 E3/E4/E5의 미승인을 보도록 정정.
2. 같은 초기 CI의 V177 6건은 별도 `python script.py` 하위 프로세스가 repo 루트를 `PYTHONPATH`에서 찾지 못한 것이 원인. frozen matrix에 `PYTHONPATH: github.workspace` 명시하여 동일 프로그램·원본·승인 없이 복원 경로 회귀검사를 복구.
3. [완전 GREEN CI](https://github.com/yhappcom/pensionport/actions/runs/44982460084): V100~V199 2692/2692, V200~V242 836/836, V60~V99 871/871, 공식 89/89, 관리 59/59, 엄격 V3/V5/V6 및 P4 리트리벌까지 6개 작업 success.

## 완료판정 한계·차단

- ETF `LVE7XN_esTc` 실물: 250 cue / 68 미승인 후보 / 13 child, **정식 E3 V123 승인 0/13 / E5 실제 발행 0**. 현행 E1~E5 실제 전체 승인·E2 독립 Gold·E4 owner 금융근거는 HOLD를 유지.
- 오프라인 공식자료 바이트·정책 검사와 '오늘 현재 법률의 적용성'은 다르다. 살아있는 법령 재검색·개인 포트폴리오 적합성은 미검증.
- 본 CI는 기존 레거시 단일 시스템 스냅샷의 회귀검사이지 실제 사용자 두 번의 ChatGPT 의미판정 또는 개인 투자권고를 생성하지 않았다.
- `P0-0-04`가 체크리스트 자체 PASS로 확정되기 전 `P0-0-05`는 BLOCKED. 다음 P0-0-05는 11개 분기, 42개 HOLD PR 및 Issue #48/#50 실제 채택·격리 원장과 평가를 진행한다.

[구조화된 전 단계 영수증](IRE_P0_0_04_INTEGRATED_CI_CLOSEOUT_20261122.json)과 [체크리스트](IRE_STRICT_SEQUENTIAL_EXECUTION_CHECKLIST_20261122.md)를 함께 확인한다.
