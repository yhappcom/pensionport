# 박곰희TV 학습 워크플로 — 간소화 버전 2 (2026-10-08)

## 목적과 범위
이 프로젝트의 유일한 목적은 박곰희TV의 **영상 내용을 근거 기반으로 학습하고, 투자 판단에 유용한 통합 지식**을 축적하는 것이다. 인프라 점검·목록 재수집·로그 작성은 학습의 대체물이 아니다.

- 영상 목록은 `VIDEO_INVENTORY_2026-10-07.md`로 **고정**한다: 전체 791편, 분석 대상 롱폼 703편, Shorts 88편 제외. 별도 요청 전까지 목록 재탐색 금지.
- 기존 `data/videos.jsonl`, `data/canonical_events/`, `data/analysis_events/`, `knowledge/`, `synthesis/`는 **보존**한다. 기존 canonical은 분석 기록 등록을 뜻하지 모든 영상의 심층 검증 완료를 보장하지 않는다.
- 이 파일은 이전 복잡한 workflow의 **전면 대체본**이다. 옛 794-baseline/discovery, writer-lease 필수 획득, 무조건적인 대형 파일 compaction, 반복 인프라 진단은 실행하지 않는다.

## 실행 — 영상 분석이 먼저다
1. 최신 `main`에서 roster, `data/videos.jsonl`, `data/canonical_events/`, `data/analysis_events/`를 조회해 처리된 **고유 video_id**와 미처리 롱폼을 찾는다. `state/progress.json` 숫자를 그대로 믿지 않는다. 완료율 = 로스터 롱폼에서 분석 기록이 저장된 고유 영상 수 / 703. 기존 이벤트와 base 사이 중복을 제거한다.
2. **미처리 영상의 정확한 YouTube 링크**를 사용한다. 한국어 전사 확보는 정상적으로 지원되는 Firecrawl Alexandria `youtube/read`를 우선 사용한다. 영상별 하나의 요청으로 `## Transcript`와 실제 본문을 확인한다. 제작자 설명·챕터·신뢰할 수 있는 해당 ID의 상세 정리자료는 보조자료다. 원문이 없으면 근거가 있는 부분까지만 PARTIAL로 표기한다. 접속 차단·이용조건을 우회하지 않는다.
3. **음성 원문 내용 전체를 충분히 검토**한 뒤 주제·핵심 주장·근거·실행 방법·적용 조건·위험·예외·숫자·기존 지식과의 관련성(NEW/REINFORCE/EXTEND/CHANGE/CONFLICT/TIME_SENSITIVE)을 정리한다. 자동 자막의 명백한 인식 오류는 추측하지 않고 미확정으로 표기한다. 세법·ISA·연금·건강보험·거래소 기준 등 시점 의존 항목은 가능한 공식 1차자료로 교차검증하고 당시 내용과 현행 사실을 구분한다. 자막만 읽었으면 화면 검토 완료라고 하지 않는다.
4. **한 영상의 분석이 끝나는 즉시** `data/analysis_events/<video_id>.json`을 저장하고 다시 읽어 내용을 확인한다. 최소 필드: `video_id`, `source_url`, `source_level`, `published_at`(알면), `title`, `core_claims`, `actionable_guidance`, `assumptions`, `risks_and_exceptions`, `quantitative_claims`, `relations`, `verification_status`, `limitations`. 공개 저장소에 전사 전문을 복사하지 않는다.
5. 저장된 분석 artifact가 있고 기존 base/canonical에 video_id가 없다면 가장 최근 event 번호를 다시 조회하고 `data/canonical_events/<max_sequence+1>_<video_id>.json`을 **한 번만 생성**한다. 양쪽 파일의 존재를 재확인한 경우에만 신규 분석 1편으로 센다. 이미 artifact만 있는 영상은 분석을 다시 하지 않고 event 연결만 복구한다. 같은 id 및 event 번호 중복 저장을 피한다.
6. **한 번에 3~5편을 목표**로 하되 근거 품질을 우선한다. 실제 시간/도구 제약 시 1편도 정당하다. 자막 확보·인프라 점검만 반복하는 회차는 성공으로 보지 않는다. 매 10개 고유 canonical마다 `knowledge/`, `synthesis/`에 투자원칙·일관성·충돌을 주제별로 통합한다.

## GitHub 쓰기와 동시성 — 단순화
- **새 예약작업은 하나만 사용한다.** 일반 실행에서 `state/execution_lock.json`을 읽거나 갱신할 필요가 없다. 기존 lock 파일은 과거 호환성을 위해 보존하되 새 작업의 시작을 차단하지 않는다.
- 전역 파일 수정은 최소화한다. `data/videos.jsonl`, `data/learning_queue.jsonl`, `data/claims.jsonl`은 일반 회차에서 **읽기 전용**이다. 진행률은 언제든 실제 base+event로 복구 가능하다. `state/progress.json` 업데이트는 선택사항이며 영상 분석의 전제조건이 아니다.
- 각 영상은 `video_id`로 중복 검사를 하고 artifact → event를 **직렬 저장**한다. 수동 분석이 동시에 진행 중이면 같은 ID/번호 파일을 만들지 않는다. GitHub 파일 생성의 중복 또는 sequence 충돌 시 새 후보로 계속 진행하지 말고 현재 원장을 확인한다.
- 실제 `OpenAI safety checks` 차단이 발생하면 오류 대상/원문을 보고하고 해당 회차의 저장을 중단한다. 정책 차단은 문구 바꾸기·경로 바꾸기 등으로 우회하지 않는다. 정상 GitHub 409 SHA 충돌만 최신 상태 조회 후 처리한다. 원인을 추정하거나 자동화가 정상이라고 꾸미지 않는다.
- 결과 파일이 실제 존재하지 않으면 분석 완료, canonical, pending_sync로 계산하지 않는다. artifact만 있고 event가 없을 때에만 `pending_sync`다.

## 종료 보고
- **첫 문장은 이번 회차에 실제로 GitHub에 저장한 신규 영상 수와 ID/제목**이다.
- 간략히 핵심 학습 내용, 근거 수준, 공식 검증 및 미확인 사항, 저장 성공/차단 여부, 로스터 롱폼 누적/703과 남은 영상, 다음 후보를 보고한다.
- 결과가 0편이면 왜 영상 분석 또는 저장이 불가능했는지 실제 오류 기준으로 밝힌다.
- 성공 여부는 *예약 트리거 실행*이 아니라 **출처 기반 영상 학습 결과가 저장됐는지**로 판단한다.

## 검증 출발점
2026-10-08 현재 로스터 기준 기존 등록은 216/703편, 실제 전체 canonical은 228편(로스터 밖 기존 12개 포함), 마지막 event 번호는 230이다. 이는 **초기 참고치**일 뿐, 모든 실행은 실제 ledger를 다시 계산한다. 전사 확보 실험은 `data/source_acquisition/youtube_read_pilot_20261008.json`에 있다. 후보는 `09R29vsv6to`, `eTOOtll0VPc`, `PW1EuMtw18o`, `2GjGjwkHrMA`, `fnLgP_KCv8A` 중 실제 미등록 ID부터 우선한다.
