# V219 — E2 250-cue / 66-atom / 32-relation / V182-17OPEN 통합 원본 검문 (2026-11-21)

**판정: 실물 원본·동결 V6·통합 입력 무결성 및 미승인 위험 보존 PASS / 독립 의미 정확도 E2 HOLD.** 모든 항목은 현재 한 번의 통합 실행에서 검사했다. 연구 승인·지식 발행은 0건이다.

## 1. 실제 원본 및 전수검문

| 항목 | 실측 |
|---|---:|
| 사용자 보관 SRT `LVE7XN_esTc` 원본 SHA-256 | `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b` |
| 자막 총수 · 원문 바이트 SHA 일치 | **250/250** |
| V219 미승인 native 원자 수 · 동결 V6 구조감사 | **66, PASS** |
| 직접 source-ref cue | 63 |
| 기존 원자 문맥 cue (직접 source-ref 없음) | 157 |
| 원자·문맥 모두 미연결, 화면 의존 격리 | 11 |
| 잠정 비주장·담화 cue (독립 정답 아님) | 19 |
| 음성·화면 원자료 검증 필요로 표기된 cue | **24** |
| 금융 의미 유의사항 태그가 있는 미승인 원자 | **39/66** |
| 과거 V182 source-first 위험 OPEN 항목 재연결 | **17/17**, 여전히 OPEN |
| V218 출처 기반 관계 보존 | 17 inter-atom + 10 intra-atom + 5 media-hold = **32/32** |
| 별도 독립 blind gold precision·recall | **미측정** |

- 187개 primary 없는 자막 = 문맥 157 + 화면 미확인 11 + 비주장·담화 잠정 19. **187건을 원자 누락 187건이라고 간주하지 않는다.** 반대로 이 소스 내 분류가 독립 정답 기반 **누락 0건**을 증명하지도 않는다.
- 이 자료의 `DISCOURSE_OR_NONCLAIM_PROVISIONAL`은 **ChatGPT 내부 원문 검토에 따른 임시 레이블**이다. 이는 완결된 독립 부정 정답(false positive absence label)이 아니다. 위험 자막 24개의 음성·화면 플래그는 보존.
- 원본 cue 세기와 해시·원자 구조·수치 원천 출처 대조는 재현 가능한 소프트웨어 실측이다. 누락·중복의 의미 정답셋 없음.

## 2. 단일 native 개정: 출처·조건·숫자 혼입 개선

기존 V217 66원자 교환을 보존하고, **V219 신규 비공개 미승인 교환**을 만들었다. 9개 원자에서 **명제 8건 + 숫자 참조 1건**을 정밀 수정했다. `source_refs`, owner, 원자 식별자, 문맥·조건·예외 cue, 자막 처분, 화자 `UNKNOWN`, 입장 `UNRESOLVED`, 승인상태는 변경하지 않았다.

| 원자 | 실제 보완 |
|---|---|
| `C00005` | ETF 패시브/액티브 유형 설명과 **전체 펀드의 유형**을 혼동하지 않도록 범위 미확정 |
| `C00029` | '주식에는 없고 ETF에만'이라는 배타적 표현을 화자 발언으로 고정, 금융진실성 미승인 |
| `C00030` | **보유 주식 가치의 단순 합계 vs 부채·현금이 반영된 순자산** 차이를 위험으로 보존 |
| `C00031` | 원문에는 'ETF 주식 수'가 나오는데 기존 명제가 **유통좌수**를 단정하던 근거 확대를 제거 |
| `C00032` | NAV-시장가격 **원화 차이와 괴리율(%)**의 개념 혼용을 명시적으로 보류 |
| `C00035` | 성과 차이 **추적차이 vs 추적오차**의 정의·통계 구분을 보류 |
| `C00046` | 전사의 '40km·45km' 비유를 오디오 없이 'kg'라고 보정하거나 사실로 승인하지 않음 |
| `C00070` | 주식만 모은 상품이라는 설명이 기타 기초자산 ETF를 배제하는 위험 표시 |
| `C00067` | 가상 ETF 거래수량 `123,477`이 이전 순자산의 `415`를 숫자 근거로 잘못 상속한 연결 제거 |

새 native 원본 SHA-256 `4d62a2de33d5ced39d2306361d5a8df1e9daf2b534475245f6784437bc2c0e83`. 동결 V6 실제 250 자막 감사 결과 **66개, primary 없는 187개, atom digest `d776f515aebfcc9adf20022cb1eeff71a16d50fa9aa323d2d42f926b9ade2e80`, 구조 PASS**.

## 3. 전체 미해결 문제를 단일 통합 게이트에 연결

새 코드 `v219_e2_integrated_source_claim_quality_guard.py`는 다음 9개 **비공개 바이트 입력**의 SHA를 고정한 후 서로 대조한다: 원본 SRT, V217 native, V219 native, 250-cue taxonomy, 66 금융위험 원장, V182 OPEN 17 crosswalk, V219 legacy relink, native 9개 개정기록, V218 관계 그래프. 250개 cue 모두 원문 및 해시·원자 primary/context 역참조 일치 검사.

