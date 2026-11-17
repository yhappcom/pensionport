# V166 E1 최종 실행 검증 — 합성 경로 PASS / 소유자 실물 연구 HOLD 유지

**작성 기준** 2026-11-17 KST. 대상: 사용자 확정 E1 "입력·검토·승인·저장 경로가 하나로 연결". **이 문서는 엔진 *구조적 연결* 검증에만 해당한다.** E2(의미), E3(실제 ChatGPT 판정), E4(실제 승인 품질), E5(실제 13구간 발행), E6, E7은 E1 증명에 포함되지 않는다.

## 1. 이 단계에서 발견하고 수정한 원인

- 문제: V164는 질문·가설 5개를 typed source-only로 검문하지만 `typed_final_knowledge_release_authorized=False`, `v128_parent_publication_authorized=False`. V126/V127은 원래 동결 V123 `require_chat_final_release`/ `assess_chat_final_gate`만 수용하므로 V164 결과가 저장 경로에 연결되지 않았다.
- 수정: V164의 출처 고정 발언 검문을 **동결 V123이 이미 지원하는 V143 `NON_RESEARCH_CONTENT` 격리 계약에 변환**하는 최소 어댑터를 도입했다. 핵심 공유 구현 `v166_shared_source_only_native_contract.py`을 B0001 5-원자 검문 래퍼 `v166_source_only_to_v123_quarantine.py`와 합성 부모 발행 시험 `test_v166_e1_same_typed_review_to_sqlite.py`가 공통으로 사용한다.
- 최소 권한: 새 어댑터는 **승인기가 아님**. `release_authorized_by_compiler=False`; 질문·가설을 금융 사실로 바꾸지 않으며 기존 V123·V126·V127·V128 구현과 그 보호된 digest를 수정하지 않는다.
- 기존 `unresolved_high_risk_omissions=12` 및 `disagreements_adjudicated=false`는 입력 그대로 보존. 원전 미확인 `C00002`, `C00009`, `C00010`은 자동 승인하거나 격리하지 않는다.

## 2. 동일 합성 입력 종단간 저장 시험 — 실제 CI 성공

- GitHub Actions: https://github.com/yhappcom/pensionport/actions/runs/44024787646
- 테스트 모듈: `test_v166_e1_same_typed_review_to_sqlite.py`, `test_v166_typed_to_native_quarantine.py`, 기존 `test_v128_continuous_chat_atomic_parent.py`.
- 결과: 신규 합성 **동일 입력**을 가진 후속 호출에서 아래 연쇄가 실제 실행됨:

```
V6 원문/원자/호스트 digest
  -> source-only typed row (원문 문구·원자 SHA·ChatGPT 검문 메모 검증)
  -> V166 공통 변환기로 V143 원자별 격리 기록
  -> 수정 없는 V123 재검문: CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY
  -> 실제 V127.1 checkpoint + V127 전 구간 결합 (합성 부모 2개 자식)
  -> V128 parent 최종 검문 + staging SQLite + 원자적 COMMIT
  -> V126 private knowledge: events=2, knowledge=2, parent_publications=1
```

이 사례에서 하나의 합성 가설 원자는 `SOURCE_SPEECH_ONLY`로 연구용 사실에서 제외되고 나머지 2개만 지식으로 저장됐다. **소유자 원본을 금융 사실로 승인한 것이 아니며, test fixture의 2개 자식을 13개 자식 실증으로 오인하면 안 된다.**

- 안전 반례 5종: 추가 금융 원전 미확인(부모 전량 발행 0), 원자 SHA 조작, 원문 인용 조작, 원래 V6 호스트 event 변조, 검토되지 않은 cue는 차단. 합성 양성+부정 6개 직접 시험 PASS.
- 회귀: V164 typed/ V166 B0001 변환 39 합성 시험, 기존 V143 source quarantine 및 V128 native 원자적 부모발행 회귀, E1 순서 규칙 검사 모두 성공. **CI 전용 합성 데이터, 정확도 인증 아님.**
- GitHub CI를 통해 저장 결과를 확인했으며 별도 API 모델, 유료 금융 자문 시스템, 실제 개인 포트폴리오는 이용하지 않았다.

## 3. 소유자 실제 #1 B0001 부정/안전 실행 — 별도 검문

사용자 비공개 라이브러리에서 V164 패킷, V163 원본 V6 DB, V160 manifest, 1–70.zip을 가져와 실제 원본의 SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`를 재검산했다.

1. 공개 저장소에서 바뀌지 않은 `v123_chat_final_gate.py`의 Git blob `17da9fae7d4fcc48087c55ca0d2031ba72a0bb3c`와 **바이트 동일한 V154 코드 아카이브를 비공개 작업공간에 추출**했다.
2. V164에서 실제 원문 120 cue와 16원자에 해시로 귀속된 질문·의견·가설 5건을 V164 원래 `audit_typed_speech_row`로 검문했다.
3. 원래 V123은 `7 ACCEPT / 8 OPEN / 1 EXCLUDE`였으며, **동일 V143 출처 고정 격리 형식**의 초안을 비공개 복사본에 적용해 동결 V123을 새로 실행한 결과 **`7 ACCEPT / 3 OPEN / 6 EXCLUDE`**였다.
4. V123 최종 결과는 예상대로 **`CHAT_FINAL_HOLD_OPEN`**, `finance_open=3`. 고위험 과거 카운터=12와 `disagreements_adjudicated=false`는 그대로다. `require_chat_final_release`가 발행을 거부했다.
5. 이 소유자 B0001 실행에서는 **V166 공유 컴파일러 코드를 직접 호출한 것은 아니고**, 공개 V166 컴파일러와 같은 V143 원자별 처분 구조를 비공개 메모리 복사본에 재현한 뒤 진짜 변경 없는 V123으로 재검문했다. 공개 E1 합성 시험과 구분해야 한다. 실물 원자 사실 여부, 금융 법규 및 고위험 누락 전수는 검증하지 않았다.

- 비공개 결과 파일: `V166_E1_B0001_PRIVATE_SOURCE_ONLY_NATIVE_V123_REPLAY.json`
- 그 비공개 파일의 SHA-256: `816402908b17055bbdba3839309c7a3def5e6449afcd1b5c7ce9acb23871eb90`
- 공개 GitHub에는 비공개 SRT/원자·화자 원문/실물 SQLite·도서 발췌 파일을 저장하지 않는다.

## 4. E1 합격 범위와 미완료 범위

**E1 PASS 권고 (기능 아키텍처에 한정):** 사용자 기준인 입력→의미 검토 기록→정식 승인기→전구간 staging→실제 지식 저장의 **동일 데이터 경로가 합성 입력에서 입증됐고**, 소유자 실물의 미검증 정보는 정상적으로 HOLD됐다.

**E1 PASS가 뜻하지 않는 것:**
- B0001 실제 최종 의미 PASS 아님.
- 영상 #1 실제 13구간 발행(0건) 아님.
- 유튜브 791편 확장성이나 독립 정확도 95%/재현율 98% 인증 아님.
- 실제 개인 투자자문 및 현행 법령 적용성 검증 아님.

향후 E2에서는 비공개 1,481 cue와 원자 전수를 활용해 질문·의견·가설·금융 사실·조건·예외를 **실제 의미 기준으로** 검토해야 한다. E2가 실패하면 그대로 E2에서 원인 수정하며 E3는 시작하지 않는다. E1 재검증에서 연결 결함이 다시 나타나면 그 즉시 E1 FAIL로 되돌린다.

**동결 V123, main, 13-child 실제 지식, 금융 승인, Master116/P4, 사용자 포트폴리오 불변.**
