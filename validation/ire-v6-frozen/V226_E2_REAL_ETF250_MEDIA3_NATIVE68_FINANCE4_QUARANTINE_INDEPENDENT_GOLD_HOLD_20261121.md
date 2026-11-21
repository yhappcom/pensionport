# V226 — 실제 ETF 원본의 화면발화 누락 3건을 미승인 V6에 복구하고 금융개념 충돌 4건을 E3 격리 (2026-11-21)

## 결론

**원본 ETF 자막 250개를 다시 재생해 V220부터 보류 파일에만 있던 3개 화면 설명 발언을 정식 미승인 원자 후보로 연결했다.** 금융 사실·화자·시청각 증거를 승인하지 않았다. 과거 V224 65개 원자 및 V225 32개 관계와 복구된 22개 후보 endpoint는 불변이다.

| 실물 검사 | V225 | V226 |
|---|---:|---:|
| 원본 SRT 검토 범위 | 250/250 | 250/250 |
| 미승인 native V6 원자 | 65 | **68** |
| 직접 source_refs를 가진 자막 | 64 | **72** |
| native primary가 없는 자막 | 185 | **177** |
| 미승인 원음·화면 근거가 필요한 cue | 11 | **11 그대로 HOLD** |
| 후속 금융 지식으로 발행되면 안 되는 과도·부정확한 발언 | V225 4건 검토 | **4건 E3 격리 명시** |
| 추적차·추적오차 용어 원음 확인 필요 | V225 2건 검토 | **2건 E3 HOLD 명시** |
| 관계 원본 | 32개, 이전 누락 후보 22회 복구 | **32개 모두 유지** |
| 외부 블라인드 gold·정밀도/재현율 | 없음 | **없음** |

동결 V6 `audit_host_atomic_exchange`를 실제 원본 SHA `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`으로 변경 전·후 각각 재실행한 결과, 65→68 원자, 64→72 direct cues, 185→177 UNRESOLVED cues, suspicious `NO_ATOM=1`을 정확하게 재현했다.

## 1. 실제 원자 누락의 원인과 수정

V220에 이미 출처 기반 발화 후보 3개가 있었지만 `V220MEDIA-001/002/003`을 화면 근거 부족으로 판단하면서 **정식 미승인 V6 원자조차 생성하지 않아** 연구 후속 작업에서는 별도 파일만 읽어야 했다. 영상의 그림 속 내용이 실제로 참인지와 **화자가 그 내용을 발언했는지**가 하나의 보류 여부로 결합된 설계 결함이다.

그래서 다음과 같이 **원문 발언 후보만 추출**했다.

- `C00074`: 163~167번 화면 설명에서 진행자가 지수/NAV 추적 차트의 가까움·벌어짐을 말한 부분. 165·167번을 원문 직접 인용으로 지정. **실제 그래프 모양과 추적차 정의는 미확정**.
- `C00075`: 230~231번 가상 ETF의 일별 괴리 관련 발화. 해당 2개 자막만 인용; **화면 수치·일자·괴리율 부호 미확정**.
- `C00076`: 232~235번 수익률/기초지수 장기 차트 관련 발화. **차트·통계적 의미·화자 신원 미확정**.

3개 원자 모두 `HYPOTHETICAL`, `speaker=UNKNOWN`, `stance=UNRESOLVED`, 미승인 원문 인용·문맥/가상범위만 가진다. 금액·수익률·시점을 새로 생성하지 않았고, **기존 원자 65개의 명제·원문·조건·예외·숫자·화자 필드는 완전히 동일**하다.

기존 V220의 `3`개 발화 후보와 실제 68원자를 1:1 매핑하고 원문 음성·화면 확인 11개 cue와 원래 미확정 관계 5건의 **HOLD를 유지**했다. 8개 cue가 새 native의 `CANDIDATES`가 되었으나 영상 확인이 필요한 11개 cue 중 3개는 여전히 직접 원자가 없는 문맥 cue다. 새 250 cue 분류는 64개 기존 anchored, 154 context, 21 narrative/provisional, 8 media-source-anchored-but-visual-HOLD, 3 media-context-visual-HOLD로 정확히 250이다.

## 2. 금융 주장 승인 오염을 차단

2026-11-21 기준 공개 한국거래소 자료와 대조한 **영상 속 화자의 발언**은 원문 그대로 보존했다. 그러나 그 발언을 사실로 인정하거나 참인 수정 지식을 영상에서 직접 추출한 것처럼 처리해서는 안 된다.

| V6 원자 | 영상에서 말한 내용 | E3에서 보존한 상태 |
|---|---|---|
| `C00029` | 괴리율이 ETF에만 있다는 배타적 일반화 | **QUARANTINE** — ETN도 지표가치 대비 괴리율 지표 있음 |
| `C00030` | 순자산은 주식가치 단순 합계라는 표현 | **QUARANTINE** — 자산·부채·발행좌수 구분 필요 |
| `C00032` | 가격과 NAV 차이를 그 자체로 괴리율이라고 표현 | **QUARANTINE** — 원화 차이 vs NAV 대비 비율 구별 |
| `C00070` | ETF는 주식을 묶은 것이라는 광범위 정의 | **QUARANTINE** — 채권형·합성형 등 존재 |
| `C00035,C00072` | 추적차·추적오차 용어 사용 | **HOLD** — 원음/통계적 추적오차와 추적차이 구분 필요 |

**정정 해설을 새 영상 발언 원자로 만들지 않았다**. 공식 웹페이지의 개념 확인은 원자별 공식 원문 바이트/법령 시점 인증을 의미하지 않으며, 21개 이전 공식개념 비교 원장은 append-only로 유지한다.

