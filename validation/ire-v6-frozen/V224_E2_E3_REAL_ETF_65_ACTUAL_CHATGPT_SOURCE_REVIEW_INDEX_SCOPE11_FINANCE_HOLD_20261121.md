# V224 — ETF 원본 250개 자막 실제 ChatGPT 원자 65개 의미 심사와 전역 적용조건 누락 수정 (2026-11-21)

**정확한 판정: 실제 원본·출처 인용·조건 전파·원자별 내부 ChatGPT 심사 기록 PASS / 독립 정확도 인증·공식 금융 사실 최종 승인 HOLD.** 공개 GitHub에는 개인 SRT/원자 전문/실제 의미심사 비공개 자료를 보관하지 않았다.

## 1. 무엇이 실제로 부족했는가

V223의 `E3 review intake READY`는 **실제 원자별 최종 의미 검토가 아니라 미승인 입력 패킷 생성**이었다. 또한 V6 원자의 `source_refs` 자체는 정확해도 **멀리 떨어진 상위 담화 적용범위가 개별 투자 선택 권고에 상속되지 않는 결함**이 남아 있었다.

비공개 ETF 원본 `LVE7XN_esTc`의 45~47번 SRT는 진행자가 **이번 여섯 가지 선택 기준이 인덱스 ETF용임을 명시**한다. 그러나 `C00018,C00025,C00028,C00033,C00041,C00048,C00056,C00057,C00058,C00059,C00072`은 그 범위의 출처 cue를 `condition_cue_indices`/context로 상속받지 않았다.

이 결함은 원본 250 cue의 SHA, 원자의 primary quote, 숫자, CI 검증을 모두 통과해도 **전체 연구 지식에서는 조건 없는 ETF 보편 권고로 잘못 통합될 수 있는 실질 의미 결함**이다.

## 2. 실제 원본/최종 검토 입력

