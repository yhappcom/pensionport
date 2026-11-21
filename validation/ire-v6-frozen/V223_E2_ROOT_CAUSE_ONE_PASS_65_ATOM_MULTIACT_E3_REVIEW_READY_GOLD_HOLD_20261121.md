# V223 — E2 반복 HOLD의 근본 원인 교정: 원자별 복합 의미 판정과 ChatGPT 검토 입구 연결 (2026-11-21)

**검증 판정: 원본 250-cue / 65-atom 출처·원자별 발화기능·동결 V6 재생 PASS. 독립 gold·원음/화면·금융 진실성은 계속 HOLD.** 공개 GitHub에는 소유자 원본 SRT 및 비공개 전체 원자/의미 판정 텍스트를 업로드하지 않는다.

## A. 왜 V206~V222 반복 개선에도 E2가 통과하지 못했는가? (실물 원인 분석)

1. **검증 목표 불일치 (P0):** 많은 V6 구조 및 합성 테스트는 해시·자막 전체 범위·주장 인용 존재·조건 인덱스 무결성을 검증했지만, 한국어 원문이 특정 주장의 **의미·화자·사실성**을 실제로 뒷받침하는지 독립 검증하지 못했다. 483/483 CI PASS를 **투자 지식 정답률 PASS로 볼 수 없음**.
2. **단일 `kind` 다의성 (P0):** V6 `kind={FACT, OPINION, RECOMMENDATION, HYPOTHETICAL,...}` 하나로 **명제 유형·발화 의도·가상 예시·시점 조건**을 모두 표현하려 함. 원문 전용 62개 의미구간은 평균 4.2개 cue이며 **11개 source unit이 2~3개 native 원자를 포괄**. `FACT` 명제가 `RECOMMENDATION` 문맥에 들어 있다고 해서 자동 오분류가 아닌데, 앞선 검증은 이 차이를 11개 OPEN으로 남겼다.
3. **원자별 ChatGPT 의미 확정의 영수증 부재 (P0):** 이전 V221 원문 단위 62개와 후보 원자 65개 관계는 존재했으나, **65/65에 대한 개별 발화 기능·가상성·시점·텍스트 입장·금융 위험의 일관된 원장 및 승인 제한**이 하나의 실행 경로에 연결되지 않았다.
4. **진입/승인 경로 교착 (P0):** E2 최종 의미 인증이 완료돼야만 E3 검토로 진행한다는 운영 흐름은, 실제로는 **ChatGPT E3가 E2 미확정 발언을 검토해 해결해야 한다는 목표**와 충돌했다. E2 HOLD를 E3 **검토 입구 차단**으로 사용한 것이 구조적 결함이다. **E3 검토 시작 가능**과 E3 최종 승인/E4/E5 발행은 엄격히 분리해야 한다.
5. **이력을 신규 정답과 혼동 (P1):** 역사 V176 owner SQLite 부재는 과거 지식 이관/E5의 중요 제약이지만, 신규 ETF 영상의 독립 정답셋 구축/측정 자체를 불가능하게 하는 논리적 선행조건은 아니다.
6. **실제 증거 부족 (P0):** 검증 가능한 원음·원화면 부재, source risk cue 24건, 비공개 과거 역사 DB 미확보, 65 native 중 speaker=UNKNOWN/stance=UNRESOLVED 65건, 금융 위험 다수, 사전 고정 독립 gold/one-to-one 고위험 FN 판정 부재. 이들은 **소프트웨어를 추가한다고 저절로 해결되지 않는 실질적 증거 문제**다.

## B. 이번 턴 ChatGPT가 직접 재검토한 원본 의미 판정

