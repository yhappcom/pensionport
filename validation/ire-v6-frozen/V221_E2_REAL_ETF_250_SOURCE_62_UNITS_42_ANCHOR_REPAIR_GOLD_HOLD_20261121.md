# V221 — ETF 250-cue source-first 62 의미단위 ↔ native 66 원자 대표근거 정합성 보정 (2026-11-21)

**E2 결론: 실제 원본 기반 근거 위치 보정 42건 / 구조·출처 검사 PASS, 독립 의미 정답 및 최종 연구 승인 HOLD.** 기존 V219·V220 개인 원자·원장·동결 V6/V123/V126/V127/V128는 수정하지 않았다. 비공개 SRT 전문이나 원자별 전문은 GitHub에 게시하지 않는다.

## 1. 이전 PASS가 놓친 결함의 성격

V219의 동결 `audit_host_atomic_exchange` 구조감사는 **인용문이 실제 원문에 있는지**, 숫자·조건·소유구간이 올바른 형식인지 확인하지만, 인용문이 그 명제를 **의미적으로 직접 뒷받침하는지**는 독립 판정하지 않는다.

실제 영상 `LVE7XN_esTc` 250 cue를 기존 native 식별자를 보지 않는 **원문 전용 작업 순서**로 다시 읽어 62개 문맥/발화 단위를 작성한 뒤, V219 66 native 원자와 대응시킨 결과 **7개 원자의 primary cue가 해당 발화 의미단위 밖에 위치**했다. 나머지 일부 primary도 주장 내용을 직접 말하기보다 앞선 도입 또는 문장 조각에 붙어 있었다.

실제 대표 오류:
- `C00032`: ETF 시장가격과 NAV 괴리 설명을 cue **135**에 대표 고정했으나, 실제 설명은 **141~145**. 대표 cue **144**로 보정.
- `C00067`: 가상 ETF **123,477주** 거래량 주장에 415억 순자산이 포함된 cue **227**을 대표로 사용. 실제 수량 cue **228**로 보정.
- `C00029`: ETF에서만 괴리율이 나타난다는 과도한 배타 주장 cue 120(전환 발화)→cue **123**(발언 원문). 이 이동으로 소유 윈도 W00006→W00007을 함께 수정.
- `C00016`: '큰 ETF가 높은 수익률을 보장하지 않는다'는 반박의 대표가 cue 63(앞선 조언 끝)이었음. **65**(명시적 부정)로 수정.
- `C00035`: 추적 관련 오차의 정의를 도입 cue 152에만 대표 고정한 오류를 핵심 설명 cue **156**으로 수정, 추적차·추적오차 정의는 검토 보류.
- `C00060/C00061`: 가상 지수 +20%, ETF +18%의 **숫자 원문 위치 159/161**로 대표 이동.
- `C00063/C00064`: 가상 NAV 17,728원·시장가격 17,645원의 **실제 숫자 자막 218/220**을 대표로 이동.

## 2. 실제 개선 결과

| 항목 | V219 | V221 |
|---|---:|---:|
| 원본 cue/SHA | 250/250 PASS | 250/250 PASS, SHA 동일 |
| 미승인 native 원자 | 66 | **66**, ID·명제·숫자·조건·예외 불변 |
| source-first 의미/담화 단위 | 없음 | **62개 작성** |
| 의미단위와 적어도 한 번 겹치는 representative anchor | **59/66** | **66/66** |
| 대표 인용문 위치 수정 | — | **42개** |
| 그중 owner 윈도까지 변경 | — | **7개** |
| 최소 하나의 원자 대표근거를 갖는 cue | 63 | **65** |
| 원자 primary가 없는 cue | 187 | **185** |
| 미귀속 시청각 cue | 11 | **11, HOLD** |
| 차트 발언 미승인 후보 | V220 3 | **3 유지** |
| source-first 담화/원자 유형 충돌 | 미검문 | **1건 OPEN (`C00003`)** |
| 독립 TP/FP/FN·정밀도·재현율 | 미측정 | **미측정** |

42개 수정은 **인용 위치와 owner/cue disposition만 조정**한다. 66원자의 기존 발언·kind·numeric token·condition/exception·화자 `UNKNOWN`·stance `UNRESOLVED`은 바꾸지 않았다. 원문 중심성 개선은 **동일 ChatGPT가 작성한 내부 문맥 단위와의 일치도**이지 의미 정확도 100%나 독립 gold가 아니다.

대표 이동으로 영상 내 창 소유권이 바뀐 7건은 정확히 `C00015,C00026,C00029,C00032,C00040,C00061,C00065`이며 원본 20-cue window planner로 재계산했다. 수치가 다른 원자에 잘못 귀속되지 않았는지 frozen V6 numeric/source audit를 반복했다.

## 3. 62개 원문 전용 의미 판정의 범위와 보류

원본 source-only 문맥 구분: 담화/인사 4, 의견 3, 시점 의존 2, 원문에서 발언한 금융 개념 25, 권고 15, 비유/예시 3, 영상 차트 설명 3, 가상상품 화면 예시 7 = **62개**. 250 cue가 모두 최소 하나의 의미/담화 구간에 포함되었음을 검사했다.

이후 66개 native와 대응한 결과:
- native와 문맥이 연결된 source-only 발화 53개.
- 비주장·전환 잠정 3개, 비핵심 도입·비유 2개.
- **`SRC221-005` ↔ `C00003`: 6개 기준을 앞으로 설명한다는 안내와 '선택 권고'라는 원자 kind가 일치하지 않음 → OPEN 1건, 자동 승인·삭제 금지.**
- 화면 증거가 없는 설명 `SRC221-037`, `SRC221-056`, `SRC221-057`은 V220의 3개 시청각 미승인 보조 발화에 연결하고 **66 원자에 자동 병합하지 않음**.

