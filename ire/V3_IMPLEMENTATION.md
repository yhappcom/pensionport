# IRE V3 P0-A/P0-D 구현 명세 — 2026-11-02

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

### ChatGPT 호스트가 수행하는 내부 명령

사용자에게 각 단계의 JSON 입력을 요구하지 않는다. 아래는 ChatGPT가 실행할
수 있는 도구가 있을 때 내부적으로 사용하는 CLI이다.

```bash
python -m ire.v3_orchestrator status --private-manifest /private/batch.json

python -m ire.v3_orchestrator next --private-manifest /private/batch.json \
  --max-packets 4 --max-chars 18000

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

- **P0-B:** 금융 발언 단위의 적응형 문맥 재구성 및 과도한 비주장 분류의
  누락 위험 감사. 현재 V3는 V2 기존 문맥 경계를 보존한다.
- **P0-C:** 실제 공식 기관 원문 다운로드·적용일·예외·수치 독립 검증.
- **P0-D:** 규칙 기반 후보 검색은 개선했지만, 정량 의미 검색 재현율은
  별도 미노출 원본/독립 심사자 판정 없이는 알 수 없다.
- **P1:** 실전 누적 주제 통합, 기존 지식과 상충 검토의 독립 정확도 검증.
- **P2:** 현행 법규·투자자 적합성 재확인에 근거한 실제 자문 평가.
- **실행 한계:** 저장소의 Python은 별도 API 없이 ChatGPT를 스스로 호출할
  수 없다. 채팅 시간/문맥/도구 제약으로 한 번의 요청에서 반드시 모든
  원본 문맥을 완주한다고 보장하지 않는다. 채팅 종료 후 자동 백그라운드
  실행도 보장하지 않는다.
- **원본 연구:** #1~#5의 5,129 SRT cue 및 V2 517문맥에 대해 V3
  전체 의미분석·금융 진위 검증을 실행하거나 승인한 것은 아니다.
  현재 GitHub에는 해당 비공개 원문이나 공식 검토 증거가 없다.

## 검증 정책

`ire/tests/test_v3_orchestrator.py`와
`ire/tests/test_v3_semantic_candidates.py`의 합성 시험은 기능 회귀 시험이다.
실제 원본/독립 평가자 골드가 없으면 recall·precision 및 금융 자문 신뢰도
인증을 표시하지 않는다. 모든 의미 관계는
`PENDING_SEPARATE_ADJUDICATION` 상태에 머문다.

기존 `main`, 과거 260편 연구, V2 PR #10은 보존한다.
V3 변경은 별도 Draft PR로 검토한 후 통합한다.
