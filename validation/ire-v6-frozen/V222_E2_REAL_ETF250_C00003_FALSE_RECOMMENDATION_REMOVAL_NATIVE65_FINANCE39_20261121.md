# V222 — ETF 원본 250개 자막의 비주장 오분류 정정 및 원자·위험·자막 원장 동기화 (2026-11-21)

**최종 연구 판정: 소유자 실제 SRT 출처·동결 V6 구조검사 PASS / 독립 의미정확도 및 화자·금융사실 E2 HOLD.** 이전 V219~V221 비공개 실물을 덮어쓰지 않았다. 공개 GitHub에는 사용자 원본 SRT/개인 검토 텍스트를 올리지 않았다.

## 1. 실제 오분류 및 원문 근거

- 소유자 원본 `LVE7XN_esTc` SRT **250/250 cue** 바이트 SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b` 확인. 이전 V221 native 66개 SHA `6f8a5179efd5bd0c743717fc82771f636fd6876d406d6d6870994255e2995038`.
- **C00003**은 `RECOMMENDATION` 명제 "인덱스 ETF 비교를 위한 여섯 기준을 제안"으로 등록됐으나, 실제 13~16번 발언은 **여섯 가지 기준을 앞으로 배워보겠다는 강의 구성 안내**, 구체적 ETF 상품 매수/선택 권고 자체는 아님. V221 source-first 의미단위 `SRC221-005`도 `NARRATIVE_NONCLAIM`으로 검토했으며 원자 후보와 유형이 불일치했다.
- **V222 private 새 교환:** C00003만 제거하여 **65개 미승인 원자 유지**, 기존 65개 원자는 proposition·kind·speaker·stance·condition/exception·numeric token·source refs·owner **전혀 변경하지 않음**.
- cue 14의 `CANDIDATES(C00003)`를 **`NO_ATOM`(잠정 비주장)** 으로 명시적으로 전환. 원래 cue 13/15는 C00003의 `context`에만 속해 있었으므로 새 native에서는 context 연결 해제. 원문 전문/해시와 이전 원자/처분/검토자 이유를 별도 append-only "negative decision" 이벤트에 보존.
- **중요:** NO_ATOM은 gold-확정 "실제 음성에 주장 없음"이 아니다. 동결 V6의 위험 키워드에 걸리는 `suspicious_no_atom_cues=1`을 그대로 보존하므로 차후 독립 누락 심사를 건너뛸 수 없다. 원자 삭제에 다른 원자간 32개 source-first 관계의 연결점 C00003이 없음도 대조했다.

## 2. 변경 전후 수치 및 범위

| 항목 | V221 | V222 |
|---|---:|---:|
| 원본 SRT cue | 250 | 250, 원본 SHA 동일 |
| 미승인 native 주장 원자 | 66 | **65** |
| 직접 primary 근거 cue | 65 | **64** |
| primary 미확정/미연결 `UNRESOLVED` cue | 185 | **185** |
| source-first 검토로 `NO_ATOM`으로 판정한 cue | 0 | **1**, 독립 gold 아님 |
| 원자 문맥만 연결된 cue | 155 | **153** |
| 비주장·담화 잠정 분류 cue | 19 | **22** (13·14·15번 3개) |
| 시청각 source-only 미연결 격리 | 11 | 11 유지 |
| 원음·원화면 확인 위험 cue | 24 | 24 유지 |
| 원자별 금융 의미 위험표식 | 39 | **39/65** 유지 |
| 과거 관계 원장 | 17 cross + 10 within + 5 media = 32 | **32/32 불변** |
| 동일 ChatGPT 원문 의미 단위 | 62 | 62, source-first gold 인증 아님 |
| 추가 발화 유형 불일치 검토 대상 | C00003 1건 명시적 | C00003 잠정 해소, **11개 coarse-unit 유형 차이 OPEN** |
| 독립 gold 정밀도·재현율·고위험 누락 0 | 미측정 | 미측정 |

새 frozen V6 실물 감사를 **원본 SRT와 V222 미승인 65 native**에 직접 재실행해 `proposed_atomic_claims=65`, `cues_with_candidates=64`, `unresolved_cues=185`, `suspicious_no_atom_cues=1`, atom digest `0aefefa2a75b12449d0cf52898d66f70631a7036f13a3e5569ccad1d1ae5831a` 구조 PASS.

11개 추가 유형 불일치(`C00006, C00009, C00015, C00019, C00034, C00039, C00044, C00045, C00046, C00056, C00069`)는 거친 source 단위가 여러 발화 유형을 포함할 수 있어 **전부 실제 오분류라고 단정할 수 없음**. 실제 정밀 발화 수준 판정 전 자동 수정·승인 금지.

## 3. 구조적 개선 — 원자 삭제와 연결된 모든 원장 재생

기존 V219 금융 위험 원장 66행과 V221 cue census 250행은 과거 native SHA 및 대표 근거 cue를 가리켰으므로 V222 native만 저장하면 **판정 원장 버전 불일치**가 발생한다. 이를 해결했다.

- 새 금융 검토원장 **65행**: 원자 65개 ID/원자 kind/primary cue+원문 text SHA/context/숫자 토큰을 실제 V222와 1:1 일치시키면서 이전 위험 tag **39개**와 speaker·stance/금융/ gold 미확정 상태를 그대로 유지.
- 새 250 cue census **250/250**: 원본 전문/SHA와 현재 primary/context claim ID를 역산하여 새 분류 **64 primary + 153 context + 22 잠정 담화/비주장 + 11 화면격리** 재고정. 위험 음성/화면 24개 불변.
- 독립 blind gold 입력 없는 상태에서 `NO_ATOM` 및 `DISCOURSE_OR_NONCLAIM_PROVISIONAL`을 확정 정답 라벨로 쓰지 않는다.
- 기존 V221 62↔66 매핑과 관계 연결 32건은 append-only 보존하고, V222 전용 **62↔65 신규 매핑**을 작성했다.

## 4. 신규 코드와 실패방지 검사

검증 브랜치에 다음 코드가 추가됐다.

- `v222_e2_source_nonclaim_filter_guard.py`: 실제 SRT 원본, V221 source-only 62단위, V221 native 66, V222 native 65, 비주장 판정 이벤트, 선행 32개 관계 그래프의 **원본 바이트+SHA** 검문. 실제 `audit_host_atomic_exchange`를 이전·새 native에 각각 실행하고 **리뷰한 비주장 원자만 제거됐는지, 그 외 원자·숫자·문맥·조건·예외·화자가 바뀌지 않았는지, 참조 관계가 유실되지 않았는지** 검증.
- `audit_postfilter_native_risk_and_cue_census`: V222 native 65개, 새 금융위험 65행, 원문 자막분류 250행의 동일 SHA 및 원본 인용/수치/위험표식 관계 검사. 이전 버전의 risk row·cue disposition이 끼어들면 차단.
- `test_v222_e2_source_nonclaim_filter_guard.py` **27개**, `test_v222_postfilter_source_sidecars.py` **16개** = **43개 합성 실패방지 회귀검사**, 로컬 43/43 PASS. 실제 사용자 원문은 비공개 로컬 실물 재생; 공개 CI에서는 합성 사례만 이용.
- `require_approved_e2_disposition`은 원음/독립 gold/금융 근거가 없는 새 native를 최종 E3/E4/E5로 승격시키지 않음. 기존 동결 V6/V123/V126/V127/V128은 바꾸지 않았음.

공개 CI 총 검사는 V221 **440개**에 V222 신규 **43개**를 더한 **483개**(현행 E2 412 + 역사 E2 53 + E1 18). GitHub Actions [run 44846138358](https://github.com/yhappcom/pensionport/actions/runs/44846138358) **483/483 PASS**, 실제 job logs에서 412/412 + 53/53 + 18/18의 OK를 확인했다. 이 공개 CI는 합성 입력만 검증하고 개인 원본 E2 의미 품질의 독립 정확도를 증명하지 않는다.

## 5. 비공개 owner Library append-only 결과

1. `V222_PRIVATE_ETF250_NATIVE65_C00003_NONCLAIM_SUPPRESSED_UNAPPROVED.json` SHA `5e31ce67dba14bce573de933b19a8b655f4e530324caaef7cea3dd35e9ba68ae`.
2. `V222_PRIVATE_ETF250_C00003_SOURCE_FIRST_NONCLAIM_REJECTION_EVENT.json` SHA `5f06711a7ff4c8faeb71842e1dec9f1042db1704d792b22d42c2dcc24f58399d`.
3. `V222_PRIVATE_ETF250_62_SOURCE_UNIT_NATIVE65_MEANING_CROSSWALK_UNAPPROVED.json` SHA `61f17c9272e8abffd17cf47064638a428f290afa1d543b6b7449ea8984a534db`.
4. `V222_PRIVATE_ETF250_FROZEN_V6_NONCLAIM_FILTER_REAL_RECEIPT_HOLD.json` SHA `684357a53aa61f35cb013622a25a02490e9a3b6e702adb8d2802e02907f8cc56`.
5. `V222_PRIVATE_ETF250_11_COARSE_KIND_DIFFERENCES_OPEN.json` SHA `74c560f844a9c8f80f423ecfa6238185761b968b40034f217ec842bc54222988`.
6. `V222_PRIVATE_ETF250_NATIVE65_FINANCIAL_RISK39_REPINNED_UNAPPROVED.json` SHA `384affff0e61c3a0a7cc72addac1a74ee88e1a00caf2d00316759f926e1b2a51`.
7. `V222_PRIVATE_ETF250_SOURCE_CUE250_CENSUS_REPINNED_HOLD.json` SHA `c58e54c55f19e48abc6df281b723e61908d4f0e46123bf35106d86b0e14a4cf5`.
8. `V222_PRIVATE_ETF250_POSTFILTER_SOURCE_RISK_CUE_RECEIPT_HOLD.json` SHA `0cd55452322e68b914a0879fd2d3bd09a4318e0921a00d4af6d4622da71c9ad6`.

**모든 원본 자막·실제 원자·관계 정정 상세문서는 개인 Library에만 존재**하고 공개 저장소에는 소프트웨어/집계 보고서만 보관한다.

## 6. E2 완료 조건

현재 **E1 PASS, E2 원본 출처/원자 구조/명시적 비주장 정정 PASS·독립 의미 품질 HOLD, E3–E5 NOT_RUN**.

남은 문제는 (a) 독립 고정 gold 및 완전동치·조건·예외·고위험 누락 판정, (b) 화자·입장 65개 미확정 및 화면/음성 위험 cue 24개, (c) 금융 의미 위험 39개와 coarse type 차이 11개 독립 검문, (d) 역사 V176 owner SQLite 확보 또는 레거시 격리 및 E3~E5 원자적 승인/저장 실제 경로 실증이다. 자문에 금융 사실 65개를 자동 승인하거나 발표하지 않았다. `main`, 동결 엔진, PR #75 Draft/migration 정책 불변.
