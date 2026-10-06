# pensionport 운영 규칙

## Canonical source / 실행 시작 규칙
모든 예약·수동 실행은 **이전 채팅의 보고나 `state/progress.json` 요약만 믿고 이어서 작업하지 않는다.**
실행 시작 시 최신 `main`에서 아래를 fresh-fetch하고 실제 상태를 다시 계산한다.

- `WORKFLOW.md` — 유일한 운영규칙
- `LEARNING_QUEUE.md` — 사람이 읽는 요약
- `data/learning_queue.jsonl`
- `data/learning_queue_unresolved.jsonl`
- `data/videos.jsonl`
- `data/inventory_control.json`
- `data/channel_snapshot_2026-10-06.jsonl`
- `data/channel_snapshot_2026-10-06.meta.json`
- `data/canonical_events/`
- `state/progress.json`
- `state/execution_lock.json`
- 필요 시 최신 `state/run_events/`

### 현재 상태 재계산
실행 시작 후 반드시 actual data에서 다음을 다시 계산한다.
- queue total
- base canonical count / base max sequence
- canonical event overlay
- effective canonical count / effective max sequence
- pending_sync
- verification_needed
- source-backed unanalyzed ready
- unresolved
- next checkpoint

우선순위는 항상 **actual data + canonical-event overlay > progress summary > chat/report memory**다.
`state/progress.json`이 뒤처져 있어도 actual data를 덮어쓰거나 되돌리지 않는다.

## Baseline inventory event-first mode

2026-10-06 고정 채널 snapshot이 **effective 794/794**에 도달할 때까지 이 절이 일반 VIDEO-ANALYSIS-FIRST 규칙보다 우선한다.

### Baseline 완료 전 실행 모드
- 신규 콘텐츠 분석/canonicalization/source-acquisition 심층분석은 하지 않는다. 목표 분석 편수는 0이다.
- chronology repair는 목록화의 선행조건이 아니다. exact Video ID가 확실하면 title/date/duration 일부가 미확정이어도 inventory에 먼저 보존한다.
- 가능한 많은 unique exact Video ID를 배치로 수집한다.
- effective baseline inventory는 다음으로 계산한다.
  - compacted base: `data/channel_snapshot_2026-10-06.jsonl`
  - overlay: `data/inventory_events/<video_id>.json` 중 base에 같은 Video ID가 없는 event
- snapshot meta/progress의 저장된 숫자보다 위 effective 계산을 우선한다.

### Append-only inventory event
- 디렉터리: `data/inventory_events/`
- 파일명: `<video_id>.json`
- exact Video ID 하나당 immutable event 하나만 허용한다.
- event 최소 필드:
  - `schema_version`
  - `event_type=baseline_inventory_discovery`
  - `snapshot_as_of=2026-10-06`
  - `video_id`
  - `title`
  - `published_at`
  - `duration`
  - `content_type`
  - `learning_scope`
  - `source`
  - `discovered_at`
- create 전 compacted snapshot과 inventory event directory에서 같은 Video ID 존재 여부를 확인한다.
- 같은 path가 이미 존재하면 desired state가 already-applied된 것으로 처리하고 중복 생성하지 않는다.

### Lock 예외와 compaction
- `data/inventory_events/<video_id>.json`의 deterministic append-only `create_file`은 shared mutable file을 수정하지 않으므로 **single-writer lease 없이 허용**한다.
- `state/run_events/<unique_run_id>.json` append-only create도 동일하게 lease 없이 허용한다.
- 반면 `data/channel_snapshot_2026-10-06.jsonl`, meta, learning queue, inventory_control, progress 등 **공유 mutable aggregate 수정은 기존 single-writer lease가 필수**다.
- execution lock 획득/갱신이 상위 safety check로 차단되어도 inventory discovery와 inventory-event create를 중단하지 않는다.
- lock write는 fresh-refetch 후 1회만 재시도하고, 다시 차단되면 그 실행에서는 aggregate compaction을 건너뛴다. 같은 lock write를 반복 호출하지 않는다.
- event create 성공은 inventory progress 성공이다. aggregate compaction 실패/보류는 `compaction_pending`일 뿐 discovery failure가 아니다.
- 이후 lease를 정상 획득한 실행이 inventory events를 snapshot/queue/meta/progress에 idempotent하게 compact한다.

