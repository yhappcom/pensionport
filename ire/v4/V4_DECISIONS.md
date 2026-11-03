# IRE V4 설계 결정 기록 (ADR 요약)

2026-11-03. 모든 결정은 **P0 호스트 실증 전의 조건부 설계안**이다.

## ADR-001 — 실행 호스트

**결정:** `ChatGPT Work`를 API 없는 장시간 실행의 **첫 실증 후보**로 선택. 기존 일반 Chat는 설계/진단/짧은 파일 처리용, Work가 실제 모델 반복 호출과 비공개 파일 연계를 할 수 있는지 직접 측정한다.

**근거:** OpenAI 제품 문서에서 Work의 장시간 다단계 수행, 앱·파일 연계, 작업 지속을 설명한다. Work 내에서 코드/비공개 파일/연구 루프를 무제한 실행할 수 있다는 보장은 찾지 못했다.

**보류/조건:** 계정별 Work 접근, 파일 연결, 도구 실행, 작업 재개, 실원본의 안전한 처리 가능 여부가 미확인. `host_probe`에서 하나라도 실패하면 변경 승인 금지. **Python이 Work를 API처럼 호출할 수 있다고 가정하지 않는다.**

## ADR-002 — 하나의 요청과 하나의 응답 구분

**결정:** U1(`ONE_USER_REQUEST`)을 필수, U2(`ONE_HOST_TASK`)를 실증 목표, U3(`ONE_CHAT_RESPONSE`) 보장 금지로 명세화. 도중 승인이 필요한 환경에서는 `PAUSED_APPROVAL`로 투명하게 종료/중지.

## ADR-003 — V3 보존/재사용

**결정:** V3 SHA/cue·immutable correction·evidence WAL·금융 의미·relation/advisory gate는 read-only adapter 기반 재사용. V3 310개 테스트가 새 코드에서 그대로 통과해야 함. `main`과 기존 연구 기록 불변.

## ADR-004 — 평가 진실성과 숨김 골드

**결정:** 원본 인용 일치, 금융 의미 독립 정확도, 법령 사실 인증, 사용자 적합성의 네 가지 신뢰도를 분리. 과거 모델에 노출된 15개 source-only 태스크를 동일 모델의 독립 blind holdout으로 사용하지 않는다.

## ADR-005 — 주장 단위 부분 릴리스

**결정:** 특정 미검증 명제를 `OPEN`으로 격리하면서 다른 독립적으로 확인된 주장에 대한 연구 보고는 계속. `VERIFIED`와 `ADVISORY_ELIGIBLE`은 근거와 조건이 충족된 최소 범위에서만 허가한다. V3 전체 배치 단위 차단의 연구 생산성 한계를 개선하되 자문 안전장치는 완화하지 않는다.

## ADR-006 — 호스트 제약 우회 금지

**결정:** 웹 UI를 비공식 모델 API처럼 자동 클릭하는 구조, 비밀 계정 인증 우회, GitHub Actions에 원본 업로드, 승인 없이 개인 투자 행위를 실행하는 구조 배제.

## 미해결 질문과 책임

| 질문 | 상태 | 해소 방법 |
|---|---|---|
| 실제 사용자의 Work 액세스가 있는가? | 미확인 | P0 Capability Probe |
| Work가 같은 작업에서 12개의 모델 의미 분석을 연속 수행하는가? | 미확인 | P0 실원본 12창 |
| 작업의 중단/재개가 호스트에서 이어지는가? | 미확인 | P0 장애 실험 |
| 공식 원본/비공개 SRT에 안전하게 접근할 수 있는가? | 미확인 | P0 권한 및 경로 검증 |
| 독립 검토자와 신규 숨김 골드 데이터를 확보할 수 있는가? | 미확인 | P4 검토자·표본 등록 |
| 791편을 어느 단위로 처리할 수 있는가? | 미확인 | P3/P5 처리량·호스트 한도 실측 |

## 참조

- https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex
- https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt
- https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt
- 기존 GitHub `yhappcom/pensionport`, IRE V3 Draft PR #11 (2026-11-03 기준)