이 자체가 외부/독립 평가 데이터가 아니며 작성자에게 기존 프로젝트 맥락 노출 이력이 있다. source-only 구간을 후보 원자 생성 시 직접 참조하지 않는 작업 순서로 만들었더라도 **완전한 독립 블라인드 gold라고 주장하지 않는다**. 동치의 one-to-one 판정이나 정밀도 95%/재현율 98%/고위험 누락 0의 수치 인증은 여전히 불가능하다.

## 4. 신규 소프트웨어 검문

`v221_e2_source_first_semantic_anchor_guard.py`는 다음을 통합한다.

1. **6개 원본 바이트 고정**: SRT·62 source-first 원장·V219 원자·V221 수정 원자·42개 보정 로그·62↔66 매핑의 SHA256과 실제 JSON 재확인.
2. **동결 V6 원본 재생**: 과거·신규 native 각 250 cue 모두 구조 감사. 자료 변조 및 금액·수치 토큰 귀속 실패 시 실행 차단.
3. **42개 수정 외 변형 차단**: `source_refs`, `owner_window_id`, `context_cue_indices` 이외 명제/kind/화자/입장/조건/예외/숫자 변경을 불허. 보정된 source quote가 실제 의미단위 안에 있는지 재검증.
4. **전수 관계 누락 차단**: 62개 source-first unit의 cue coverage, native 66 전체의 대응·대표근거 재계산. 화면 3개 별도 HOLD, 유형 불일치 OPEN 1건 보존.
5. **승인 인계 차단**: source-first 내부 리뷰만으로 독립 gold·화자 확인·금융 진실성·E3/E4/E5를 승인하지 못하게 강제. 기존 동결 운영 승인코드 직접 변조하지 않음.

공개 합성 원문 회귀시험 **22개**를 워크플로에 추가했다. 최종 커밋 전 단계의 [GitHub Actions run 44840883202](https://github.com/yhappcom/pensionport/actions/runs/44840883202)에서 전체 **440/440 PASS**(현행 E2 369 + 이전 E2 53 + E1 18), Traceback/FAILED 없음. 소유자 원본/원자 파일은 공개 CI에 업로드하지 않았고, 실제 private native 재실행은 별도 로컬에서 성공했다. 코드-only CI PASS가 독립 gold 의미 판정 PASS는 아니다.

## 5. 새 비공개 자료 (owner Library append-only)

- 원문 전용 62개 의미 단위: `V221_PRIVATE_ETF250_SOURCE_FIRST_INTERNAL_ANNOTATION_62_UNAPPROVED.json` SHA `119e10c5d0eabf0fa28caf50498148959648675907b143b2bad93dce8743907a`
- 수정된 66 native V6: `V221_PRIVATE_ETF250_66_NATIVE_42_SOURCE_ANCHOR_CORRECTED_UNAPPROVED.json` SHA `6f8a5179efd5bd0c743717fc82771f636fd6876d406d6d6870994255e2995038`
- 대표근거 42개 변경사건: `V221_PRIVATE_ETF250_42_PRIMARY_ANCHOR_CORRECTIONS_UNAPPROVED.json` SHA `c37b1f1023cb8041ab0704603e90a8f71409570d1025615acceaacf09ff59a3d`
- 62↔66 근거 대응표: `V221_PRIVATE_ETF250_62_SOURCE_UNIT_66_NATIVE_MEANING_CROSSWALK_UNAPPROVED.json` SHA `2cf73e4dbadf64bf6ec6f431a629c7c6481b382f3c7d50334a7c5785d077a8c5`
- 수정 후 250 cue 분류: `V221_PRIVATE_ETF250_REANCHORED_CUE_CENSUS_HOLD.json` SHA `5ba83494697944bd67c4993c97a312ad06be2aebd9da288547169f383c83ffc1`
- source-first/동결 V6 통합 실물 영수증: `V221_PRIVATE_ETF250_REAL_SOURCE_FIRST_FROZEN_REANCHOR_AUDIT_RECEIPT_HOLD.json` SHA `e5414982e7980d757ad0267407dc7efa7c67ad3b04b5c48fe45442a595125824`

추가 파일 6개는 개인 Library만 보존. 실제 원문 자막 전문·private 원자/판정 텍스트를 GitHub에 게시하지 않는다.

## 6. E2 단계의 잔여 실패 조건

1. **독립/블라인드 확정 gold 없음**. 따라서 P≥95%·R≥98%·고위험 누락 0을 수치로 인증할 수 없음.
2. **화자·입장 66개 미확정**, 원음·화면 위험 cue 24개와 미귀속 화면 주장 후보 3개는 미승인 보존.
3. **금융 의미 위험 39/66 및 추가 source-first 유형 불일치 C00003**을 승인할 만큼 공식자료·조건·시점·원화면이 확정되지 않음.
4. **V176 실제 역사 owner SQLite 부재**. 이는 신규 영상 gold-based 성능 측정과 논리적으로 분리 가능하지만 **역사 지식 병합/E5 레거시 재발행을 차단**한다.
5. **동결 E3~E5 현행 실물 승인 경로 NOT_RUN**, 개인 지식 저장 0건.

**최종 판정: E1 PASS; E2 실물 원문 출처·대표근거 감사 PASS / 의미 정확도 HOLD; E3–E5 NOT_RUN**. 신규 의미 단위 62개의 근거 매핑은 엔진의 오류 탐지 개선일 뿐 E2 전체 통과가 아님.