### 완료 전환
- effective baseline inventory가 794/794에 도달하면 모든 event overlay를 포함해 중복/분류를 검증한다.
- 가능한 경우 lease를 획득해 aggregate를 compact하고 `baseline_complete=true`를 기록한다.
- aggregate write가 일시적으로 막혀도 effective 794/794가 검증되면 추가 discovery는 중단하고 compaction만 남긴다.
- baseline 완료 후 다음 실행부터 일반 content-analysis lane을 재개한다.

## 단일 writer 실행 lease
여러 채팅과 예약작업이 같은 `main`의 공유 mutable aggregate를 동시에 수정하지 않도록 해당 write 전에 `state/execution_lock.json` lease를 획득한다. 단, 위 Baseline inventory event-first mode의 deterministic append-only inventory event와 unique run event create는 명시적 예외다.

### 획득
1. `state/execution_lock.json`을 fresh-fetch한다.
2. `status=active`이고 `lease_until`이 현재시각 이후면 다른 실행이 writer다. 이 실행은 **canonical write를 하지 않는다**.
3. lock이 released/expired이면 fresh SHA를 사용해 다음 값으로 update한다.
   - `status=active`
   - 고유 `run_id`
   - `source=scheduled|manual`
   - `started_at`
   - `lease_until=started_at+45분`
4. update가 SHA conflict 등으로 실패하면 즉시 refetch한다. 다른 run이 active lease를 획득했다면 그 run에 양보한다.

### 보유 중 규칙
- lease 보유 run만 canonical event, aggregate, knowledge, progress write를 수행한다.
- read-only 상태 확인과 discovery 검색은 다른 채팅도 가능하지만 write는 금지한다.
- 30분 이상 실행이 계속되면 필요 시 fresh-SHA로 lease를 갱신한다.

### 해제
- 정상 종료 시 fresh-fetch 후 자신의 `run_id`가 holder인지 확인하고 `status=released`로 갱신한다.
- 비정상 종료로 lock이 남아도 45분 후 자동 expired로 간주한다.
- 다른 run의 active lease를 강제로 해제하지 않는다.

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



## 선행 inventory reservoir — 분석 대상을 미리 목록화
분석 실행 때마다 영상을 새로 찾는 just-in-time discovery를 기본 운영으로 사용하지 않는다.
`data/learning_queue.jsonl`을 **미리 구축된 전체 학습 inventory**로 유지하고, `data/inventory_control.json`의 reservoir 기준을 따른다.

### 목표
- exact Video ID가 확인된 미처리 롱폼 버퍼 목표: **100편**
- 최소 안전 버퍼: **60편**
- 한 inventory discovery pass에서 신규 exact ID 목표: 최대 **40편**
- source acquisition pass 목표: 최대 **20편**

### 실행 시작 시 buffer 계산
`exact_id_unprocessed_buffer = learning_queue의 exact video_id 보유 항목 중 effective canonical에 없는 수`

상태를 다음으로 분리한다.
- `source_backed_ready`: 원문/자막/상세 보존자료가 있어 즉시 실제 분석 가능
- `source_acquisition_needed`: exact Video ID는 확보했지만 분석 가능한 source를 아직 수집하지 못함
- `verification_needed`: 충분한 source 탐색을 이미 수행했으나 확보 실패; retry 조건 전 반복검색 금지
- `processed`: effective canonical에 포함
- `video_id_unresolved`: 제목 등 후보만 있고 exact ID 미확정

### reservoir 유지 규칙
1. buffer가 **60편 미만**이면 content 분석과 별개로 inventory bootstrap을 최우선 선행 작업으로 수행해 exact ID를 대량 확보한다.
2. 한 번에 1개를 찾고 분석하는 방식이 아니라, 가능한 공개 색인/공식 링크/시리즈 목록에서 **최대 40개 exact ID를 먼저 묶어서 등록**한다.
3. 새 exact ID는 full source가 없어도 `source_acquisition_needed`로 master inventory에 먼저 등록할 수 있다. 제목은 검증되지 않았으면 null 또는 unverified로 둔다.
4. source acquisition은 inventory에 등록된 후보를 대상으로 별도 배치 수행한다. source 확보가 되면 `source_backed_ready`로 승격한다.
5. buffer가 **60~99편**이면 source-backed 분석을 진행하면서 실행 말미에 inventory를 보충한다.
6. buffer가 **100편 이상**이면 일반 content lane을 우선하고 신규 inventory discovery는 정기 보충 수준으로 낮춘다.
7. inventory bootstrap은 두 개의 독립된 focused discovery pass에서 신규 exact ID가 더 나오지 않거나 목표 buffer를 달성할 때까지 이어간다.

