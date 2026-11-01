# IRE — ChatGPT 대화 연계 연구 모드 (외부 모델 API 0회)

2026-11-01. 기존 연구 결과의 인용·정답 재사용·금융 사실 자동승인은 금지한다.

## 처리 모델

금융 의미 분석은 현재 사용자가 대화하는 ChatGPT 모델이 직접 수행한다.
IRE 소스 프로그램은 이 채팅의 모델을 무인으로 호출할 수 없으므로, 실행자가
현재 채팅에서 받은 문맥 패킷을 읽고 응답을 비공개 파일로 전달하는
CHAT_ASSISTED 프로토콜을 제공한다. API 키는 필요하지 않다.

1. prepare: SRT 바이트 SHA-256, cue 전체, 담화 구간, 비공개 세션 봉인.
2. next: 다음 미처리 문맥을 원본 인용 ID·문구·앞뒤 문맥과 함께 출력.
   --batch-size 2~12로 여러 구간을 한 번에 출력할 수 있다.
3. 현재 대화 모델이 금융 사건, 주체, 상품, 행위, 관할, 적용 시점,
   조건, 예외, 측정치, 양태를 명시한 원자 주장 JSON을 작성한다.
4. accept: 패킷·원문 해시, 인용문과 수치의 실제 원문 존재, 모든 primary
   cue의 처리상태(LINKED/NONCLAIM_CANDIDATE/UNRESOLVED)를 검사.
   복수 문맥은 전부 검사한 뒤 저장하므로 한 건의 위조 인용이 모든
   응답의 유효 저장을 중단한다.
5. status/next: 중단된 세션의 다음 미처리 구간을 자동 선택, 기존
   제출 답변은 변경하지 않음. 결과를 0600 비공개 경로에만 보존.
6. finalize: 모든 문맥이 제출된 경우에만 신규 주장 원장·관계 후보·
   공식 근거 연구 작업표를 만들고, 사실 승인 0건 및 BLOCKED를 기록.

이 프로그램은 ChatGPT 대화로 원문 패킷을 전달할 수 있게 준비하지만,
대화 바깥에서 스스로 모델을 실행하거나 도구 한 번으로 무인 완전 분석을
마친다고 주장하지 않는다. 현재 채팅의 컨텍스트 한계를 넘는 영상은
검증된 비공개 체크포인트로 이어서 처리한다.

## 실행 명령

개별 영상 준비:

    python -m ire.chat_bridge prepare \
      --original-srt /private/266.srt \
      --source-sha256 ACTUAL_SRT_SHA256_64_HEX \
      --video-id=-lX8iJd-xDM \
      --private-session-dir /private/ire_chat_sessions

다음 6개 담화 문맥을 채팅에 출력:

    python -m ire.chat_bridge next \
      --original-srt /private/266.srt \
      --source-sha256 ACTUAL_SRT_SHA256_64_HEX \
      --video-id=-lX8iJd-xDM \
      --private-session-dir /private/ire_chat_sessions \
      --batch-size 6

현재 채팅에서 만들어 별도 비공개 JSON 파일에 저장한 응답을 검사·기록:

    python -m ire.chat_bridge accept \
      --original-srt /private/266.srt \
      --source-sha256 ACTUAL_SRT_SHA256_64_HEX \
      --video-id=-lX8iJd-xDM \
      --private-session-dir /private/ire_chat_sessions \
      --private-reply-file /private/chat_answers.json

진행 상태 검사에는 accept 대신 status, 모든 구간의 초안 작성 완료
후 최종 연구 작업표 저장에는 finalize를 사용한다.

개별 답변은 IRE_CHAT_WINDOW_ANSWER_V1 형식으로 session_id,
window_id, packet_sha256, claims, cue_dispositions를 갖는다.
묶음 답변은 IRE_CHAT_BATCH_ANSWERS_V1 형식으로 session_id,
batch_sha256, answers를 갖는다. 모든 답변은 원문과 패킷 ID에
결속되어야 하며, 원문에 존재하지 않는 인용과 누락 cue는 즉시 차단된다.
각 claim의 frame과 source_refs 계약은 ire/claims.py를 따른다.

## 독립 근거 검증

공식 기관의 원문은 필요할 때 현재 채팅의 웹 검색/문서 조회로 새로
확보한다. 기존 투자 연구 결론은 금융 사실 근거로 사용하지 않는다.
최종 공식 사실 검증은 주장별 원문, 효력일, 관할, 예외, 산식 등을
독립적으로 확인해야 한다. 현재 채팅 모델이 만든 초안은
독립 검토자 두 명의 블라인드 정답과 동일하지 않다.

## 실제 초기 원본 적용 (#266)

새 SRT 바이트 SHA:
059484995ba7a84dd5ec21ed682a526b95832f65b56cea1cf48745548c2d8335

- 원본 cue: 771; 전체 담화 문맥 구간: 78.
- 이 채팅에서 처음 4개 문맥을 직접 읽고 초안 JSON을 작성·검사·보존.
- 검증된 4개 문맥에서 원자 주장 초안 8건 생성. 나머지 74개 문맥은 미처리.
- 원문 인용과 상태 검사는 통과했지만 금융 사실성·완전성은 미인증.
- 외부 모델 API 호출 0회, 정식 지식 승인 0건, 자동 병합 0건.
- 비공개 원본과 명제 초안은 GitHub에 커밋하지 않음.

## 보존 정책

main/기존 엔진 및 과거 연구 원장 불변.
프롬프트·패킷·원문 해시가 달라지면 기존 캐시 재사용 차단.
가짜 사실 승인, 출처 없이 주장, 검토자 독립성 허위 인증 모두 차단.