- 사용자 보관 ZIP `1-70.zip`의 원문 SRT SHA `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
- V223 미승인 native 65 SHA `32f541d8e0603b225db700122a3e0c95e54943455262b9959a7acfcc1864b091`.
- 이번 수정 native 65 SHA `757fb276be907d57405a005d503f7518609e985fc9322de95bced8158d947072`, 새 동결 V6 atom digest `28506dc077b7e4186767dcb299855d8c7c85cb4b591ef57ba05b0ce460de49d9`.
- 원자 65개 개별 ChatGPT 원문·문맥·예외·금융의미 실제 검토. 개별 판단/출처/텍스트·공식근거 참고자료/발표시점 위험/원문과 계산값 구분을 비공개 65행 결과로 영수증화.
- 전역 index-only 조건 **cue 45, 46, 47**을 **11개 적용 대상 원자**에 실제 조건/문맥 cue로 전파. 정식 V6 형태·소유창/primary/숫자/명제/kind는 불변.
- 금융 위험 원장 65행·원본 cue census 250행·ChatGPT 검토 패킷 65행을 **새 native SHA로 재고정**. 시각/음성 hold 5개 관계와 나머지 source 관계 27개, 위험 태그 40/65 그대로 보존.

## 3. 실제 원자별 ChatGPT 검토 판정 (65/65)

| 원문 의미상 판정 | 건수 | 정확한 의미 |
|---|---:|---|
| `TEXT_SUPPORTED_AS_SPOKEN` | **40** | 자막에서 말한 내용으로는 확인. **참인 금융 지식이라는 뜻 아님** |
| `SOURCE_SUPPORTED_AS_SPOKEN_WITH_MATERIAL_QUALIFICATION` | **17** | 발언은 확인하지만 적용범위·금융개념·조건 및 사실성 수정/한정 필요 |
| `TRANSCRIPT_ASR_OR_MISSING_REFERENCE_HOLD` | **8** | 원음·화면/전사·숫자단위 근거 부족으로 의미 확정 불가 |
| **합계** | **65** | 개별 이유가 서로 다른 65행, 텍스트 원문 SHA 결합 |

금융 사용성 재분류는 **견해/권고 17, 개념 검토·정식 금융 법령/원문 바이트 인증 전 16, 가상 예시 13, 용어·범위 정정 필요 10, 역사/실증 미확인 8, 화면 의존 1**이다. 40개 원자에 있던 위험표식은 보존했다.

**대표적인 실물 문제와 조치**

| 원자 | ChatGPT 실제 결론 | 처리 |
|---|---|---|
| `C00018,C00025,C00028,C00033,C00041,C00048,C00056,C00057,C00058,C00059,C00072` | 여섯 지표를 보편적 ETF 선별 절대원칙으로 사용하는 오류 위험 | cue 45~47 `INDEX_ETF_ONLY_SCOPE` 상속; 기존 세부 조건·예외 보존 |
| `C00029` | 화자의 '괴리율이 ETF에만 있다'는 배타적 일반화 부정확. KRX ETN에도 실질가치 대비 괴리율 지표 있음 | **현재 교육 사실 승인 거부**, source quote 보존 |
| `C00030,C00031` | ETF 순자산 계산에서 현금·부채/비용 및 총 발행좌수 반영과 기존의 주식합계/주식수 표현 분리 | 금융 개념 수정/한정 필요 |
| `C00032` | 가격과 NAV의 **금액차**와 **괴리율(%)**을 혼동 | 비율 정의 분리, 원문 발언 그대로 보존, 사실 승인 거부 |
| `C00035,C00039` | 추적차이·추적오차 정의 및 시장/운용 원인 단순 이분법 | 원음·정식 금융 정의와 시점 확인 HOLD |
| `C00045,C00046` | 0.001·0.002 단위 미상, '40km/45km' 몸무게 ASR | 원음 없이는 자동 수정 금지 |
| `C00049,C00051,C00053,C00063~C00067` | 영상이 '가상의 ETF 화면'이라고 선언한 수치·기초지수·보수 | 실제 ETF 데이터·현재 시세나 투자 지식으로 자동 발행 금지 |
| `C00065` | 예시 NAV 17,728원 대비 시장가격 17,645원 | *검토자 계산* -83원·약 -0.4682%, source utterance와 분리 |
| `C00070` | ETF가 모두 주식 바스켓이라는 범위 과장 | 채권형·합성/파생 ETF 등 존재, 사실 일반화 수정 필요 |

**2026년 현재 규정 유의사항:** 금융위원회는 2026-08-12 발표에서 2026-08-19부터 ETF·ETN 괴리율 관리 의무(종가 기준)를 국내 2%·해외 5%로 강화했다고 밝힘. 일부 KRX 오래된 교육 페이지의 이전 비율을 최신 법령으로 인용해서는 안 된다. 이 최신 정책은 **원본 영상이 그 시점에 같은 규정 하에 제작되었다는 주장도, 본 연구의 시행일/법령 원문 바이트 인증도 아니다**.

참고한 공개 출처(법령/자료 원문 바이트 검증이 완료되었다고 인증하지 않음):

- 한국거래소 ETF 가격/NAV·거래 구조: https://m.krx.co.kr/contents/06/0609/060901/JHPETP060901M01.jsp
- 한국거래소 NAV·괴리율 기본정보: https://open.krx.co.kr/contents/OPN/01/01030203/OPN01030203T1.jsp
- 한국거래소 ETN 괴리율의 존재: https://www.krx.co.kr/contents/OPN/01/01030302/OPN01030302.jsp
- 신한자산운용 SOL ETF 개념: https://www.soletf.com/ko/information/concept
- 금융위원회 ETF·ETN 2026-08-12 괴리율 관리 개선: https://www.fsc.go.kr/po010106/87512?curPage=6

## 4. 검증 엔진 구조 개선

새 재사용 코드 `v224_e2_e3_inherited_scope_review_gate.py`:

1. **단일 호출 11개 증거자료 바이트 원본 재검사**: 비공개 SRT, 수정 전·후 native, 전역 조건 리뷰, 금융 위험 전·후, cue250 전·후, 실제 65원자 ChatGPT 의미검토 65행, E3 패킷 전·후.
2. 동결 `audit_host_atomic_exchange`를 원본 250 cue의 구버전·신버전 원자 각각에 적용. **11개 조건/문맥 변화 이외 proposition·숫자·kind·owner·화자·원문 인용을 절대 변경하지 못함**.
3. 원자 간 **멀리 떨어진 상위 범위 조건의 상속**을 실제 cue SHA/인용과 원자 ID/조건 연결로 검문. 관련 권고의 범위를 잃으면 fail-closed.
4. 40개 기존 금융 위험과 250 cue 전체 처분을 새 native에 1:1 재연계. **cue 47**은 기존 잠정 담화에서 원자의 *조건 문맥*으로 이동, 삭제나 승인 아님.
5. ChatGPT 실제 원자별 검토 65행의 고유 판단 이유·원문/문맥 인용·참조·고정된 disposition·audio/gold/finance 미인증 플래그를 검문.
6. E3 미승인 검토 패킷의 27개 근거 관계와 5개 미확정 원화면/원음 quarantines가 유실되지 않는지 검문; 기존 확정 E4/E5는 차단.
7. 오디오/화면 없는 화자 인증, 허위 독립 gold, 허위 금융승인, 가상의 현물가격 승격, reviewer-only 계산 조작을 거부.

**실제 원본 250cue 동결 V6+새 원장+E3 text-review 통합 재생 PASS**. 승인 우회 시 `InvalidInput`으로 차단 확인. 공개 CI 합성 출처·누락·변조·허위 인증 회귀시험 **35개** 로컬 PASS. 기존 V223의 521 + 35 = **556개**를 공개 GitHub CI에 연결. 검증 브랜치 [GitHub Actions run 44851143064](https://github.com/yhappcom/pensionport/actions/runs/44851143064)의 실제 실행 로그에서 **556/556 PASS**(현행 E2 485 + 이전 E2 53 + E1 18)를 확인했다. 이 결과는 합성 코드·데이터 경로 회귀시험 PASS로, 비공개 금융 사실 승인 또는 독립 정답 기반 정확도 PASS는 아니다.

## 5. 비공개 개인 Library 증거

- `V224_PRIVATE_ETF250_INDEX_ONLY_GLOBAL_SCOPE11_REVIEW_UNAPPROVED.json` SHA `1812b84460b08d4d3dc55ef8f6ddf5eb7e73892c9db4a038a11c7cd1a37fafd1`
- `V224_PRIVATE_ETF250_NATIVE65_SIXCRITERIA_SCOPE_REPAIRED_UNAPPROVED.json` SHA `757fb276be907d57405a005d503f7518609e985fc9322de95bced8158d947072`
- `V224_PRIVATE_ETF250_FINANCE65_SCOPE_REPINNED_RISK40_UNAPPROVED.json` SHA `73601dd1dd5e1522037ba621771cd7ba867e78384853835a5f49a4fab907cad8`
- `V224_PRIVATE_ETF250_CUE250_SCOPE_REPINNED_HOLD.json` SHA `96cc35c83cd2d21dd1dfb46d6bc31ace1a41a081a9a01addf40c8afc0046da20`
- `V224_PRIVATE_ETF250_ACTUAL_CHATGPT_65_CLAIM_MEANING_FINANCE_DISPOSITIONS_HOLD.json` SHA `17b9d81cec3403a80f51617ebd1332c4a3c31a2f94a584edce113bc654af5ee4`
- `V224_PRIVATE_ETF250_E3_CHATGPT_65_ACTUAL_REVIEW_HOLD_PACKET.json` SHA `84de53900a66c0aad08a60e60c4b833a688fd6f840d17cfc758d051511f546a3`
- `V224_PRIVATE_ETF250_REAL_SOURCE_REVIEW_SCOPE_FROZEN_V6_RECEIPT_HOLD.json` SHA `7beabc1160db8c6a2cfa70d760691cfc4c5b155b708723efcc52508b2ac00b55`
- `V224_PRIVATE_ETF250_FULL_ONE_PASS_CUSTODY_RECEIPT_HOLD.json` — SHA `dc60ebc7fb1b32830e9642ca967dd342c7dd631744d09224dbfa3d66bb78ac5d`, 실제 11종 바이트/원본/V6/E3 일괄 재생 영수증.

이들 파일은 **이전 V223 산출물을 바꾸지 않는 append-only** 기록이다.

## 6. 단계 판정과 다음 실물 제약

**E1 PASS. E2 원문 구조·조건 전파·ChatGPT 65개 실제 내부 의미심사 기록 PASS, 그러나 독립 gold 정밀도·재현율 최종 HOLD. E3 ChatGPT 원문 의미검토는 실제 수행됐으나 E3 최종 승인 HOLD. E4·E5 NOT_RUN.**

- 원본 영상의 음성·화면 24개 위험 cue/미귀속 화면 보류 5개 관계 해결 없음; 화자 원음 신원 65/65 미확정.
- 현재 독립 정답셋 없음. 정밀도 95%/재현율 98%/고위험 FN=0을 **측정했다는 주장 금지**.
- 금융 공식 설명과 현재법 검토는 진행됐지만 **공식 시행일·법령 버전·원문 바이트 및 원자별 승인 맵**은 최종 미완료. 10개 수정/한정 필요 원자는 승인 불가.
- V176 역사 owner SQLite 원본 미확보. 신규 원본 한 편의 정확도 평가와 레거시 지식 병합은 별도 이슈로 관리하되 E5 역사 병합은 차단.
- 투자자문·포트폴리오 적용에 승인되지 않은 65개 원자/가상 상품 수치를 자동 사용하거나 지식 발행하지 않는다.

**`main`과 동결 V6/V123/V126/V127/V128은 변경하지 않고 PR #75는 Draft 상태 유지.**
