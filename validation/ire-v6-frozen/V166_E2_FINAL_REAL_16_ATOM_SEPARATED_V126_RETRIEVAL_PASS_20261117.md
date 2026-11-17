# V166 E2 — 최종 원문 의미구조·조건/대비·V126 안전 조회 검증

**2026-11-17 KST · 사용자 확정 E2 기준: "질문·의견·가설·금융 사실을 구분하고 조건·예외 보존"**

**판정: E2 PASS (실제 B0001 120 cue / 16원자 + 합성 통합 회귀시험에 한정). E3~E7 아직 NOT_RUN.**

## 1. 코드의 정확한 버전과 비공개 원본 직접 실행

- 검증한 실제 GitHub E2 코드: `validation/ire-v6-frozen/v166_e2_semantic_separation.py` **Git blob SHA-1 `ffbce2f412cd73488faba489dc1b6bb35f9c8811`**. 사전에 확보한 실제 파일 바이트에 대해 `git hash-object` 재계산으로 **일치**를 확인했다. 별도 구현을 같은 것으로 오인하지 않는다.
- 원본 SRT SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`. 사용자 라이브러리 `1-70.zip` 원본 자막 및 V160 매니페스트, V164 `V163_B0001_16_ATOMS_EXCHANGE.json`을 비공개 로컬에서 직접 읽어 `verify_source`로 원본 전체 출처 검증.
- 기존 ChatGPT 작성 비공개 16행 의미 사이드카 원문 파일 SHA-256 `d970713e83116af3baafc07459eb6856145e7d4ea67340821e577f796c50113e`, canonical JSON digest `e6c7e1feaf214cc30c8bf3725925c1ea244877f4190f454955971d5756fd3757`.
- **정확한 검증 함수 `audit_e2_semantic_ledger(source, exchange, ledger)`를 원본 16행에 직접 실행했고 16/16 검문 PASS**. 이는 기존 V166 E2 보고서의 "별도 기계 검산만 수행" 장애를 해소한 것.

| 실제 소유자 B0001 E2 검산 항목 | 결과 |
|---|---:|
| 원문 자막 / 원자 | 120 cue / 16원자 |
| 원자-원본 SHA / 의미 타입 / 문맥 SHA | 16/16 검증 |
| 기존 V6 조건 연결 보존 | **2개 원자** |
| 기존 V6가 명시한 exception cue | **0개 원자** (원문에 예외·대비 없음의 인증 **아님**) |
| 의사소통 의미상 사실 의존관계 | **9개, 모든 원전 상태 OPEN** |
| 숫자 ASR 불명확 토큰 | **1개** |
| 동일 E2 코드의 실제 원본 대상 변조·부적법 승격 반례 | **13/13 차단** |
| 금융 사실 검증, 외부 블라인드 gold, 개인 투자자문 | **인증 없음** |

실제 반례: 원본 SHA, 원자 SHA, 원문 인용, 조건 삭제, 검토자 note SHA, 사실 의존관계 삭제, 숫자 누락, 허위 원전 승인, 무근거 화자 특정, 검토자 주의를 화자 인용으로 바꾸기, 개인 자문 승인, FACT를 개인 의견으로 축소, 원자 누락. **모두 정확한 공개 E2 검증 함수로 오류 판정.**

## 2. 원자 간 담화 관계 보존 — 5건 실물 확인

단순히 과거 V6의 `exception_cue_indices=[]` 값이 그대로라는 이유만으로 문맥이 완결됐다고 주장할 수 없다. ChatGPT가 원본 120 cue를 읽어 다음 **원자 사이** 연결을 추가 점검했다.

| 원자 연결 | 구분 | source cue | ChatGPT 의미 판단 |
|---|---|---:|---|
| C00001 ↔ C00293 | QUESTION_REFINEMENT | 5 | 손실 위험 질문 뒤 투자 확신이 무엇인지 다시 묻는 연결 |
| C00004 ↔ C00005 | CONTRAST | 73 | 번역·설명의 어려움과 전체 메시지의 단순성은 함께 존재 |
| C00008 ↔ C00277 | QUESTION_COMPARISON | 94 | 책의 손익 비대칭 원칙과 안전마진 개념의 비교 질문이며 성과 동일성 확정 아님 |
| C00009 ↔ C00010 | CONTRAST | 107 | 후기 주주서한의 설명과 초기 파트너십을 대조하며, 역사 사실은 별도 검증 |
| C00284 ↔ C00007 | SPECULATION_VS_SOURCE_DESCRIPTION | 85 | 제목 번역 이유에 대한 추측과 어원 설명을 혼동하지 않음 |

원문/두 원자 문맥/해당 cue 텍스트 SHA-256/ChatGPT 검토 메모 SHA를 검증하는 `audit_e2_cross_atom_discourse`를 **정확한 공개 E2 코드로 실행해 5/5 PASS**, 위조 source cue, 미존재 원자, 금융 진위 허위 인증, 중복 관계, note SHA 변조 **5건 모두 차단**. 비공개 담화 원장 canonical digest: `0ef095d3b717c631cd80b8c5ec3e7a9cdd70552c33de7617ed4af6409a98278c`.

이 단계는 **실제 예외 문구를 임의 생성하지 않고**, 원래 V6 조건 2개를 보존하면서 기존 원자 간의 대조·수식 관계도 별도 출처에 고정하는 개선이다. 없는 조건을 원본 출처로 조작하지 않는다.

## 3. 승인 지식의 조회에서 화자·검토자 문장 혼합 차단

- 실제 코드 확인 결과, 동결 V126 `PrivateKnowledgeStore.evidence_for_question`는 기존 `atom.proposition`을 포함한 원자 전체를 반환한다. 일부 원자의 `proposition`에는 **화자 발언을 요약한 부분과 ChatGPT의 부가 위험 주의사항**이 하나의 문자열에 들어 있다.
- E2에 **`build_e2_source_separated_context_packet`**과 **`source_separated_evidence_for_question`**을 추가했다. 둘 모두 E2 원본/원자/의미 검문을 통과한 경우에만 별도 구조로 반환하고, 기존 V6 `proposition`은 *화자 원문 인용 필드로 절대 전달하지 않는다.*
- 결과의 `source_verbatim_quote`는 SRT 원문에 실제 있는 바이트만 사용하고, `source_speech_paraphrase`는 `CHATGPT_PARAPHRASE_NOT_ORIGINAL_SPEAKER_QUOTE`, `reviewer_caution`는 `CHATGPT_CAUTION_NOT_ORIGINAL_SPEAKER_QUOTE`로 **역할 고정**.
- 실제 소유자 16개 행으로 전자를 실행: **원문 직접 인용 16/16, reviewer 주의사항 분리 16/16, 9개 사실 의존관계 OPEN 유지, 지식 발행 False**.
- 더 나아가 실제 V128 **합성 원자적 SQLite 부모발행→V126 실제 active knowledge 조회→E2 안전 출력 변환** 통합 검증을 수행. **비공개 SQLite 조회의 기존 `atom.proposition`이 답변용 안전 출력으로 노출되지 않음**, 타 구간의 E2 사이드카 부재·검토자 note SHA 위조·출처에 없는 인용은 차단.
- 합성 UNKNOWN speaker에게 V146 필수 화자 의미 출처 영수증을 누락했던 최초 CI가 예상대로 FAIL: https://github.com/yhappcom/pensionport/actions/runs/44030321082. V146을 수정/우회하지 않고 실제 V146 source-pinned synthetic provenance 원장을 추가. **재실행 CI 전부 SUCCESS:** https://github.com/yhappcom/pensionport/actions/runs/44030447901.
- 여전히 기존 V126 저장 DB, V123/127/128 원본 바이트를 변경하지 않았다. 현재 E2 함수가 제공하는 것은 **검토자용 source-separated evidence context**이며 자동 최종 자문 답변은 아니다.

## 4. E2 판정과 엄격한 활용 제한

**E2 합격 근거:** 사용자 기준인 질문/의견/가설/사실 구분 + 실제 원문 문맥/조건·대비 보존 + 화자·검토자 설명 분리 + 잘못된 발언 사실 승격/원문 변조 차단을 **실제 B0001 16원자/120 cue, 정확한 버전 코드 및 격리된 V126 실제 조회 합성 테스트에서 검증**했다.

**E2에 포함되지 않고 여전히 금지된 주장:**
- 실제 영상 #1의 나머지 12구간 또는 791개 영상의 전수 의미 완료, 독립 정밀도 95%/재현율 98%, 고위험 FN=0 증명.
- B0001 `C00002`, `C00009`, `C00010` 등 외부 사실의 진위 승인 및 과거 V123 HOLD 해제. B0001 실제 연구 발행은 여전히 **0**.
- ChatGPT 최종 승인 원장(E3), 정식 금융 근거·승인 관문(E4), 13개 구간 원자적 실제 지식 발행(E5), 재실행(E6), 투자자문 답변(E7).
- 원자 의미 행은 ChatGPT가 원본을 읽고 작성한 **source-first 검토**이고, 별도 외부 블라인드 골드셋이 아니다. CI 녹색은 그 의미 내용 자체의 외부 독립 정확도 인증이 아니다.

**다음 단계:** 상태 원장 `E2=PASS`, `E3=NOT_RUN`, `current_step=E3`로 전환 후 E3의 **승인·보류·격리 판정 전달 정확성**을 새 검증으로 시작할 수 있다. 이전 단계의 회귀·출처 결함이 다시 발견되면 즉시 E2 FAIL로 롤백하며 그 이후 단계로 진행 금지.

**변경하지 않은 보호 대상:** `main`, 동결 V123/V146, V126/V127/V128, 비공개 SRT/원자 전문·SQLite, Master/P4, 개인 포트폴리오.
