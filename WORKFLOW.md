# pensionport 운영 규칙

## Canonical source
실행 시작 시 아래 파일만 빠르게 읽어 충돌을 확인한다.
- `WORKFLOW.md`
- `LEARNING_QUEUE.md`
- `data/learning_queue.jsonl`
- `data/learning_queue_unresolved.jsonl`
- `data/videos.jsonl`
- `state/progress.json`

## 최우선 목표
최우선 목표는 **실제 영상 콘텐츠 분석 처리량**이다.
운영 모드는 `VIDEO-ANALYSIS-FIRST + INVENTORY-FIRST`이며, INVENTORY-FIRST는 분석 가능한 영상이 있는데 inventory 정비를 우선하라는 뜻이 아니다.

Video ID가 확인된 `identified_unprocessed` 롱폼 중 신뢰 가능한 원문·자막·상세 보존자료를 확보할 수 있는 영상이 있으면 즉시 콘텐츠 분석을 시작한다.
날짜 보강, chronology repair, 전수 inventory 대조, unresolved ID 해결은 분석 가능한 큐가 있는 동안 후순위다.

## 독립 상태머신 — 분석과 동기화를 분리
콘텐츠 분석과 GitHub canonical 동기화를 서로 독립적인 작업 lane으로 운영한다.

### A. content_analysis_lane
- 실제 신규 콘텐츠 분석만 담당한다.
- 예약 실행당 목표는 **최대 40편**이다.
- GitHub 저장 실패, synthesis 저장 실패, inventory 요약 불일치 때문에 이 lane을 정지하지 않는다.
- 저장 실패 영상은 `pending_sync`로 보내고 즉시 다음 분석 가능한 영상으로 이동한다.

### B. canonical_sync_lane
- 이미 분석문이 존재하는 영상의 index/queue/claims/knowledge/framework/progress 동기화만 담당한다.
- `videos/pending/<video_id>.md`가 있고 내용분석이 완료된 영상은 **재분석하지 않는다**.
- 이 영상은 신규 분석 처리량에 포함하지 않고 sync backlog로만 관리한다.
- 동일 파일 쓰기는 반드시 최신 SHA를 다시 읽은 뒤 직렬로 수행한다.
- 한 파일의 write가 실패하면 `pending_sync`로 남기고 다른 파일 또는 content lane으로 진행한다.

## 영상 선택 우선순위
매 실행에서 다음 순서로 선택한다.

1. `identified_unprocessed` + source-backed + 실제 콘텐츠 분석 미완료
2. 이미 분석문이 있는 `pending_sync`는 재분석하지 않고 짧게 sync 시도
3. `verification_needed`는 재검색 조건이 충족되지 않으면 즉시 skip
4. 위 1번 후보가 없으면 **즉시 신규 롱폼 discovery**로 master queue를 확장하고, source-backed 신규 영상을 찾아 분석을 계속한다.

오래된 순서를 선호하되, source 확보 실패 때문에 전진을 멈추지 않는다.

## source 미확보 / verification_needed 재시도 규칙
신뢰 가능한 원문·자막·상세 보존자료가 없는 영상은 제목만으로 세부 내용을 만들지 않는다.

한 번 충분히 검색했는데 source를 확보하지 못한 영상은:
- `analysis_status=verification_needed`
- `blocked_reason=source_unavailable`
- `last_source_check_at`
- `next_source_retry_at`
을 기록한다.

동일 영상은 매 실행마다 재검색하지 않는다.
재검색은 아래 중 하나일 때만 수행한다.
- `next_source_retry_at` 도달
- 새로운 source 신호가 발견됨
- 사용자가 직접 원문/링크/자료를 제공
- 기존 source 접근성이 달라졌다는 명시적 근거가 있음

기본 재시도 간격은 **30일**이다. 재시도 전에는 즉시 skip하고 다음 영상으로 간다.

## 신규 discovery 규칙
분석 가능한 기존 큐가 소진되었거나 남은 항목이 모두 `verification_needed` / `pending_sync`이면 그 실행을 0편으로 끝내지 말고 신규 롱폼 discovery를 수행한다.

- 박곰희TV(@gomhee)의 새로운/누락 롱폼 Video ID를 찾는다.
- Shorts는 제외한다.
- 광고·인터뷰·몰아보기·교육시리즈 등 롱폼은 포함하고 tag로 구분한다.
- 신규 영상은 분석 전에 master queue에 등록한다.
- Video ID 중복, Shorts 여부, 게시일, 기존 처리 여부를 확인한다.
- source-backed 신규 영상이 확보되면 즉시 분석한다.

신규 discovery가 한 번의 실행 패스에서도 source-backed 후보를 만들지 못한 경우에만, tool/time 한도와 함께 0편 종료가 허용된다.

## 고속 배치 학습
- 기본 작업 단위는 **최대 40편**이다.
- 신뢰 가능한 원문/자막/보존자료가 계속 확보되는 한 1~5편에서 임의 종료하지 않는다.
- 같은 유형의 검색·검증·GitHub 저장은 가능한 범위에서 배치화한다.
- 속도 향상은 필수 분석항목 생략으로 얻지 않는다.
- blocked item은 즉시 skip한다.
- sync-only 작업은 신규 분석 편수에 포함하지 않는다.