### discovery source 우선순위
- 공식 YouTube 채널의 롱폼/playlist/연결 가능한 공개 surface
- 공식 Shorts가 연결하는 원본 full-video exact ID
- exact YouTube 링크를 포함한 공개 강의·커리큘럼·색인 페이지
- 영상 게시 당시의 공개 요약/리뷰/임베드 페이지
- 검색엔진에서 확인되는 exact watch/youtu.be 링크

### 분석과 inventory의 분리
- inventory 등록은 **학습 완료가 아니다**.
- exact ID만 확보한 항목은 제목이나 검색 snippet만으로 분석하지 않는다.
- 예약작업은 매번 “무슨 영상을 찾을까”부터 시작하지 않고, 먼저 구축된 `source_backed_ready` 목록에서 분석한다.
- ready가 줄어들면 `source_acquisition_needed`를 배치 source 확보하고, 그와 별도로 exact-ID reservoir를 보충한다.


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


## 실행이력 / heartbeat
- **모든 예약·수동 writer 실행은 종료 시 unique `state/run_events/<timestamp>_<run_id>.json`을 append-only로 남긴다.** 성공 실행도 예외가 아니다.
- run event 최소 필드:
  - `run_id`
  - `source=scheduled|manual`
  - `started_at`, `finished_at`
  - `start_effective_canonical`, `end_effective_canonical`
  - `newly_analyzed_count`
  - `sync_only_count`
  - `pending_sync_count`
  - `verification_needed_count`
  - `discovery_checked_at`
  - `last_run_result`
  - `write_failure`
  - `heartbeat_location`
- `state/progress.json`은 최신 canonical snapshot/summary이며 실행이력 원장이 아니다.
- `state/run_events/`가 실제 실행이력 원장이다.
- `state/run-heartbeat.json`은 **legacy fallback**이다. 신규 실행의 최신상태 판정에는 사용하지 않는다.
- progress heartbeat write가 실패해도 run event를 남기고 콘텐츠/discovery를 중단하지 않는다.


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

1. **START SNAPSHOT** — 최신 main의 canonical source 전체, `data/inventory_control.json`, execution lock을 fresh-fetch하고, actual data + canonical-event overlay에서 queue total / effective processed / pending_sync / verification_needed / source_acquisition_needed / ready source-backed / exact-ID unprocessed buffer / base count·max sequence / effective max sequence / unresolved를 재계산한다. progress/chat summary와 다르면 actual data를 우선한다.
2. **INVENTORY/CONTENT LANE** — exact-ID unprocessed buffer가 60 미만이면 먼저 inventory bootstrap으로 최대 40개 exact ID를 선등록한다. 그 다음 source-backed 미분석을 최대 40편 분석한다. pending_sync 재분석 금지. verification_needed는 due date 전 재검색 금지. source_acquisition_needed는 최대 20편씩 source 확보를 배치 시도한다.
3. **SYNC LANE** — pending_sync는 desired state를 먼저 정의하고, 각 target을 `fresh fetch(ref=main) → idempotent merge → already-applied check → update(branch=main, fresh SHA) → optional post-fetch verify` 순서로 한 path씩 직렬 처리한다.
4. **ERROR LANE** — raw tool 오류의 class/status/message를 보존한다. raw 오류에 없는 이름을 붙이지 않는다. 특히 실제 오류에 safety precondition 문구가 없으면 그렇게 보고하지 않는다. stale SHA는 GitHub `409 CONFLICT` 장애군으로만 분류한다.
5. **RETRY LANE** — 오류 직후 fresh fetch하여 desired state가 이미 반영됐는지 먼저 확인한다. 반영됐으면 성공 처리한다. 미반영이면 최신 content에 재merge 후 1회만 retry한다.
6. **CONSISTENCY LANE** — 종료 전 queue와 data/videos를 다시 읽어 processed / pending_sync / verification_needed / max sequence를 재계산하고, 이미 존재하는 Video ID·sequence·claim·knowledge section은 절대 중복 append하지 않는다.
7. **HEARTBEAT LANE** — 종료 직전 progress를 fresh fetch → merge → update하고, 성공/실패와 무관하게 unique run event를 append-only로 남긴다. legacy run-heartbeat는 신규 실행의 최신상태 판정에 사용하지 않는다.

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


