# IRE V3 P0-A/P0-B/P0-C/P0-D 구현 명세 — 2026-11-02

## 개발 현황

V3는 별도 모델 API 없이 **현재 ChatGPT 채팅을 연구 해석 주체**로 사용하는
V2 위의 점진적 개선이다. 이 파일은 실제 구현과 미완료 목표를 구분한다.
원본 SRT·상세 원자 주장·사적 투자정보를 GitHub에 저장하지 않는다.

### 구현된 기능

1. `v3_orchestrator.py`: 배치 manifest의 실제 원본 파일을 SHA-256으로 검증한
   뒤, 모든 영상의 V2 ChatGPT 의미분석 체크포인트를 재확인한다.
2. `status`: 영상별 전체/완료/남은 분석 문맥 및 첫 미처리 문맥 공개.
3. `next`: 원본 우선 미처리 패킷을 영상 순서로 최대 12개, 최대 60,000자
   범위에서 내보낸다. 원본·이전 분석을 섞지 않는다. 제한보다 큰 문맥은
   조용히 생략하지 않고 오류로 중단한다.
4. `accept`: ChatGPT가 생성한 각 구조화 답변의 원본 cue, 실제 인용,
   video/session/window ID, 패킷 지문을 전체 사전검증한 후 개별 불변
   체크포인트에 기록한다. 손상된 결과가 포함된 배치는 저장하지 않는다.
   기록 중 I/O 장애가 발생하면 이미 기록된 응답만 보존되어 재개 가능.
5. `finalize`: V2의 배치 전수 검증, 기존 지식 스냅샷 최신성 검사 및
   미완료 차단 기능을 그대로 호출한다. 공식 금융 사실은 자동 승인하지 않는다.
6. `v3_semantic_candidates.py`: 특정 한국어 금융 표현과 약칭을 규칙 기반으로
   정규화한다. 서로 다른 두 가지 이상의 금융 개념이 일치한 경우에 한해
   기존 어휘/필드 일치 점수를 보완하며, **관계 후보만** 반환한다.
   자문 검색의 후보 재현율도 보완하지만 금융 사실이나 관계를 인증하지 않는다.

7. `v3_semantic_audit.py`: 금융 수치나 구체적 세제 규정을 단순
   비주장으로 분류한 경우 저장 전에 차단하고, 수치 주장에 필수 측정값이
   빠지면 차단한다. 복합 주장은 재검토 경고로 표시한다. 저장된 기존
   체크포인트에 대해서도 `audit` 명령으로 위험 여부를 검사한다.
8. `v3_adaptive.py`: 신규 원본에 한해 `window_strategy=V3_ADAPTIVE`를
   명시하면 기존 V2의 문맥 경계를 쓰지 않고 완료된 문장·휴지·금융
   개념 전환과 크기 상한으로 문맥을 재구성한다. 원본 cue는 100% 1회씩
   primary window에 속하며, 각 window의 본문은 금융 주장 자체가 아니다.
   기본값 `V2_COMPAT`는 이전과 동일한 session ID·체크포인트를 사용한다.
   적응형은 다른 세션 ID·불변 체크포인트를 사용하므로 이전 진행분을
   조용히 재활용하거나 덮어쓰지 않는다.

**중요:** 의미 분석의 실제 누락률과 원자 주장 정답률은 이번
규칙 기반 검사만으로 인증하지 못한다. 적응형 윈도 수가 줄어드는
것과 금융 사실이 정확해지는 것은 별개이다.

### P0-C 공식 원문 근거 검증 및 Decimal 검산 (이번 확장)

9. `ire/v3_evidence.py`: 기존 V2 근거 원장의 URL·원문 SHA·인용 검사에
   더하여, ChatGPT가 주장하는 관할·효력 시점·조건·예외·수치 일치마다
   **공식 문서에서 찾을 수 있는 정확한 scope anchor 인용**을 요구한다.
   `MATCH`·`CONFLICT`에는 해당 원문의 근거 문장이 반드시 있어야 하고
   `UNRESOLVED`·`NOT_SPECIFIED`는 실증했다고 위장할 수 없다.
   효력 시작·종료일은 문서 안의 해당 연·월·일을 검증하며, `numbers=MATCH`
   판정에는 원자 주장의 모든 수치 리터럴과 일치하는 근거가 필요하다.
   일치한 결과는 기존 V2 불변 근거 원장과 별도의 해시 봉인 V3 범위
   검토 영수증으로 비공개 저장한다.
