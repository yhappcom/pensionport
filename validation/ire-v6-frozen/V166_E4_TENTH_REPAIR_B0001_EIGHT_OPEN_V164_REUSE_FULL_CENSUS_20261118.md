# V166 E4 제10차 — B0001 기존 V164 5 + E4 최근 3 = 원래 V123 OPEN 8건 전수 조정

**2026-11-18 KST, GitHub 증명 브랜치 · E1/E2/E3 PASS, E4 FAIL, E5–E7 NOT_RUN. 엔진 NO-GO.**

## 1. 중복 연구의 근본원인과 실제 추가 진전

새로운 OPEN 5건을 다시 '첫 의미분석'으로 시작하는 것은 잘못된 작업이라는 점을 **기존 V164 코드와 비공개 실제 영수증**으로 확인했다.

- 기존 `v164_typed_v123.py`의 `B0001_EXPECTED`와 비공개 `private/V164_PRIVATE_B0001_5_TYPE_SOURCE_REVIEW.json`에는 다음 5건의 실제 ChatGPT source-first 담화 분석 결과가 **이미 존재**: `C00001`(투자 손실을 우려하는 가정 질문), `C00003`(책의 사업 원칙을 투자에 적용해 보자는 토론 제안), `C00277`(안전마진·저가 조건에 따른 손실·잠재수익 가설), `C00285`(개인적 독서 난이도 평가), `C00293`(투자 확신을 묻는 질문). 각 행은 원문 cue·상황·검토메모 SHA, unknown speaker, 조건·반례, 금융 사실/실제 전략 성과/개인 자문 거부가 기록돼 있다.
- 최근 E4에서 추가 원전과 직접 cue를 확인한 **3건**은 `C00002` (영어 도서 서지/한국어 발음 미인증), `C00009` (버핏 주주서한 선집 범위 미확정), `C00010` (초기 파트너십 1957 제3자 전사/공격성·성과/화자 미확정). **원문 일부와 출처 귀속만 확인**, 세 원자 전체 정식 V123 PASS 아님.
- **중요 결함 수정**: 기존 `v166_e4_owner_open_partial_source.audit_partial_open_video_census`가 3건에 대한 부분근거 receipt을 검사한 뒤 `n_open_unapproved=3`으로 출력했다. 실제 B0001 원래 V123에서는 **OPEN 8건**이므로 이를 전체 unresolved 수라고 읽을 위험이 있었다. 변경 후 `n_open_unapproved`와 `still_open_claim_ids`는 **진짜 native V123 전체 OPEN**을 나타내고, `n_targeted_partial_claims=3`, `other_native_open_claim_ids` 5개를 별도로 표시한다. 3건 부분근거가 모두 있어도 전체 연구 통과 금지.

## 2. 새 E4 단일원본 8/8 전수 감사 코드

신규 `v166_e4_full_eight_open_census.audit_b0001_eight_open`:

- `VerifiedSource`의 원본 B0001 scope (cue 1~120), 모든 cue의 V123 원문 SHA, V6 원자 16개 SHA 및 원자별 실제 `source_refs` 일치 검사.
- 기존 V164 typed source-only 5행은 **기존 `v164_typed_v123.audit_typed_speech_row` 원코드로 검문**, 발언의 의미·인용 cue·원문 SHA·검토자 note SHA와 UNKNOWN 화자 규칙 재검사. **조건부 발언 `C00001/C00277`의 조건 cue와 `C00293`의 질문·인용 상태를 보존**. 개인적 견해나 가설을 실현 가능한 금융 수익이나 자문으로 승격하지 않음.
- E4 외부 문헌 부분근거 3행은 기존 `audit_partial_open_video_census`와 검문하고, **V123 OPEN 8건 정확한 집합**과 서로 겹치지 않는 5+3 구성을 요구.
- 반환은 `HOLD_ALL_EIGHT_NATIVE_OPEN_RECONCILED`; `approved_open_claims_newly_added=0`, `full_v123_video_pass=False`, `v128_real_owner_approved_knowledge_published=0`, `e5_authorized=False`. 전수 **근거·의미 검토 영수증의 연결**과 **주장 정식 승인**을 혼동할 수 없도록 계약으로 강제.

검증 `test_v166_e4_full_eight_open_census.py` **15개 합성 native V164+E4 결합 정상/변조 회귀**: 8/8 원자 검문, V164 행 하나 누락, E4 문헌 하나 누락/복제, OPEN를 ACCEPT로 부당 변경, 3건만 OPEN으로 위장, cue SHA 위조, 과거 V164 note SHA 위조, 원자 간 인용 대체, 화자 UNKNOWN 변조, 조건 cue 삭제, 질문→확정 사실 변경 등 모두 FAIL-CLOSED.

