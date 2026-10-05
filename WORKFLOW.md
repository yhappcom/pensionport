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


## GitHub write 안전 프로토콜
이 절은 모든 canonical write와 heartbeat write에 강제 적용한다.

- 실행 시작 시 읽은 canonical 파일의 SHA는 **충돌 확인용 snapshot**일 뿐, 실행 말미 write의 SHA로 재사용하지 않는다.
- 기존 파일을 수정하기 직전에 반드시 그 **정확한 target path를 다시 fetch**하고, 그 fetch가 반환한 최신 blob SHA로 `update_file`을 수행한다.
- 같은 파일을 한 실행에서 두 번 이상 수정할 때는 직전 성공 write가 반환한 새 content SHA를 다음 write에 사용하거나 다시 fetch한다. 오래된 SHA를 재사용하지 않는다.
- 같은 path에 대한 write/delete는 절대 병렬 실행하지 않는다. canonical write는 path 단위로 직렬화한다.
- SHA mismatch, 409/422 conflict, stale-file/safety precondition 계열 오류가 발생하면 실패로 확정하기 전에 target file을 즉시 다시 fetch하고, 최신 내용에 의도한 변경을 재적용하여 **1회 자동 재시도**한다.
- 위 재시도도 실패한 경우에만 해당 항목을 `pending_sync` 또는 write failure로 기록하고 다음 콘텐츠/다른 파일로 진행한다.
- `state/progress.json` heartbeat도 종료 직전에 반드시 fresh fetch → merge → update 순서로 쓴다. 실행 시작 시 읽은 progress SHA를 사용하지 않는다.
- primary heartbeat가 실패해 `state/run-heartbeat.json`으로 fallback할 때도 fallback 파일을 먼저 fresh fetch하고 최신 SHA로 쓴다.
- 오류 보고에는 막연히 “안전검사 실패”라고 쓰지 말고, **target path / 오류 클래스(SHA conflict, permission, connector precondition 등) / fresh-refetch retry 결과**를 기록한다.
- 다른 파일의 성공 commit 때문에 기존 파일의 blob SHA가 자동으로 바뀌는 것은 아니지만, 수동 실행·예약 실행·동일 파일의 선행 write가 겹칠 수 있으므로 write 시점 fresh fetch를 항상 기준으로 삼는다.


## GitHub connector 실행 트랜잭션 규칙

fresh-SHA 규칙에 더해 다음을 적용한다.

- 기존 파일 write는 가능하면 한 실행 트랜잭션 안에서 `fetch_file(target, ref=main) → 최신 content에 의도 변경 merge → update_file(target, sha=fetched_sha, branch=main)` 순서로 직렬 실행한다.
- 여러 target을 수정할 때도 각 path마다 위 read-modify-write를 독립적으로 완료한 뒤 다음 path로 이동한다.
- 실패 직후 재시도하기 전에 target을 fresh fetch하고 **의도한 desired state가 이미 반영됐는지 먼저 확인**한다. 이미 반영됐다면 추가 write 없이 성공으로 판정한다.
- partial sync 복구 시 `data/videos.jsonl`, queue, claims, knowledge, framework, progress 각각을 실제 현재 내용으로 idempotency 검사한다. 이미 존재하는 video/claim/section을 중복 append하지 않는다.
- 오류는 connector 요약문으로 재명명하지 않는다. 가능한 경우 raw tool 오류의 클래스와 HTTP 상태(예: `CONFLICT / 409`, `UNPROCESSABLE_ENTITY / 422`, `FORBIDDEN / 403`) 및 원문 메시지를 기록한다.
- raw tool 결과에 실제로 `safety precondition`이 없으면 단순히 “connector safety precondition”이라고 보고하지 않는다.
- stale SHA와 connector/orchestration precondition은 별도 장애군으로 취급한다. stale SHA는 GitHub Contents API의 409로 재현 가능하며 fresh-refetch 후 정상 복구되는 것이 기준이다.
- write 장애 진단 시 임시 진단 파일을 사용할 수 있으나 테스트 후 삭제하고, 실제 canonical target 한 곳에서도 동일 프로토콜이 통과하는지 확인한다.


## 낮은 추론 수준 대응 — 결정론적 예약 실행

예약 실행은 모델 추론 수준에 의존하지 않도록 다음 상태머신을 고정한다.

1. **START SNAPSHOT** — canonical 6개 파일을 읽고 실제 data 파일에서 queue total / processed / pending_sync / verification_needed / ready source-backed / data-videos count·max sequence / unresolved를 재계산한다. 요약 문서의 숫자와 다르면 data 파일을 우선한다.
2. **CONTENT LANE** — source-backed 미분석 → 최대 40편 분석. pending_sync 재분석 금지. verification_needed는 due date 전 재검색 금지. ready=0이면 신규/누락 롱폼 discovery 1패스 필수.
3. **SYNC LANE** — pending_sync는 desired state를 먼저 정의하고, 각 target을 `fresh fetch(ref=main) → idempotent merge → already-applied check → update(branch=main, fresh SHA) → optional post-fetch verify` 순서로 한 path씩 직렬 처리한다.
4. **ERROR LANE** — raw tool 오류의 class/status/message를 보존한다. raw 오류에 없는 이름을 붙이지 않는다. 특히 실제 오류에 safety precondition 문구가 없으면 그렇게 보고하지 않는다. stale SHA는 GitHub `409 CONFLICT` 장애군으로만 분류한다.
5. **RETRY LANE** — 오류 직후 fresh fetch하여 desired state가 이미 반영됐는지 먼저 확인한다. 반영됐으면 성공 처리한다. 미반영이면 최신 content에 재merge 후 1회만 retry한다.
6. **CONSISTENCY LANE** — 종료 전 queue와 data/videos를 다시 읽어 processed / pending_sync / verification_needed / max sequence를 재계산하고, 이미 존재하는 Video ID·sequence·claim·knowledge section은 절대 중복 append하지 않는다.
7. **HEARTBEAT LANE** — 종료 직전 progress를 fresh fetch → merge → update한다. 실패하면 동일 검증·1회 retry 후 fallback heartbeat를 fresh fetch하여 기록한다.