10. `ire/v3_numeric.py`: 검증된 신규 IRE 주장에 실제 인용된 숫자와
    단위만 입력으로 받아 `Decimal`로 세후액, 분할 인출 잔액,
    기간별 총액 및 명목 회수기간을 독립 산술 검산한다. 발언 속 수치와
    연산 결과가 다른 경우 차이를 명시하되, 계산이 맞아도 세법 적용
    타당성이나 투자수익률을 인증하지 않는다. CLI 실행 시 상세 계산과
    원문은 비공개 감사 파일에 보관하며 공개 출력은 상태만 표시한다.

검증 계약은 `ire/contracts/evidence_v3.json`에 저장한다.
공식기관 도메인 허용 목록은 출처 후보 필터일 뿐 발행자 진위를
암호학적으로 인증하지 않는다. 현재 실제 네트워크 취득기는 HTML 및
일반 텍스트만 지원한다. PDF·동적 페이지·공식 법령의 법적 효력
최종 확인은 아직 별도 검증 대상이다.

#### 검증 실행 경로

ChatGPT가 공식기관 사이트에서 문서를 검색·검토하고 정확한 범위 인용을
작성한 뒤, 프로그램이 제출된 URL로 **직접 재취득**해 검증한다.
자막 전문과 인용된 주장 및 투자조건은 외부 모델 API에 전달하지 않는다.

```bash
python -m ire.v3_evidence review \
  --private-knowledge-snapshot /private/ire_kb/LATEST.json \
  --private-ledger /private/ire_evidence/LATEST.json \
  --private-chat-review /private/official_scope_review_v3.json \
  --private-evidence-dir /private/ire_evidence \
  --private-original-document-dir /private/official_bytes

python -m ire.v3_numeric verify \
  --private-knowledge-snapshot /private/ire_kb/LATEST.json \
  --private-calculation /private/source_cited_arithmetic.json \
  --private-audit-dir /private/ire_numeric_audits
```

실제 파일 경로는 예시다. `v3_evidence` 검토 입력에는 V2 필드 외에
`scope_anchors` 객체가 필요하며 5개 범위마다 공식 원문 발췌 배열을
제출해야 한다. 효과가 확인되지 않은 날짜·수치·예외는 명시적으로
`UNRESOLVED`로 처리한다. 근거 원문과 인용 문자열이 다른 경우
결과를 저장하지 않는다.


### P0-B 실전 의미 검토 정정: 원본 체크포인트 불변 유지

11. `ire/v3_corrections.py`는 저장된 ChatGPT 금융 주장 중 원문 인용보다
    뜻이 넓거나 수치 단위를 추정한 부분을 정정할 때 기존
    `answers/Wxxxxx.json` 파일을 **수정하지 않는다**. 동일 세션의
    `corrections/Wxxxxx_rev0001_<digest>.json`처럼 버전별 보충 원장을
    생성하고 최초 체크포인트 전체 바이트 해시, 직전 유효 답변 해시,
    원본 cue/세션/패킷 SHA-256, 정정 사유를 모두 연결한다.
12. `ConversationResearchSession._answer()`는 원본 체크포인트를
    자체 검증한 뒤 존재하는 정정 원장 전체를 순서대로 검증하고
    마지막의 수정된 답변을 적용한다. 원본이나 수정 원장의 내용 또는
    부모 해시가 조작되면 즉시 실패하며, 재개·배치·최종 원자 주장
    조립도 수정된 답변을 참조한다. 수정 이력도 금융 진위 승인이 아니다.
13. `ire.v3_orchestrator correct`는 비공개 수정안을 검증하고
    불변 수정 영수증을 저장한다. 수정 전·후의 완전한 창별 응답,
    그에 대한 원본 인용 검사가 필요하며, 기존 정답을 덮어쓰는
    임의 패치를 허용하지 않는다.

```bash
python -m ire.v3_orchestrator correct \
  --private-manifest /private/batch.json \
  --private-correction /private/corrected_window_review.json
```