## 3. 실제 소유자 B0001 원본 독립 기계적 재검산

이번 작업에서 **비공개 실제 ZIP을 다시 열어** 다음을 수행했다:

- `1-70.zip` 영상 `5NvtBlmt93Y` 원본 **1,481개 cue** SHA `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`.
- `V164_PRIVATE_B0001_TYPED_V123_REAL_SOURCE_AND_V128_HOLD.zip`의 `V163_B0001_16_ATOMS_EXCHANGE.json` + 동결 `V163_B0001_FROZEN_NATIVE_V123_REVIEW.json`, 그리고 이전 V164 실제 source-only 5행과 지난 E4 실제 3건 부분근거 영수증을 **함께 조회**.
- 실제 V123 원본 **16개 원자 SHA 모두 일치, 120개 검토 cue SHA 모두 일치, 모든 원자 직접 인용 `69/69` 원문 일치**. 원래 OPEN 8개 중 직접 원문 인용은 **42/42** 일치: V164 source-only 5개 + 최근 E4 외부문헌 3개.
- 실제 기존 V164 5개의 **원문 cue 집합, 속성, memo SHA, 원자 직접 인용 anchor, unknown speaker, 가설·의견·질문 성격, `research_knowledge_export_allowed=False`** 검증. 이전 E4의 3개 각 원자 digest·인용 digest·보완자료의 한계와 정확히 결합.
- 비공개 새 영수증 (실제 소유자 파일): `/mnt/data/v166-private/V166_E4_PRIVATE_B0001_ALL_EIGHT_NATIVE_OPEN_RECONCILED_20261118.json`. SHA-256 **`632fee62fc74f9534178c25c1e797f7d00f99bd0c99e31b2bfbd9cde4fb8a342`**, 파일 권한 0600. GitHub에는 원문·비공개 평가 문장·음성이나 투자 포트폴리오 자료를 올리지 않음.
- **중요 한계**: 비공개 실제 8건은 로컬 원본 ZIP·이전 V164 검토 파일·E4 부분근거 증빙을 **독립 기계적 해시·cue 검문**으로 합친 것이다. GitHub Actions의 신규 Python `audit_b0001_eight_open` 함수는 **합성 120cue/16원자 fixture**에서 실행했으며 비공개 원본 전체를 GitHub CI에 올려 실행하지 않았다. 현재 작업 결과가 Native V123 신규 승인 영수증이라거나 V128 실제 발행 성공이라는 주장은 하지 않는다.

## 4. 결과·잔여 문제

- [E1–E4 최신 종합 GitHub CI](https://github.com/yhappcom/pensionport/actions/runs/44191720427): **9/9 jobs PASS**; E4 신규 native 8/8 재구성 15회 및 동결 V164 기존 테스트까지 성공.
- **B0001 8/8 OPEN의 원문·검토 증빙 연계는 완료**, 그러나 `C00002/C00009/C00010`은 오디오·서지 특정 판본·1957년 1차 문헌/화자 등 객관적 근거가 부족하고, V164 기존 5건은 source-only로서 금융 사실·자문용 지식으로 승인할 수 없다.
- **원래 동결 V123 결과 7 ACCEPT / 8 OPEN / 1 EXCLUDE = `CHAT_FINAL_HOLD_OPEN`**. 다음 이후 source-only 격리본 `7 ACCEPT / 3 OPEN / 6 EXCLUDE`는 재분류 뷰일 뿐 이 원래 V123 판정 자체를 수정하지 않는다.
- **실제 신규 V123 승인/실제 사용자 B0001 V128 발행: 0**, 13 구간 부모 발행 없음. E4 FAIL, E5/E6/E7 NOT_RUN.
- 운영용 외부 키/최신 owner PIN의 실물 배포·전수 투자자문 조회 경로 강제, 현행 금융법 적용일/예외를 포함한 실물 주장 한 건의 진짜 End-to-End V123→E4→V128 정상 발행 여전히 미완료.

**다음 E4 개선 기준:** 기존 8건을 새 분석으로 중복 수행하지 않고 **미확인 객관적 원전/오디오 3건**과 B0001 각 원자 간 의미 관계, OPEN 원자의 격리 정책과 온전한 13구간 정식 승인 가능성을 다룬다. 확정할 수 없는 주장은 추가 근거 없이 PASS하지 않는다. `main`·동결 V123/V126/V128·개인 원본과 포트폴리오 미변경.
