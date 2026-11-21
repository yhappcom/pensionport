# V214 — ETF 실제 원본 250 cue, 최신 동결 V6 직접 검사, 화자·원자·정답 상태 (E2 HOLD)

**2026-11-20 KST** · GitHub Draft PR #75 · `main` 및 동결 승인 경로 미수정.

## 1. 이번에는 합성시험만 한 것이 아니다

사용자 소유 개인 Library `1-70.zip`의 `LVE7XN_esTc` 실제 SRT 원본 **250개**, 원본 SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`를 사용했다. V210에 보존된 **57개 미승인 ChatGPT 원자 후보**의 바이트를 복원했고 해당 JSON SHA-256 `fb82a04335d5ef2bdc99f3eb502f3453eedaa76693cc5a14c55d668d5bdee71b`를 **원본 파일 바이트 자체로 고정**했다.

GitHub Actions는 합성 ETF 시험만 했지만, 별도의 **코드 전용 아티팩트** `e2-v214-code-only-native-validator` (run 44759374878, artifact ID 14640087173)를 다운로드하여 **현재 실제 동결** `ire/v6/atomic_exchange.py` + V176/V210/V214 코드를 **비공개 로컬 실행환경에서 그대로 실행했다**. 이 경로는 실제 원본 SRT/개인 JSON을 GitHub 또는 GitHub Actions에 업로드하지 않는다. 코드 전용 아티팩트와 실물 연구 영수증은 서로 구별한다.

### 최신 동결 native V6 실물 검증

| 원본 직접 검문 | 실측 |
|---|---:|
| 원본 SRT SHA 및 자막 전수 | 250/250 |
| 원본 기반 연구 창 | 13개 (20 cue 단위) |
| V210 기존 미승인 주장 후보 | 57 |
| **동결 V6 `audit_host_atomic_exchange()` 직접 구조검사 PASS** | **55개 미승인 원자** |
| 부적합 원자 후보 격리 | 2 (E2REAL-036, E2REAL-050) |
| 개별 원자 최종 분류를 보류한 원본 자막 | 195 |
| E2 별도 출처 판정이 연결한 문맥 조건 자막 | 15 |
| E2 별도 출처 판정이 연결한 예외 자막 | 2 |
| 정식 V6 stance=UNRESOLVED 및 speaker=UNKNOWN | 55/55 |
| 전체 영상 E2 최종 의미 승인 | **0 (HOLD)** |

`E2REAL-036`은 원문에서 지수 20%·ETF 18%를 언급해도 검토자가 산출한 `−2%p`를 화자가 말한 숫자로 서술해서는 안 되므로 차단했다. `E2REAL-050`은 가상 ETF 시장가격과 NAV에서 산출한 `−83원` 및 약 `−0.4682%`를 **직접 발언한 숫자**로 승격하지 않아 차단했다. 이는 계산 자체가 틀렸다는 판정이 아니라 **수치 유도와 원문 인용의 출처/형식 분리**이다.

`V214`는 전체 250개 cue에 명시적 `CANDIDATES` 또는 `UNRESOLVED` 항목을 제공한다. 195개의 UNRESOLVED는 모두 원자 누락 195건이라는 뜻이 아니다. 하나의 후보가 여러 cue를 문맥으로 포함할 수 있으며, 각 cue의 원자 추출 완전성을 아직 인증하지 않았다는 뜻이다. 누락을 `NO_ATOM`으로 자동 확정하지 않는다.

**실물 동결 V6 직접검사 영수증(비공개)**: `V214_PRIVATE_REAL_ETF_250_EXACT_GITHUB_NATIVE_V6_SOURCE_ATTESTED_RECEIPT.json`, SHA-256 `9ca7327ade4a1faa2475d977ff0d0deeb3da3c000da7fb34368ef7fc1f122f4a`, native V6 원자 digest `9fdbf16ed64ce39ac5385482135ae3b7cc6115ef16761aab57f52b0a024ca09a`. 전체 비공개 exchange 파일 SHA-256 `2010c40f03c673177ec600dd5a0b516990aec43ef5f6cb004eac90be874ad055`.

## 2. 조건·예외 손실 재발방지: V213 출처 관문 재사용

V210에서 이미 찾아낸 조건·예외 **17개**를 무조건 V6 인덱스에 넣지 않았다. V214 최초 실행에는 **17개 출처 역할 검토 대기 / V6 인덱스 0**으로 유지해 불명확한 qualifier가 거짓 speaker-spoken source로 승격되지 않음을 먼저 확인했다.

이어서 ChatGPT가 현재 **원본 자막 문구를 직접 재검토**한 별도 E2 `SOURCE_EXPLICIT` 출처 패킷 17개를 비공개로 저장·해시 고정했다. 조건 15개/예외 2개는 그 자막의 원문 정확한 문구/SHA가 존재할 때만 새 native V6의 조건·예외 `cue_indices`에 들어갔다. `speaker_audio_verified=false`, `independent_gold_certified=false`를 유지한다. 현재 문장 전사를 검증한 것이지 실제 음성 화자·법령상 사실을 인증한 것이 아니다.

패킷: `V214_PRIVATE_REAL_ETF_17_CHAT_SOURCE_QUALIFIER_PROVENANCE.json`, SHA-256 `948a033a2b086ae8b65095ce268308940b72458af548bedc096bc3a562fe7545`. 코드의 `qualifier_source_review=None` 기본값은 여전히 V6 인덱스를 빈 상태로 보류하고, 별도 원문 SOURCE_EXPLICIT 판정이 존재할 때만 반영한다. `SOURCE_CONTEXT`와 `REVIEWER_ADDED`는 speaker-spoken condition으로 승격하지 않는다.

## 3. 화자·입장 분리, 동치·중복 재검토

원본 SRT에는 실제 음성 화자 식별·원화면 확인이 없어 **55개 native V6 후보에 `speaker=UNKNOWN`, `stance=UNRESOLVED`**를 유지한다. 별도 비공개 파일에서는 기존 V210 후보의 종류(FACT 30/OPINION 9/RECOMMENDATION 11/HYPOTHETICAL 5/MATH 2)를 근거로 텍스트 의미 유형을 분리했으나, **기존 V210 분류를 전용 코드로 정리한 것**이지 새 외부 독립 정답이 아니다.

57개 후보의 1,596개 가능한 쌍 중 **원문 구간이 실제로 겹치는 8쌍을 이번 채팅에서 원문 대조**했다. 사람/로봇 비유 vs 패시브 추종 설명, 순자산 심리 안정감 vs 수익률 비보장 반례, LP 예외 vs 높은 거래량 권고, 보수의 정의 vs 행동 권고 등의 **서로 다른 의미**를 잠정 구분했다. 자동 중복 병합 **0**, 외부 검토자 독립 동치 판정 **0**. 겹치지 않는 1,588쌍의 의미 동치 전수 검사는 완료되지 않았다. 역사적 V181의 69 원자와 V188의 71 원자 개별 비공개 원장을 현재 세션에서 복구하지 못했으므로 57·69·71의 일대다 동치/누락은 아직 종결할 수 없다.

비공개 리뷰 `V214_PRIVATE_REAL_ETF_TEXTUAL_ROLES_AND_EIGHT_OVERLAP_REVIEW.json`, SHA-256 `25c5287a566069eab2018975da390eae08320a2d183b04e2d97781dc3c62263c`.

## 4. V182 잔여 17 OPEN과 직접 V6 대조

V182에서 개별 번호가 알려진 원본 17개 OPEN의 인용·SHA를 모두 다시 원본 SRT와 검증했다. 최신 native V6 초안에서는 4개 cue가 `CANDIDATES`이고 13개 cue가 `UNRESOLVED`다. **17개 모두 승인/종결 처리를 하지 않았다**. 이는 원음 9건, 원화면 5건, 역사 통계 1건, 절대적 일반화 2건에 대한 증거가 별도로 필요하기 때문이다. `high_risk_false_clearances=0`은 **자동 오승인 0**만 의미하며, 기준 정답셋 없이 실제 고위험 누락 0을 증명한 것이 아니다.

비공개 `V214_PRIVATE_REAL_ETF_V182_17_OPEN_NATIVE_CROSSWALK.json`, SHA-256 `17cf80f1e51ca47b85bd0aef5529ae8f0cca6014ac45b01eb0cbda0c847167e4`.

## 5. RunFail 위험을 실제 실물 입력에서 발견·수정

V214의 초기 코드가 `json_digest(private_v210_inventory)`를 호출했다. 실제 V210에는 계산 예시의 소수(`0.4682`)가 있으므로 **동결 `ire/v6/codec.py`의 정수 전용 canonical JSON 검사에서 `NON_CANONICAL_JSON_TYPE`가 발생하는 실물 입력 결함**을 재현했다. 합성시험에 소수가 없어서 초기에 검출되지 않았다.

**수정:** 동결 codec 규칙을 완화하거나 실물 계산값을 수정하지 않고, V210 원본 **JSON 바이트**와 외부 고정 `expected_v210_source_sha256`를 필수 입력으로 사용한다. 파싱된 JSON과 원본 JSON 바이트 내용·해시가 불일치하면 `InvalidInput`으로 fail-closed. 다음 부정 시험을 추가했다.

- 실제처럼 계산 소수 필드가 있어도 V214 V6 실행 성공
- 입력 파일 바이트 또는 외부 SHA가 변경되면 오류를 명시적으로 반환
- 비공개 원본 입력/해시 누락 시 Python `TypeError` 대신 거부
- 원문 밖 숫자·위조 quote·원문 cue 인덱스 위조·검토자 주의사항의 원문 조건 승격 차단

최신 [GitHub Actions 44760963605](https://github.com/yhappcom/pensionport/actions/runs/44760963605) **281/281 PASS** (현행 E2 210, 기존 V176/E2 53, E1 18), 외부 네트워크/LLM API 없는 실제 frozen native Python을 private 원본과 함께 직접 로컬 실행해 추가 실측했다. 이 개선은 **연구 엔진의 입력 처리·런타임 예외를 줄이는 조치**이지 ChatGPT 플랫폼 UI의 모든 RunFail을 제어한다는 보증은 아니다.

## 6. 네 가지 사용자 완료조건에 대한 정직한 단계 판정

| E2 과제 | 현 시점 |
|---|---|
| 실물 원본 250개 native V6 구조 변환 | **250 cue/13 창·55개 미승인 원자 native 검사 PASS. 나머지 UNRESOLVED 195 cue, 역사 V176 원장 미복구로 최종 완료 아님** |
| 화자·입장 의미 확정 | 57개 텍스트 분류 정리했으나 원음 없이 speaker/stance 확정 **미완료** |
| 원자 누락·중복·동치 판정 | 겹치는 8쌍 직접 검토, 원문 유도 수치 2건 차단. 역사 69/71 원자 및 비겹침 쌍 **미완료** |
| 독립 정답 기반 precision·recall·고위험 누락 | 외부 독립 원자 골드 부재, 분모 고정 불가. **미측정** |

**E2 최종 판정 HOLD**, E1 구조 PASS 유지, E3~E5 현행 순차 경로 미진행. GitHub에 실물 SRT, 개인 비공개 검토·동결 owner SQLite, 사실성 확정 데이터를 올리지 않았으며 `main`을 수정하지 않았다.

### CI 시점 보완 기록

V214 단계 상태 검증에서 처음 [run 44760775601](https://github.com/yhappcom/pensionport/actions/runs/44760775601)은 V213 이전 시험의 E2 테스트 건수 `185` 고정값 때문에 실패했다. 실제 실물 V6 구조나 native qualifier 투영 오류가 아니라 이전 시험의 누적 테스트 건수 가정이다. 이후 V213 역사 검문은 최소 보장 건수 `>=185`로, 최신 V214 단계 검문은 현재 총수 `281`로 구분하여 수정했다. 최종 [run 44760963605](https://github.com/yhappcom/pensionport/actions/runs/44760963605) **281/281 PASS**, Python Traceback·KeyError·TypeError 없음. 과거 실패 이력을 지우지 않는다.