수정안은 `IRE_V3_CHAT_CORRECTION_SUBMISSION_V1` 스키마이며
`schema, video_id, session_id, window_id, packet_sha256,
prior_answer_sha256, reason_codes, affected_claim_ordinals,
review_note, reviewed_as_of, corrected_answer`가 필수다.
`corrected_answer`에는 해당 창의 `claims, cue_dispositions`가
**전체 재제출**되어야 한다.

#### 2026-11-02 #1~#5 원본 재현 시험

- 개인 Google Drive의 `1-100.zip`을 재확보해 원본 SHA-256을
  기존 공개 진단 해시와 재대조했다. 5편 총 5,129 cue를 재검증했다.
- V3 적응형 planner B의 문맥은 총 346개다. 기존 V2는 517개이며
  모든 cue의 primary 소유권은 정확히 1회이다.
- #1의 W00001~W00008: 8개 창, 잠정 금융/교육 원자 주장 31건을
  실제 자막을 읽고 작성·저장했다. 나머지 338개 창은 미처리.
- W00003의 2개 문구 오류를 수정했다. 첫 번째 원문만으로 월 단위를
  추정하지 않고 W00005 cue 55의 별도 월 단위 설명과 구분했다.
  개인연금이라는 일반 표현을 그 창만으로 특정 세제계좌로 확대하지 않았다.
- 원본 W00003 캐시 파일은 v001과 v002의 SHA-256이 같다.
  정정 영수증 파일만 신규로 추가했다. 모든 수정·신규 응답은
  비공개 Google Drive `IRE_V3_001-005_private_checkpoint_v002_20261102.zip`
  에 저장했으며, 새 격리 환경에 재복원해 8개 창·W00009 재개를 검증했다.
- 국민연금공단 및 현행 소득세법의 공개 문서 후보와 5개 산술 예제를
  별도 조사했지만 **공식 원문 바이트 재취득·법령 적용범위·인적
  독립 검증·자문 정확도 승인**을 완료한 것은 아니다.
- 이번 확장 포함 GitHub Actions 합성 회귀시험 174건 통과.
  `ire/tests/test_v3_corrections.py` 9건은 수정/사칭/변조/재해시 공격을 검사한다.

### ChatGPT 호스트가 수행하는 내부 명령

사용자에게 각 단계의 JSON 입력을 요구하지 않는다. 아래는 ChatGPT가 실행할
수 있는 도구가 있을 때 내부적으로 사용하는 CLI이다.

```bash
python -m ire.v3_orchestrator status --private-manifest /private/batch.json

python -m ire.v3_orchestrator next --private-manifest /private/batch.json \
  --max-packets 4 --max-chars 18000

# 기존 저장 응답까지 포함하여 금융 비주장 누락 위험 감사
python -m ire.v3_orchestrator audit --private-manifest /private/batch.json

# 현재 ChatGPT가 원본 문맥을 해석한 후, 생성한 비공개 답변 파일을 제출
python -m ire.v3_orchestrator accept --private-manifest /private/batch.json \
  --private-submission /private/current_chat_answers.json

# 모든 영상의 전체 문맥 처리 후에만 지식 통합 시도
python -m ire.v3_orchestrator finalize --private-manifest /private/batch.json \
  --private-knowledge-dir /private/ire_kb \
  --private-audit-dir /private/ire_audits
```

기존 지식이 있는 경우 `finalize`에 반드시
`--prior-knowledge-snapshot`을 전달하고, 근거 원장이 있으면
`--prior-evidence-snapshot`, `--private-evidence-dir`도 전달한다.
오래된 버전의 지식 스냅샷을 사용한 덮어쓰기는 V2가 차단한다.

### 적응형 문맥 모드 선택

사용자에게 직접 요구하지 않는 비공개 입력 매니페스트의 영상 항목에
`"window_strategy":"V3_ADAPTIVE"`를 명시하면 신규 적응형 계획으로
실행된다. 이 필드를 생략하면 `V2_COMPAT`로 처리되어 2026-11-02 이전
V2 체크포인트를 그대로 사용할 수 있다.

```json
{"video_id":"ABCDEFGHIJK",
 "original_srt_path":"/private/001.srt",
 "source_sha256":"실제로_확인한_64자_SHA256",
 "private_chat_sessions_path":"/private/ire_sessions",
 "window_strategy":"V3_ADAPTIVE"}
```