## 순서 불명확 시 전체 미확인 영상 스캔 fallback

chronology가 불완전하거나 게시일만으로 다음 영상을 안정적으로 정렬할 수 없는 경우에도 content lane을 정지하지 않는다.

### 후보 집합 계산
1. master queue와 신규 discovery에서 exact Video ID가 확인된 롱폼 전체 집합을 만든다.
2. effective canonical(base `data/videos.jsonl` + base에 없는 canonical event overlay)에 이미 존재하는 Video ID는 제외한다.
3. `content_analyzed_pending_sync` 등 분석 완료 상태는 content 후보에서 제외하고 sync lane으로만 보낸다.
4. `verification_needed`이면서 `next_source_retry_at` 전인 항목은 제외한다.
5. 남은 source-backed 분석 미완료 영상을 게시일 유무와 관계없이 실제 분석 후보로 사용한다.

### 선택 규칙
- 게시일이 신뢰 가능하면 오래된 순서를 선호한다.
- 게시일이 없거나 chronology가 충돌하면 `inventory_no`, 그 다음 `video_id`를 결정론적 tie-breaker로 사용한다.
- chronology 보강은 콘텐츠 분석의 선행조건이 아니다.
- 기존 queue가 비면 공개 채널의 롱폼 exact-ID 집합과 `queue ∪ effective canonical`을 대조하여 inventory 누락 영상을 찾고, source-backed 후보는 즉시 queue 등록 후 분석한다.

### stale-state 방지
- queue에 `source_backed_ready`가 남아 있어도 같은 Video ID가 effective canonical에 존재하면 ready로 세지 않는다.
- 이 경우 재분석하지 않고 aggregate compaction 대상으로만 처리한다.
- `ready_existing_queue_count`는 raw status count가 아니라 위 필터를 적용한 effective candidate count로 계산한다.


## 2026-10-06 고정 채널 snapshot
2026-10-06을 기준일로 박곰희TV 공개 업로드 전체를 고정 snapshot으로 먼저 완성한다.

- channel_id: `UCr7XsrSrvAn_WcU4kF99bbQ`
- 기준일 공개 업로드 총수 target: **794개**
- snapshot: `data/channel_snapshot_2026-10-06.jsonl`
- metadata: `data/channel_snapshot_2026-10-06.meta.json`
- 총수 794에는 Shorts 및 기타 공개 업로드 유형이 포함될 수 있으므로 각 행을 `long_form / short / live / other / unknown`으로 분류한다.
- 학습 대상 `data/learning_queue.jsonl`은 snapshot의 long-form/include 행에서 파생한다.
- snapshot 기준일 이후 업로드는 2026-10-06 baseline을 수정하지 않고 증분으로 추가한다.

### snapshot bootstrap 우선순위
1. 기준일 snapshot이 794/794로 완성되기 전에는 just-in-time 단건 discovery보다 **전체목록 수집을 우선**한다.
2. 한 pass에서 가능한 많은 exact Video ID / title / published_at / duration / type을 수집한다.
3. 동일 Video ID는 하나의 snapshot row만 가진다.
4. Shorts/라이브/광고 등도 전체 snapshot에는 남기되 학습 포함 여부를 별도 필드로 구분한다.
5. long-form으로 분류된 미처리 영상은 master learning queue에 idempotent하게 파생·등록한다.
6. snapshot 완성 후 예약작업은 기본적으로 미분석 long-form 목록을 소비하며, 별도 discovery는 **기준일 이후 신규 업로드 탐지**에만 사용한다.
7. 외부 색인 총수와 snapshot row 수가 다르면 snapshot 미완성으로 간주한다. 총수만 맞추기 위해 ID 없는 placeholder를 만들지 않는다.