## 영상별 필수 추출 — 생략 금지
각 영상마다 다음을 확인한다.
- 핵심 주장과 결론
- 주장의 논리, 전제, 적용 조건
- 숫자·한도·세율·기간·수익률·비용 등 정량 정보
- 투자·연금 전략과 실행 절차
- 중요한 예외·위험·주의사항
- 기존 영상과의 중복·확장·변경·충돌
- 과거 주장 대비 관점 변화
- 시간의존 정보
- 공식자료 검증 필요성
- 전체 박곰희 프레임워크에 새로 추가되거나 강화되는 지식
- 출처 수준과 미확인 사항

## 지식 분류
영상별 결과를 하나 이상으로 분류한다.
- `NEW`
- `REINFORCE`
- `EXTEND`
- `CHANGE`
- `CONFLICT`
- `TIME_SENSITIVE`

## 선택적 심층검증
다음 항목만 최신 권위 있는 공식자료로 심층검증한다.
- 연금저축·IRP·ISA·국민연금
- 세금·세액공제·과세·신고
- 법령·금융규제·거래소 제도
- 현재 한도·세율·수수료·거래시간 등 변경 가능 수치
- 기존 지식과 충돌
- 전체 프레임워크 변경

일반적인 영구 투자원칙과 이미 검증된 반복내용은 외부검증을 반복하지 않는다.

## 저장
분석 결과는 순차/배치로 다음에 반영한다.
- 개별 영상 문서
- `data/videos.jsonl`
- `data/learning_queue.jsonl`
- claims
- 관련 `knowledge/*.md`
- `knowledge/gomhee-framework.md`
- `state/progress.json`

GitHub 저장 실패는 해당 영상의 canonical 완료 판정을 막지만 **다음 영상 콘텐츠 분석을 막아서는 안 된다**.
실패는 `pending_sync`로 남긴다.

## 10편 체크포인트
누적 canonical 처리수가 10의 배수에 도달하면 그 영상 반영 직후 누적지식을 재종합한다.
- 반복원칙·예외·변화·충돌
- 연금저축·IRP·ISA·국민연금·세금·인출·자산배분
- 전체 박곰희 프레임워크
- 해당 10편 구간 변화와 누적결론 한국어 PDF

synthesis/framework/state의 GitHub 저장이 실패하면 산출물은 `pending_sync`로 기록하되 콘텐츠 분석 lane 전체를 중단하지 않는다.

## 실행 종료 조건
다음 중 하나일 때만 종료한다.
- 실행시간/도구 한도 도달
- 기존 큐의 source-backed 분석 후보를 소진했고 신규 discovery 1패스에서도 source-backed 후보를 확보하지 못함

다음 사유만으로는 종료하지 않는다.
- GitHub write 실패
- 특정 영상 source 미확보
- chronology 미정
- inventory 요약 불일치
- unresolved ID 존재

## 종료보고
첫 항목은 반드시 실제 신규 분석 영상 수와 Video ID/제목 범위다.
그 다음:
1. 중요 새 지식/변경/충돌
2. 공식검증
3. 저장/동기화 상태
4. canonical 누적 처리수
5. 다음 체크포인트
6. 마스터 큐 잔여 미처리수

## 품질 원칙
- 속도를 위해 내용을 추측하거나 근거 없는 세부사항을 채우지 않는다.
- 원문이 없으면 세부 발언과 숫자를 재구성하지 않는다.
- 과거의 세율·한도·상품조건·시장규칙은 현재값으로 간주하지 않는다.
- 중요 정보 누락 방지가 처리량보다 우선이다.


## source identity 안전 규칙
- Video ID와 transcript/보존자료의 identity가 일치하지 않으면 canonical 승격을 금지한다.
- `status: invalid_source_identity` 또는 `canonical_use: prohibited` 문서는 분석 완료, pending_sync, processed 수에 포함하지 않는다.
- 이런 tombstone 파일은 삭제 여부와 관계없이 실행 큐에서 항상 제외한다.
- replacement Video ID가 확인되면 replacement만 master queue에 등록하고, source-matched 상세자료가 없으면 `verification_needed`로 둔다.


## 예약 실행 heartbeat
- 매 예약 실행 종료 시 `state/progress.json`에 실행 heartbeat를 기록한다.
- 최소 필드: `last_scheduled_run_at`, `last_run_result`, `discovery_checked_at`, `newly_analyzed_count`, `write_failure`.
- `state/progress.json` heartbeat write가 안전검사 또는 다른 write 오류로 막히면 즉시 `state/run-heartbeat.json`에 동일 정보를 기록한다.
- `state/run-heartbeat.json`은 실행 추적용 fallback이며 canonical processed count의 기준으로 사용하지 않는다.
- 두 heartbeat 경로가 모두 실패한 경우에만 user-visible 종료보고에 heartbeat 저장 실패를 명시한다.
- heartbeat 실패 때문에 콘텐츠 분석 또는 discovery를 중단하지 않는다.
