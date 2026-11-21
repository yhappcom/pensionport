# V216.1 — ETF 실물 원본 C00072 차트 근거 혼입 수정·동결 V6 재검사 (2026-11-21)

**E2 결과: 실제 비공개 원본 기반 원자 수정본 동결 구조 PASS / 화자·금융 의미·독립 정답 E2 HOLD.** 기존 V215.2 교환·원장 및 V216 내부 검토 파일을 덮어쓰지 않았다. 이 문서는 원본 250개 자막 전문이나 개인 비공개 JSON을 GitHub에 공개하지 않는 검증 요약이다.

## 실물 수정

- 실제 사용자 Library `/박곰희TV_원본확보/1-70.zip`의 `LVE7XN_esTc` 원본 SRT 재확인: SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`, 250 cue.
- V215.2의 `C00072`에는 음성·화면을 확인해야 하는 167번 차트 설명이 **primary** 근거로 연결되어 있었다. 시각 근거가 없는 상태에서 그래프별 추적차 크기를 금융 사실로 승인해서는 안 된다.
- **V216.1 비공개 수정본:** `C00072`의 primary를 167에서 **168번의 텍스트 독립 평가 발화**로 재앵커하고, 원문에 명시되지 않은 추적차/추적오차 정의를 결론으로 주장하지 않도록 원자 명제를 좁혔다. 167번은 UNRESOLVED로 복귀한다. 163~167번 영상 그래프 자체에 대한 주장은 그대로 보류.
- 기존 66개 원자 중 하나의 설명·출처만 정정해 **66개 후보 수 유지**. 저자의 화자 음성 증명, 금융 용어의 현행 규정 적합성, 외부 independent gold는 여전히 미확정. `speaker=UNKNOWN`, `stance=UNRESOLVED` 및 미승인 상태 유지.
- 168번 자막의 `needs_original_audio_or_screen` 플래그는 임의로 해제하지 않았다. 따라서 위험 cue 24개, 위험 primary 원자 3개(`C00034`, `C00061`, `C00072`)는 V216.1 보수적 검사에서도 유지되나, **C00072의 167번 차트 설명에 대한 primary 의존은 제거**되었다. 새 수치나 화면 판정을 생성하지 않았다.

## 개인 Library에 보존한 새로운 비공개 실물 3종

| 파일 | SHA-256 |
|---|---|
| `V216_PRIVATE_REAL_ETF_250_CORRECTED_C00072_NATIVE_V6_UNAPPROVED.json` | `bd96128facaf030bd500e899d39445291d5efdd44e540ce01a7cb3a588be851f` |
| `V216_PRIVATE_REAL_ETF_250_CORRECTED_C00072_CUE_COVERAGE_HOLD.json` | `e477095a0e1f9d18f10e0a9044a3db41a07548c95b0953ff6ebd1ce5f00926ea` |
| `V216_PRIVATE_REAL_ETF_250_CORRECTED_C00072_FROZEN_AUDIT_HOLD_RECEIPT.json` | `796992c461271f383143e45a29218a7a16cd166f0984f45319db0fc737d67fcd` |

이들 세 파일은 GitHub에 업로드하지 않았다. 기존 원본 V215.2 교환 SHA `a4079f9ded76a280614f83d3e84bfddf49b2bf98ac5e81ff810ea5f259bf01ad`는 불변이다.

## 실행 검증

실제 GitHub Actions 성공 workflow에서 배포된 공개 코드-only 패키지의 **동결 `ire.v6.atomic_exchange.audit_host_atomic_exchange`를 소유자 원본 SRT에 직접 적용**했다.

| 동결 V6 구조 검증 항목 | 결과 |
|---|---|
| 실제 원본 250개 원문 및 변경 없는 SHA | PASS |
| 수정본 native 미승인 원자 수 | 66 |
| cue당 primary 없는 UNRESOLVED | 187 |
| 동결 atom digest | `83131c27920c24ce1f6961bb7033bf179f4397cf25879eccdb58437a5b9abc22` |
| 원자 구조 감사 | PASS |
| 원자 의미의 독립 완전성 / 숫자·법규 진실성 | **미승인** |

같은 비공개 원본 교환과 cue coverage를 신규 `v216_e2_private_residual_evidence_guard`로 재검사해 출처 재연결 정합성 PASS, 위험 cue 24개, 위험 primary 3개, 위험 context 13개, 자동 승인·병합 0을 확인했다.

이전 `V216` 합성 코드-only CI 322개는 [run 44829869066](https://github.com/yhappcom/pensionport/actions/runs/44829869066)에서 **322/322 PASS** (현행 E2 251, 과거 E2/V176 53, E1 18)이다. 이 CI가 개인 원본을 실행한 것은 아니며 본 문서의 실물 결과는 비공개 로컬 실행으로 얻었다.

## E2 현재 잔여사항

1. V176 이전 owner SQLite 사건/원자별 chain 및 역사 원자 61/69/71과 현재 66개 사이 출처 기반 동치 검문은 미완료.
2. 비공개 원음/원화면 미확보. 음성 단어 혼동(`C00034`, `C00061`)과 24개 시청각 위험 cue 검증 미완료.
3. 187개 primary 없는 자막을 **전부 누락 주장으로 계산할 수는 없다**. 문맥/담화/비주장 여부와 원자 누락 여부를 독립 점검하는 정답셋 미완료.
4. 동일 ChatGPT 의미 재검토는 사전 블라인드 외부 independent gold가 아니며 precision≥95%·recall≥98%·high-risk miss=0 실측 인증 불가.
5. **E2 최종 HOLD / E3~E5 NOT_RUN.** 실제 투자 지식 승인·발행 0건, `main`과 동결 V6/V123/V126/V128 불변, PR #75 Draft 미병합.

기존 V215.2 / V216 / V216.1 증거는 append-only 이력으로 보존한다. 차트 primary 결함의 수정은 확인했지만 현장 전체 의미 검증을 PASS로 승격하지 않는다.