실제로 생성한 원본 해시 및 원본 경로만 사용한다. 기존 원본의
체크포인트가 있어도 모드 변경 시 V3 새 세션으로 분리된다.
새 모드가 더 적은 문맥 수를 만든다는 보장은 없으며 전체 cue 수,
출처 연속성, 의미 정확도는 별도로 검증한다.

### ChatGPT 제출 규격

`next`의 `batch_sha256`, `max_packets`, `max_chars`를 그대로 전달한다.

```json
{
  "schema": "IRE_V3_CHAT_SUBMISSION_V1",
  "batch_sha256": "next에서_받은_64자_SHA256",
  "max_packets": 4,
  "max_chars": 18000,
  "answers": [
    {
      "video_id": "원본_영상_ID",
      "submission": {
        "schema": "IRE_CHAT_WINDOW_ANSWER_V1",
        "session_id": "next의_session_id",
        "window_id": "next의_window_id",
        "packet_sha256": "next의_packet_sha256",
        "claims": [],
        "cue_dispositions": []
      }
    }
  ]
}
```

`claims`와 `cue_dispositions`는 실제 원문 금융 의미분석 결과를
채워야 하며, 위 빈 배열은 완료 예시가 아니다. cue 100% 누락 없이 기록하고
미해석 주장은 `UNRESOLVED`로 남긴다. API로 모델을 무인 호출하지 않는다.

## 완료되지 않은 P0/P1/P2 작업

- **P0-B:** 기본 원본 처리 경로는 기존 V2와 호환된다. 신규 옵트인
  V3 적응형 분할 및 고위험 비주장 누락 검사는 구현·합성 검증됐지만,
  실제 영상으로 분할 효율·금융 의미 재현율·복합 주장 완전성을
  측정하는 독립 검증은 아직 필요하다.
- **P0-C:** 공식 HTML/텍스트 원문을 독립 취득하여 인용·날짜·범위·수치를
  검증하는 코드와 Decimal 검산은 구현·합성 검증한다. 그러나 발행기관
  게시물 진위·법적 효력·실제 금융 주장 정확성은 별도 확인 필요.
  공식 PDF·동적 페이지 처리는 아직 지원하지 않는다.
- **P0-D:** 규칙 기반 후보 검색은 개선했지만, 정량 의미 검색 재현율은
  별도 미노출 원본/독립 심사자 판정 없이는 알 수 없다.
- **P1:** 실전 누적 주제 통합, 기존 지식과 상충 검토의 독립 정확도 검증.
- **P2:** 현행 법규·투자자 적합성 재확인에 근거한 실제 자문 평가.
- **실행 한계:** 저장소의 Python은 별도 API 없이 ChatGPT를 스스로 호출할
  수 없다. 채팅 시간/문맥/도구 제약으로 한 번의 요청에서 반드시 모든
  원본 문맥을 완주한다고 보장하지 않는다. 채팅 종료 후 자동 백그라운드
  실행도 보장하지 않는다.
- **원본 연구:** #1~#5의 5,129 SRT cue에 V3 planner B 분할을
  실제 수행했다. 346문맥 중 #1의 8개만 분석·정정 저장하고
  338문맥은 미처리다. 전체 의미분석·금융 진위 검증/승인은
  미완료이다. 비공개 원문·원자 주장 상세·공식 검토 영수증은
  공개 GitHub에 저장하지 않는다.

## 검증 정책

`ire/tests/test_v3_orchestrator.py`,
`ire/tests/test_v3_semantic_candidates.py`,
`ire/tests/test_v3_semantic_audit.py`,
`ire/tests/test_v3_adaptive.py`,
`ire/tests/test_v3_evidence.py`,
`ire/tests/test_v3_numeric.py`,
`ire/tests/test_v3_corrections.py`의 합성 시험은 기능 회귀 시험이다.
실제 원본/독립 평가자 골드가 없으면 recall·precision 및 금융 자문 신뢰도
인증을 표시하지 않는다. 모든 의미 관계는
`PENDING_SEPARATE_ADJUDICATION` 상태에 머문다.

기존 `main`, 과거 260편 연구, V2 PR #10은 보존한다.
V3 변경은 별도 Draft PR로 검토한 후 통합한다.
