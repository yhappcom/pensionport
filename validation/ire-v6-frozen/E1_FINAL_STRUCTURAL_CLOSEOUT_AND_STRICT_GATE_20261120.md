# E1 최종 마감 증빙 — 2026-11-20 KST

## 변경 금지된 합격 기준과 판정

- **E1: 엔진 전체 구조 — 입력·검토·승인·저장 경로가 하나로 연결.**
- **판정: PASS, 합성 입력에 대한 동결 실제 소프트웨어 실행 구조 연결.**
- V166 과거 E1 PASS 및 V202 실제 반례 RED/FAIL 이력은 삭제하지 않고 모두 보존한다. V203 이후 정상 native host 원본유래 경로를 구현했으며 V204 비주장 윈도우와 교차 구간 참조 결함을 보완, V205 E1 테스트 실행 API 충돌을 검문한다.
- **E2: READY / NOT STARTED**, E3–E5: NOT RUN. E2 합격 전 다음 단계 진행 금지.
- `main`, 원본 SRT·owner-private SQLite, 금융 지식/포트폴리오, 동결 V123/V126/V127/V128 미수정. 작업 코드와 검증자료는 PR #73 Draft에 보존.

## 기존 E1 실패를 되풀이하지 않는 실제 코드 경로

```
V176 원본 SRT 바이트·자막 전수·해시 검문
   → ChatGPT 형식 원본 검토·원장 head 고정
   → 원본유래 V6 atomic exchange + 명시 source qualifier anchor
   → 신규 native V6 TransactionStore + submit_host_atomic_batch
   → 실제 신규 host event/bundle SHA
   → 해당 host SHA에 매여 있는 명시 ChatGPT 검토·관계 입력
   → 동결 V123 검토 → V127 구간 checkpoint/parent seam
   → 동결 V128 부모 전체 staging/atomic commit
   → 동결 V126 private SQLite 원자 저장
```

성공한 E1 합성 사례: 4 original SRT cues, 3원자, 2자식. 연구 지식 2건 저장, source-only 1건 격리, 부모 발행 1건. 기존 V166에서 먼저 만든 host 영수증을 재사용하지 않으며, 새 V176 유래 영수증의 변경 불가능한 재실행·해시를 V126에서 재검문한다.

안전 부정 사례: 금융 공식 근거 바이트 누락 → 전체 발행 0; owner SHA·검토 head 변조 → 거부; 화자·입장·적용 시점 무단 승격 → 거부; 자식/원문 변경 → 거부; 2회 동일 실행 → 지식 중복 저장 0. 별도 `NO_ATOM` 윈도우가 포함된 native batch는 실제 허용, `UNRESOLVED`이면 원장 모델/검토 증빙 증가 없이 거부. 자식 범위를 벗어난 조건·문맥·숫자는 정보를 조용히 삭제하지 않고 명시적 parent seam이 없으면 실패 폐쇄한다.

## 최종 증빙과 정확한 범위

| 관문 | GitHub Actions | 결과 |
|---|---|---|
| 원본유래 V6/V123/V128 E1 회귀 + V204/V205 런타임 대응 | https://github.com/yhappcom/pensionport/actions/runs/44720035936 | **435/435 PASS** |
| 완전 체크아웃 `ire.v6.prepush --strict` | 동일 run, strict step | **8/8 PASS**; `ALL_MANDATORY_SOFTWARE_CHECKS_PASS_ENGINE_QUALITY_NOT_CERTIFIED` |
| 독립 클린룸 코드·기존 V5 보호 | https://github.com/yhappcom/pensionport/actions/runs/44720035791 | **1,224 tests PASS**, protected scope/bytes 가드 통과 |
| 중복 PR 정리 | https://github.com/yhappcom/pensionport/pull/74 | 중복 Draft **closed, unmerged**, 기록 보존 |
| 단일 E1 검증 브랜치 | https://github.com/yhappcom/pensionport/pull/73 | **Draft, not merged to main** |

검증 코드 SHA(새 문서 기록 이전): `fe0120f99899a93ee61f857647d6c11e18063798`. GitHub PR merge checkout에 따라 Actions의 `git rev-parse HEAD`는 임시 merge SHA일 수 있으며, CI의 정상 처리와 브랜치 head는 구분한다. 이 문서 기록 이후 전체 필수 CI를 재실행해 최종 보고할 것.

## 절대 합격 처리하지 않는 항목

**E1의 합성 구조 검증 PASS를 E2~E5 또는 실제 금융 사실 승인으로 확장하지 않는다.** 실제 사용자 영상의 13개 자식 전체 승인, 실제 ChatGPT 두 사용자 턴 의미 검증, 금융시점·현행법 독립 확인, 승인된 지식의 실물 발행, 투자 자문 적합성, 독립 골드 precision/recall은 본 검사로 입증하지 않았다. 관련 성공 플래그 `False`를 유지한다.

이후 E1 반복 테스트만 추가하는 것은 기본값이 아니며 **E1에서 새 회귀/안전 결함을 재현하는 경우**에만 같은 관문을 다시 연다. 다음 작업 위치는 정확히 **E2 의미 원자 검증**이며 E2 PASS 전 E3 작업을 진행하지 않는다.