- 66원자 각각의 출처 cue 및 numeric token 소속을 검문하여 **다른 원자의 숫자가 침투하면 차단**.
- native 개정 9필드를 제외한 owner/source/condition/exception/speaker/stance 변경 시 차단.
- 17 inter-atom link와 5 시청각 quarantine 관계의 기존 연계가 사라지는 경우 차단.
- 원문 cue의 비주장/화면 격리 분류 조작, 과거 V182 17개 OPEN 은폐, 누락 gold/정밀도·재현율·화자 검증의 **허위 PASS 라벨** 차단.
- 조건을 모두 통과해도 `require_gold_before_approval`은 별도 확정 gold와 원장 없이는 최종 승인 인계를 차단한다. 기존 동결 V123/E4/E5 실제 경로로 우회 발행하는 기능은 구현하지 않았다.
- 공개 CI에는 **합성 자막만** 넣으며 비공개 사용자 영상·원자 전문·SQLite를 GitHub에 올리지 않는다.

현재 V219 신규 합성 회귀시험은 **30개**. V218 361개와 합해 **391개 검증**하도록 .github/workflows/ire-v206-e2-source-census.yml에 등록했다. 이 수치는 최종 CI 완료 전에는 예정값이다.

## 4. 금융 근거와 과거 이력 한계

현재 금융 개념 검토는 삼성자산운용 [KODEX ETF NAV 가이드](https://www.samsungfund.com/etf/insight/guide/view03.do), [PLUS ETF 기초 가이드](https://www.plusetf.co.kr/insight/concept/basic), [금융위원회 ETF 투자자 위험 자료](https://www.fsc.go.kr/no010101/86973)를 **맥락 참고자료**로 조회했다. 괴리율·추적차이·추적오차·LP와 보수 위험을 조명했으나 **해당 각 금융 사실의 법령 시행일·공식 원문 바이트 증명·적용 범위가 승인되었다는 주장은 아니다.**

- V182 17개 위험 cue별 원문 SHA는 다시 확인했으나, **V176 이전 개인 owner SQLite 사건/원자 61/69/71의 실제 바이트/해시 연결 데이터는 Library 및 GitHub 검색에서 확보하지 못했다.** 따라서 과거 원자와 최신 66개의 의미 동치·누락을 정식 완결할 수 없다. V182 source-first 사본은 실제 owner SQLite를 대체할 수 없다.
- 원본 YouTube 공개 페이지는 확인했지만 원화면 프레임·원음을 검증 가능한 자료로 확보하지 못했으므로 `UNKNOWN` 화자와 24개 audio/screen risk cue는 보수적으로 HOLD. 자막 속 오인식 수치/단위를 임의 확정하지 않았다.
- 동일 ChatGPT가 보는 원문 재검토는 **독립 외부/블라인드 사전 확정 gold가 아니다.** 참 주장 전체의 원자 단위 정답셋이 없으므로 정밀도≥95%, 재현율≥98%, 고위험 누락=0 목표의 측정 자체를 할 수 없다. 이 한계를 기술적 테스트 성공으로 덮어서는 안 된다.

## 5. 비공개 소유자 개인 Library 신규 보존

1. `V219_PRIVATE_ETF250_NATIVE66_MEANING_HARDENED_UNAPPROVED.json` SHA `4d62a2de33d5ced39d2306361d5a8df1e9daf2b534475245f6784437bc2c0e83`
2. `V219_PRIVATE_ETF250_FULL_CUE_TAXONOMY_HOLD.json` SHA `d3dcf6ae03644e8aed97bb277855f6c7201595d060ccb5a7a8824459e4d59cda`
3. `V219_PRIVATE_ETF250_ALL66_FINANCIAL_RISK_DOCKET_HOLD.json` SHA `e3d8a15326a4beaf2940ede238e60d3bb5e08e40bf29b8169690daefcd5a7dac`
4. `V219_PRIVATE_ETF250_V182_17OPEN_CUE_SOURCE_RELINK_OWNER_HOLD.json` SHA `02497e6a3517542db4f79d827dc8d58c18f9331bc86ed7430cb3f87e776e38bb`
5. `V219_PRIVATE_ETF250_9_NATIVE_FIELD_EDITS_AUDIT.json` SHA `d3d3986115880b9d868a9ab6351528853f799251bcee4c5a5d854328c59a70ba`
6. `V219_PRIVATE_ETF250_INTEGRATED_FROZEN_E2_REPLAY_RECEIPT_HOLD.json` SHA `a0513966ceab19e279c5dbcef6b6e238dfbb1bdd0a49185391d1142099da0add`

위 실물 파일들은 비공개 Library에 append-only로 저장하고 이전 V215~V218 원본 기록을 덮어쓰지 않았다.

## 6. 최종 단계 제한

**E1 구조 PASS · E2 금융 의미와 독립 정확도 최종 HOLD · E3~E5 현행 실물 경로 NOT_RUN**.

실제로 완료된 것은 ETF 1편에 대한 **250-cue 원문/이력 출처 전수 census, 66원자 구조 및 9개 의미·수치 정정, 32개 원자관계 보존, 17개 과거 OPEN 출처 재연계, 30개 추가 실패 방지 테스트**다.

아직 달성하지 못한 것은 역사 V176 owner 원장과의 전수 동치·원음/원화면 확증·독립 확정 정답 기반 정확도 인증이다. 가짜 독립 정답·화자·화면 정보를 만들지 않았고, `main`과 동결 V6/V123/V126/V127/V128를 수정하지 않았으며 PR #75는 Draft / 미병합, 연구 지식 발행 0건이다.
