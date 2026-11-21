# V242 E1 원인 재진단과 B0013 교차조건 보존형 수선계획 (2026-11-21)

## 진단 기록 — V241 성공 범위의 교정

B0013의 실패는 **무주장 자막이 아니라 V238의 과도한 atom 단위 격리**로 발생한다. B0013 원자 `C00057`은 246번 자막이 주장 근거이고 244·245·247번 자막이 구간 내부 조건·문맥이다. 그러나 45·46·47번(인덱스 ETF 대상) **3개 외부 조건·문맥**이 있어 V238이 원자 전체를 sidecar로 빼고, local count=0이 되어 V241의 안전 사전검문에서 HOLD한다. 이때 V6 엔진 자체는 전체 원문을 참조할 수 없는 PARTIAL 계약을 갖는다. 원자 전체가 없음으로 처리됐지만 구간 내부 주장은 존재한다. 결함 종류는 **구간 간 조건 외부참조 + all-or-nothing 격리 정책으로 인한 구조적 기아(starvation)**이고, 실제 의미 미승인과 별개다.

B0013 source: 241–250, 원자 `C00057` 출처 자막 246, 조건 45·46·47 및 244·245, 문맥 45·46·47·244·245·246·247, speaker UNKNOWN, stance UNRESOLVED. `proposition`은 원문 동시점 유사 ETF 비교 추천. 45–47의 적용 대상 제한을 버리면 **범용 ETF 추천으로 잘못 승격될 위험**이 있으므로 원래 원자/공식 재검토 packet을 보존한다.

## 수선 불변식과 작업순서

1. **V242 원본-bound 이중계층 projection 설계:** `C00057`의 SOURCE_LOCAL_PROVISIONAL projection은 source_refs=원문 246, 조건·문맥=**자식 내부 244·245·246·247**만 갖는 **호스트 구조 기록 전용** 입력으로 생성한다. proposition/kind/stance/speaker는 parent와 **정확히 동일**하게 유지하고 `stance=UNRESOLVED`, `e3=false`, `e4=false`, `e5=0` 강제. 외부 45·46·47 조건·문맥은 **원래 parent atom 바이트 SHA + 각 cue source SHA + V237·V234 evidence SHA**가 결합된 별도 `PARENT_QUALIFIER_ESCROW_REQUIRED_FOR_E3` 불변 sidecar로 남긴다. 과거 V228 원자는 수정하지 않는다.
2. **분리 허용의 엄격한 한계:** parent atom의 `source_refs`와 `numeric_references`가 모두 자식 범위 안에 있고, 외부 인덱스 전부가 `condition_cue_indices` 및 `context_cue_indices`에 있으며, local context/condition에서 추상적 설명이 아니라 원문 텍스트를 복원할 수 있는 경우에만 projection 후보. **외부 직접 인용·숫자·예외·반박 근거가 있다면 즉시 HOLD**. parent SHA와 child manifest SHA를 변경 불가능하게 바인딩.
3. **실제 V6 host 실행:** V241과 동일한 기존 `TransactionStore`, `audit_host_atomic_exchange`, `audit_model_anchors`, V145 원문격리, 보호 prior 145개와 68 relation을 사용한다. 신규 독립 B0013 `sqlite`에 단 한 번 원자 1개의 **구조적·미승인** host event를 기록하고 새 connection의 hash chain을 재생한다. 기존 B0001–B0012 DB 12개, V232 host DB, V233 parent checkpoint는 수정하지 않는다.
4. **차단 재시험:** 외부 45·46·47 quote/SHA, claim proposition, speaker/stance, owner segment, child scope, sidecar SHA, 원본 ZIP SHA, prior source SHA, duplicated child receipt, 진짜 의미 승인을 가장하는 선언이 변경되면 host 진입 **이전** 또는 final approval 이전에 차단한다. sidecar 없는 projection은 정식 V123/E4 입력에 절대 공급 금지. 현재 `C00057`을 승인할 공식 금융·ChatGPT 심사 데이터는 없다.
5. **최종 결과 보고:** 실제 자식 V6 structural receipts 13/13을 달성하더라도 **실제 13 child E3 승인 0**, **E4 봉인 0**, **E5 발행 0**과 E1 전체 HOLD를 유지한다. 21개 전체 cross atom의 공식 의미검토 필요는 별도 표시한다. 회귀 CI 통과와 실물 원본 실행을 구분한다.

## 완료 기준

- 13번째 **B0013 host 구조 커밋**, 1개 provisional atom, 45·46·47 조건 3개 전수 sidecar 보존; 원본 V228/원자 SHA 불변; 13개 DB 재개봉 무결성 PASS; 승인 0 유지.
- V242 fixture 양성/적대 회귀시험 PASS, GitHub Actions green, 보호 `main`/동결 원본 불변.
- 전체 E1 PASS는 여전히 **E2 의미·E3 실제 검토·E4 공식 근거와 적법 봉인·E5 원자적 발행**이 별도로 완료될 때만 판정.

## 안전 주의

자식-local projection은 원래 parent `C00057`의 완전한 의미 representation이 **아니다**. 호스트가 받아들였다는 이유로 `verified`/approved로 이름을 바꾸거나 `parent-context-verified`라 주장하는 것은 금지된다. 인정 가능한 것은 **원본 근거가 묶인 미승인 구조적 staging**뿐이다.