원본 `LVE7XN_esTc`, **250 cues**, 원문 SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`; V222 미승인 native 65개 (SHA `5e31ce67dba14bce573de933b19a8b655f4e530324caaef7cea3dd35e9ba68ae`). 65개 proposition·source cue·문맥을 확인하여 **65/65에 대하여 개별 source speech act와 epistemic scope를 재판정**. 같은 ChatGPT/기존 프로젝트 맥락을 알고 있는 상태의 내부 의미 검토이며 외부 gold 아님.

### 종전 11개 coarse-source-vs-native kind 차이의 전체 판정

| 원자 | 원래 kind | 원문 미시 발화 검토 및 조치 |
|---|---|---|
| `C00006` | OPINION | 20~21: 사람/로봇 유비는 거친 FACT_AS_SPOKEN 단위의 **ILLUSTRATION**. 신규 별도 발화기능으로 기록, 단순 의견 종류 한계 표시 |
| `C00009` | OPINION | 31~32: 패시브 ETF 초과성과에 대한 평가가 추천 구간과 혼재. **기존 OPINION 유지** |
| `C00015` | OPINION | 60~63: 초보자의 심리적 안도감 설명과 순자산 크기 선호 조언 혼재. **OPINION 유지** |
| `C00019` | FACT | 74~76: 거래량이 체결 가능성에 미치는 기초 원인 설명, 문맥 전체는 추천. **FACT 유지**, 체결 보장 금지 |
| `C00034` | HYPOTHETICAL | 149~151: 정상가·시장가의 가상 비유와 낮은 괴리율 권고 혼재. **HYPOTHETICAL 유지** |
| `C00039` | FACT | 174~175 원인 설명, 176~179 장기 지표 비교 조언. **FACT 유지**, 단순 인과 위험 보존 |
| `C00044` | OPINION | 195~196: 사람들이 보수 변화에 맞춰 이동하지 않는다는 **실증 미확정 행동 일반화**. **FACT(화자 사실 주장)로 수정**. 새 `EMPIRICAL_BEHAVIOR_GENERALIZATION_UNVERIFIED` 금융 근거 위험표식 추가 |
| `C00045` | OPINION | 197~201: 0.001/0.002 차이의 중요도를 평가하는 주관적 발화이자 조언 문맥. **OPINION 유지**, 원문 수치 단위 검증 보류 |
| `C00046` | OPINION | 202~204: 40km/45km(ASR 오류 의심) 몸무게 가상 유비. **HYPOTHETICAL로 수정**, km→kg 임의 교정 및 사실 승인 금지 |
| `C00056` | OPINION | 239~243: 여섯 ETF 지표에 절대 기준이 없다는 광범위 평가·일반화. 거친 FACT 구간과 구분, **OPINION 유지** |
| `C00069` | FACT | cue38 벤치마크 존재 설명, 39~42 평가 조언 별개. **FACT 유지** |

**기존 11건 모두 ChatGPT 내부의 원문-원자 수준에서 원인별 처리:** 9건은 거친 발화 구간의 **복합 speech act**, 2건은 **실제 native kind 필드 정정**. 이 조치는 금융 사실의 진실/정확도 인증이나 외부 독립 gold가 아님.

## C. 실제 수정 자료와 원본 재생

- native 65개 유지. **오직 `C00044`, `C00046`의 kind 두 필드 변경**, 다른 명제·원문 source_refs·화자·입장·숫자·조건·예외는 불변.
- 새 native SHA `32f541d8e0603b225db700122a3e0c95e54943455262b9959a7acfcc1864b091`; 동결 실제 V6 atom digest `290fea03d5734113604f65aac14e99197533ddcef9ae5fd8c0248170f815181e`. **실제 250/250 SRT, 65 native 원자 감사 PASS**.
- 기존 금융 위험 39개에 `C00044`의 검증 미확정 행동 일반화를 **추가 위험 1건**으로 지정해 **40/65**. 새 금융 risk ledger SHA `e0bec307bb63f08e56f323ebfe231ea716ecc8c9e056c0da274236d53f46efed`; 금액/수치·위험 39개 이전 태그는 보존.
- 원문 250-cue census를 새 native SHA에 재고정 (SHA `9cc83da8c3e26884d180ff1507d4b5d14559f8f2909e29c98bd2a8d80ad0ff7c`)하고 64 primary, 153 context-only, 11 media-unmapped, 22 provisional-discourse 수를 유지.
- 13개 가상/예시 원자를 실제 시장 시세나 사실로 자동 변환하지 않음. 기존 V218 32 source-relations = **17 cross-atom + 10 intra + 5 visual hold** 그대로 유지.
- 65/65 source text 기능/범위 review SHA `7e89aad515fde03341effc0adccdb7ab1ff19e41d6b3a6b55f001a670020bdce`; 2개 수정 이벤트 SHA `45a950b852c3296bac88254a566235ec53adfaba76a95d91afedc1c3e709d7e0`.

## D. 엔진의 공통 의미 심사 경로 구현 (재사용 가능)

검증 브랜치의 `v223_e2_semantic_convergence_engine.py`를 추가했다. 이 코드는 특정 원자 번호를 단순 패치하는 **V223 전용 하드코드 실행기**가 아니라, 새 영상에도 사용할 수 있도록 source/old-native/new-native/source-unit/mismatch/review/patch/finance/census/discourse-graph의 **12개 바이트 입력을 한 번에 받아** 다음을 수행한다.

1. 각 원본 바이트의 SHA, SRT cue, 원문 인용 전문, cue 숫자, 동결 `audit_host_atomic_exchange` 전체 검사를 재실행.
2. **원자별 서로 다른 의미 축** `textual_discourse_role`, `epistemic_scope`, `textual_stance_candidate`를 **기존 V6 kind·speaker/stance와 독립 필드**로 받아 65개 전체 매핑·검토 상태를 검사. 문맥 단위의 역할이 다른 것만으로 임의 원자 형식을 변경하지 않음.
3. kind 정정이 있을 때 **실제 source cue 증빙·이전/이후 native 실물 diff·변경 이벤트**를 필수로 검사하고, 다른 원자의 명제·숫자·화자·조건·예외가 몰래 바뀌면 차단.
4. 금융 원장 65행·250 cue 원장을 수정 native와 **같은 SHA로 재고정**. 위험태그를 제거하거나 새 실증 미확정 FACT의 위험을 누락하면 차단.
5. 32개 관계 원장이 수정 native의 실제 claim ID에 연결되는지, 화면 미확인 5개 관계가 삭제·허위 승인되지 않았는지 검사.
6. **E2가 HOLD인 동안에도** `prepare_chatgpt_e3_semantic_review_packet`으로 **원본 65개 미승인 원자와 source quotes·조건·예외·금융위험 및 원자간/원자내 관계 27개 + 별도 미확인 화면 관계 5개를 ChatGPT 검토 입구로 전달**. 코드상 E3 *검토 준비*와 E3 최종 승인/E4/E5 발행은 분리되어 있고 **후자는 계속 차단**.
7. 실제 gold·원음/원화면·공식 금융근거가 없으면 E2 최종 독립 정확도를 합격으로 선언하지 않는다. 원본 없이는 E3 검토 패킷을 만들지 못하며, 해당 패킷은 **개인 Library에만** 보존한다.

이 경로의 성공 receipt SHA `e916965cb963399426f83aeb6ada8712e0c6f971c2e89671cc1a2b509dac0363`; 실제 E3 미승인 65원자 검토 패킷 SHA `143bdebc1099d476c3aa4b2de9ba111c48346656198b3b3c6c6fa15ef4124386`.

새 합성 회귀시험 **38개**: source 바이트/인용 조작, 원자 뜻 변형, speaker 가짜 확인, kind change 미기록, 40 위험 중 일부 위험 소거, 가상 example을 시세로 승격, 32 관계 또는 5 화면 보류 탈락, gold/approval 위조, E3 packet 변조 등이 fail-closed 되는지 테스트. 실제 SRT는 공개 CI에 포함되지 않는다. V222까지 483개 + V223 38개 = **521개 최종 CI** (E2 450 + legacy E2 53 + E1 18). GitHub CI 실제 확인 이후에만 합격으로 기록한다.

## E. 이번에 해결한 것과 현재 남은 것의 정량 구분

| 의미/증거 단계 | V222 | V223 |
|---|---|---|
| ChatGPT 원자별 복합 의미축 검토 | 62개 거친 source 구간 | **65/65 원자에 별도 source 역할·scope·text stance review** |
| source/native 11개 유형 모순 | **11 OPEN** | **9개 복합 발화·2개 kind 정정, 내부 검토 기준 0 OPEN** |
| native kind의 출처 정정 | 1개 비주장 제거 | 추가 **2개 수정**, 65 원자 유지 |
| 실제 금융위험 표시 | 39/65 | **40/65**, 새 근거 위험 노출 |
| 기존 영상 source 관계/화면 보류 | 27 + 5 | **27 + 5 전부 E3 입력에 포함** |
| E3 검토 입구 | E2 최종 HOLD 때문에 미준비 | **65개 원문 패킷 생성 성공 — 검토 진입 가능** |
| E3/E4/E5 실제 연구 승인 및 저장 | NOT_RUN | **NOT_RUN**, 금융 승인·발행 0 |
| 독립 사전 고정 원자 gold 기반 P/R | 미측정 | **여전히 미측정** |
| speaker/stance 원음 기반 인증 | 65 UNKNOWN | **65 UNKNOWN 유지**, 검토 가설을 진실로 승격 금지 |

**구조적 진척은 소프트웨어 검증 대상의 *종류와 통합성*을 고친 데 있다.** 다만 독립 의미 품질 인증은 65개 미승인 원자를 곧바로 승인하는 문제가 아니다. **ChatGPT의 source-first 내부 review는 평가 예비 자료일 뿐, 독립성을 갖춘 blind gold가 아니고 원음/원화면도 없다**는 점을 지속 명시한다.

## F. 아직 외부/독립적 근거가 필요한 항목

- 원본 외부 독립 gold 또는 사전 고정·후보 격리된 검토 판정 250 cue의 실제 완성, gold-to-candidate 의미 동치·중복·조건/예외의 전수 비교, P≥95%, R≥98%, 고위험 FN=0의 **실측**.
- 원음/원화면 24개 risk cue 및 미연결 화면 발언 3개, 실제 화자·입장 인증. 자막만으로 누군지 확정하지 않는다.
- 금융 위험 40개 원자별 공식근거·적용범위·시점과 수치/단위 검증, 필요한 항목은 격리/보류.
- V176 역사 owner SQLite의 실제 사건 체인 확인 또는 레거시 지식 철저 격리; 신규 단일 영상 gold 측정과는 구분.
- E3 ChatGPT 실제 검토, E4 승인, E5 원자적 지식 저장은 **별도 적법 증거 확인 후** 수행. 현재 검토 패킷 *생성*만 완료, 승인된 사실 0개, 지식 발행 0건.

**최종 판정: E1 PASS, E2 source/structural/multi-axis ChatGPT 내부 검토 경로 PASS · 독립 의미 품질 HOLD, E3_REVIEW_INTAKE_READY_NOT_EXECUTED, E4–E5 NOT_RUN.** `main` 및 동결 V6/V123/V126/V127/V128 미변경, Draft PR #75 미병합.