### 결정 규칙
- 기존 summary 숫자를 기반으로 +1/-1 계산하지 않는다. 종료 전 actual data 파일에서 다시 계산한다.
- partial sync 복구는 각 target의 현재 desired state를 검사해 idempotent하게 이어서 처리한다.
- 한 target write 실패 때문에 다른 target이나 content lane을 중단하지 않는다.
- 원인이 증명되지 않은 오류는 `원인 미확정`으로 기록하고 추정명을 붙이지 않는다.
- 실행 보고의 write 오류는 `path / raw class / HTTP status(있으면) / message 요약 / desired-state check / retry 결과` 형식을 사용한다.


## Write 실패 증거 규칙

예약 실행에서 GitHub write 실패를 판정할 때 다음을 강제한다.

- **실제 GitHub write connector가 호출되고 raw error를 반환한 경우에만 write 실패로 기록한다.**
- raw connector error가 없으면 `safety check`, `connector precondition`, `permission`, `SHA conflict` 같은 원인을 추정하지 않는다. 이 경우 상태는 `write_status_unknown`으로 기록하고 실패로 단정하지 않는다.
- 사용자 보고에 오류를 쓰려면 최소한 `target path / invoked write action / raw error class 또는 raw message / fresh-refetch 결과 / retry 결과`가 있어야 한다.
- 단순히 모델이 “도구가 막혔다”고 판단한 문장, 계획 단계의 중단, tool-call 미발행은 write 실패 증거가 아니다.
- 예약 실행에서 한 write가 의심스러우면 같은 실행 안에서 exact target을 다시 fetch하고 desired state를 확인한다. desired state가 반영되어 있으면 성공이다.
- desired state가 없고 raw connector error도 없다면 해당 target을 한 번 더 **직접 GitHub update action으로 호출**한다. 이 두 번째 직접 호출의 raw 결과로만 성공/실패를 결정한다.
- 반복 실패를 보고하기 전에 최소 한 개의 작은 known-safe target 또는 heartbeat target에서 동일한 direct write transaction이 동작하는지 확인한다. 이것은 repository-wide 장애와 target-specific 장애를 구분하기 위한 진단이다.


## 예약 실행 write blocker 우회 — event-first canonical ledger

예약 실행에서 기존 파일 `update_file`이 상위 safety layer에 의해 간헐적으로 차단될 수 있으므로 canonical 저장은 event-first로 운영한다.

### Canonical event
- 디렉터리: `data/canonical_events/`
- 파일명: `NNN_<video_id>.json`
- 각 영상은 canonical sequence당 정확히 하나의 immutable event만 가진다.
- event는 aggregate 파일보다 **먼저** `create_file`로 저장한다.
- event에는 sequence, video_id, title, published_at, source_doc, queue_effect, claim_delta, framework_delta, created_at을 기록한다.
- 동일 sequence 또는 동일 video_id event가 이미 있으면 새 event를 만들지 않는다.

### Effective canonical state
- effective canonical = `data/videos.jsonl`의 compacted base + `data/canonical_events/` 중 base에 아직 같은 video_id가 없는 event overlay.
- processed/pending_sync/next sequence 계산은 physical base만 보지 말고 effective canonical state로 계산한다.
- event가 존재하면 aggregate compaction이 실패해도 그 영상은 canonical 처리 완료로 간주한다.
- base aggregate에 같은 video_id가 나중에 들어가면 해당 event는 audit evidence로만 남고 중복 계산하지 않는다.

### Opportunistic compaction
event 저장 후 기존 aggregate를 순서대로 idempotent compaction한다.
1. `data/videos.jsonl`
2. `data/learning_queue.jsonl`
3. `data/claims.jsonl`
4. 관련 `knowledge/*.md`
5. `knowledge/gomhee-framework.md`
6. `LEARNING_QUEUE.md`
7. `state/progress.json`

- compaction update가 성공하면 base와 event가 일치한다.
- update가 raw error로 실패하면 event를 유지하고 다음 영상/작업으로 진행한다.
- 다음 예약 실행은 event overlay를 먼저 읽으므로 이미 canonicalized된 영상을 다시 sync 대상으로 선택하지 않는다.
- aggregate compaction 실패는 canonical event 생성 성공 이후에는 콘텐츠 진행 blocker가 아니다.

### Run heartbeat event
- 기존 `state/progress.json`/fallback update가 막히면 unique `state/run_events/<timestamp>.json`을 `create_file`로 기록한다.
- run event는 실행 추적용이며 canonical video count는 base + canonical event overlay로 계산한다.
- 기존 heartbeat update가 성공하더라도 run event를 남겨도 되며, 중복 상태 판정에는 사용하지 않는다.

### 실패 판정
- `create_file` canonical event까지 raw error로 실패한 경우에만 해당 영상 canonicalization을 미완료로 본다.
- aggregate `update_file`만 실패한 경우에는 `compaction_pending`이지 canonicalization failure가 아니다.
- 예약 실행 종료보고는 `canonical event 성공/실패`와 `aggregate compaction 성공/대기`를 분리해 보고한다.