공식 자료 URL (맥락 참고, 본 문서 자체가 공식 원문 바이트 인증을 뜻하지 않음):
- KRX ETF NAV/시장가격: https://www.krx.co.kr/contents/OPN/01/01030204/OPN01030204T7.jsp
- KRX ETN 지표가치와 괴리율: https://www.krx.co.kr/contents/OPN/01/01030302/OPN01030302.jsp
- KRX 합성/채권 ETF: https://m.krx.co.kr/contents/06/0609/060901/JHPETP060901M01.jsp

## 3. 공통 엔진과 E3 검토 경로 수정

신규 공개 소프트웨어 `v226_e2_speech_only_media_bridge_and_finance_quarantine.py`:

1. **13개 비공개 입력 파일의 바이트 SHA와 원문 SRT**를 재검문. 원본이 없거나 인용 변조, native schema drift면 `InvalidInput`.
2. 기존 원자 65개 전체의 정확한 frame 불변성 강제. 새 원자만 모든 원문·원어절·대표근거·조건·윈도·기존 화면 보류와 1:1 대응하도록 교환.
3. `V220` 기존 3개 발화 후보를 새 V6 원자와 연결. **원문으로 확인 가능한 발화 후보와 실제 화면 증거가 없는 금융 사실 주장을 분리**.
4. `V225`에서 공식개념상 부정확한 금융 주장 4개와 추적 용어 미확정 2개를 E3 전용 미발행 격리로 반영. 실제 금융 서술을 수정했다며 잘못된 발언·수치를 지우는 우회 차단.
5. 68개 E3 개별 심사 task 및 원래 복구된 V225 32개 source relation/22후보 완전성 유지. 후속 E3/E4/E5로 **금융 승인/미검증 발언 승격 차단**.
6. *source-only candidate coverage* `65/68→68/68`은 **이미 식별된 후보 68개 중 정식 미승인 V6 등록 비율**일 뿐, 원본 투자지식의 정답 재현율이나 고위험 FN=0 증명이 아님.

공개 합성 원본 SRT로 **41개** 자료 누락·SHA·화자/상태 위조·금융 오류 승인 우회·E3 관계 손실·독립 정답 위장 회귀시험을 실행했다. 실제 금융 자막은 GitHub에 넣지 않고 개인 Library의 실물에 대해 별도 감사했다. 이전 **592개 + 41개 = 633개**의 CI에 통합했다.

## 4. Owner-private append-only 실물 자료

- `V226_PRIVATE_ETF250_NATIVE68_MEDIA3_SPOKEN_DRAFT_VISUAL_HOLD.json`, SHA `c8bec3354702cad0e85d4b111d2627ae2978806f3a4111c94a689d3b9e25baeb`.
- `V226_PRIVATE_ETF250_MEDIA3_SPEECH_TO_NATIVE_APPEND_ONLY_EVIDENCE_HOLD.json`, SHA `9c042c4380e84b66d5b3b7970368397dd21ddc58027f598b18ed37d20e849a80`.
- `V226_PRIVATE_ETF250_CUE250_MEDIA_SOURCE_BRIDGE_VISUAL_HOLD.json`, SHA `8904fb0b812a2a8ae426fdbf94d18be1985aa3c440cb7da8e7d409d6d3611a9d`.
- `V226_PRIVATE_ETF250_FINANCIAL_4_CONFLICTS_2_TERMS_NONRELEASABLE.json`, SHA `1d7e499e628c927404120f6198707dc7c01aa0b357d112b1f16563053176dac6`.
- `V226_PRIVATE_ETF250_E3_68_NATIVE_32_GRAPH_4_FINANCE_QUARANTINE_HOLD.json`, SHA `13b10b5b8a7c59cbfe1735fa6d6a38f21b4dd9fd1a0bf801f6aa43f8ccbc87d5`.
- `V226_PRIVATE_ETF250_MEDIA3_INTERNAL_CANDIDATE_GAP_CLOSURE_NOT_GOLD.json`, SHA `e5b69267370fa814d7d62d5e4c95e94b59b8e4c0cf42cdd9a2bbaa9deadbbe05`.
- `V226_PRIVATE_ETF250_ACTUAL_13_INPUT_E2_E3_REPLAY_RECEIPT_HOLD.json`, SHA `b4bca036e88ce93f672be43d690a7a818ccf0a6a80c62e472dfc2713a6de37e1`.

모든 개인 원문·원자 전문은 GitHub에 공개하지 않고 사용자 Library에 append-only 저장. 이전 V225, V224, V223 원장 불변.

## 5. 남은 정밀 검문

- 현재 **177개 UNRESOLVED cue**는 154개의 문맥-only, 21개의 담화 잠정, 3개의 화면 맥락 등 중복·범위 상의 재검토가 필요하다. 누락/비주장 판정은 독립 정답이 아님.
- 독립 blind gold 없음. 실측 P≥95%·R≥98%·고위험 FN=0 인증 **여전히 미완료**. 다른 영상에 비공개 원본 없이 전수 의미 완결성 보장하지 않음.
- 11개 화면 관련 cue 및 원음 화자 정체성 미확정. 3개 원자 추가는 *내용/영상 진실성 확인*이 아니라 *발화 추출 후보화*.
- 공식 원문 법령 버전·시행일/범위 검증 미완료, 금융 승인 0건. 과거 V176 SQLite 없으므로 레거시 지식 통합 차단.

**단계 결론: E1 PASS / E2 실제 원문 발화누락 3건 후보화·금융 오류 격리 및 V6 구조 PASS, 독립 gold HOLD / E3 ChatGPT 미승인 68원자 검토 패킷 READY(정식 승인 HOLD) / E4–E5 NOT_RUN.** Draft PR 유지, `main`과 frozen V6/V123/V126/V127/V128 수정 없음.
