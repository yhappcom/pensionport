# pensionport 운영 규칙

## 2026-10-07 전수 roster 확정 — 최우선 운영 override

사용자가 제공하고 검증한 `VIDEO_INVENTORY_2026-10-07.md`를 박곰희TV 영상 목록의 **현재 canonical roster**로 사용한다.

- 전체 고유 Video ID: **791**
- 롱폼: **703**
- Shorts: **88**
- 이 roster는 2026-10-07 기준 전수 수집 결과이며, 기존의 **794개 baseline inventory discovery 목표를 폐기·대체**한다.
- 따라서 아래의 과거 `Baseline inventory event-first mode`가 요구하던 794/794 목록화 완료 조건은 더 이상 content analysis를 차단하지 않는다.
- 예약·수동 실행은 더 이상 794개를 맞추기 위한 신규 inventory discovery를 선행하지 않는다.
- 모든 실행은 시작 시 `VIDEO_INVENTORY_2026-10-07.md`와 actual canonical data를 fresh-fetch하여, roster 내 롱폼 중 아직 canonical 분석되지 않은 Video ID를 계산한 뒤 content analysis를 우선한다.
- Shorts는 roster에는 보존하지만 기본 content-analysis lane에서는 제외한다.
- `data/videos.jsonl` 또는 과거 canonical 자료에 roster 밖 legacy Video ID가 있더라도 분석을 중단하지 않는다. 이를 reconciliation backlog로 기록하고 roster 내 미처리 롱폼 분석을 계속한다.
- roster의 `수집 상태=미확인`은 주로 게시일 메타데이터 미확인을 뜻한다. exact Video ID가 존재하면 분석 후보에서 제거하지 않는다.
- source identity 규칙은 계속 적용한다. 신뢰 가능한 원문·자막·상세 보존자료가 없으면 세부 내용을 추측하지 않고 `verification_needed` 또는 source-acquisition 상태로 넘긴다.

이 override는 이 문서의 과거 baseline inventory/discovery 관련 규칙과 충돌할 경우 **우선한다**. 나머지 single-writer, source identity, canonical sync, 10편 checkpoint, 품질 규칙은 그대로 유지한다.

## 2026-10-07 ROSTER FAST PATH — ACTIVE

이 절은 791개 roster 확정 이후의 **현재 실행 경로**이며, 아래에 남아 있는 legacy inventory/reservoir/discovery 및 영상별 opportunistic compaction 규칙과 충돌하면 이 절이 무조건 우선한다.

### 분석 대상
- 후보 universe는 `VIDEO_INVENTORY_2026-10-07.md`의 **롱폼 703편**만 사용한다.
- `roster long_form - effective canonical - content_analyzed_pending_sync`를 실제 미분석 후보로 계산한다.
- 794 baseline, channel snapshot completeness, inventory reservoir, 신규 discovery는 roster 분석 실행을 차단하거나 선행하지 않는다.
- `state/progress.json`에 남은 794-baseline/reservoir/channel_snapshot 필드는 **legacy informational only**이며 실행 분기 입력으로 사용하지 않는다.
- Shorts 88편은 roster에는 보존하지만 기본 분석 대상에서 제외한다.
- roster 밖 legacy canonical ID는 reconciliation backlog로만 관리한다.

### 고속 배치 실행
1. **READ/ANALYZE PHASE — lock 없이 가능**
   - 최신 roster와 effective canonical을 읽고 최대 40편 후보를 고른다.
   - source-backed 후보를 계속 분석한다. source 미확보 항목은 즉시 skip하고 다음 후보로 이동한다.
   - GitHub 저장 실패 여부와 무관하게 가능한 콘텐츠 분석을 먼저 끝낸다.
2. **WRITE PHASE — lock 1회**
   - 저장 직전에 single-writer lease를 한 번 획득한다.
   - effective canonical과 max sequence를 fresh-fetch해 이미 다른 run이 canonicalized한 ID는 제외한다.
   - 남은 분석 결과에 연속 sequence를 배정한다.
3. **영상별 최소 영속화**
   - 기본: concise canonical analysis 문서 1개 → immutable canonical event 1개.
   - canonical 문서는 분석 결론/근거/수치/위험/지식관계/source reference만 저장하고 **원문 transcript 전체를 저장하지 않는다**.
   - Markdown canonical 문서 create가 raw safety block으로 실패하면 fresh existence check 후 1회 retry한다.
   - retry도 실패하면 `data/analysis_events/<video_id>.json`에 같은 핵심 분석을 compact structured JSON으로 1회 fallback 저장할 수 있다.
   - fallback artifact가 성공하면 canonical event의 `source_doc`는 해당 JSON을 가리킬 수 있으며, 사람용 Markdown은 후속 materialization backlog로 둔다.
   - canonical event create 성공이 canonical 완료 기준이다.
4. **영상 사이 aggregate write 금지**
   - 한 영상 event가 성공할 때마다 `data/videos.jsonl`, queue, claims, knowledge, framework, progress를 갱신하지 않는다.
   - 영상 40편을 처리하는 동안 aggregate는 건드리지 않고 event ledger를 source of truth로 사용한다.
5. **BATCH COMPACTION — 실행 말미 최대 1회/path**
   - 콘텐츠/event 생성이 끝난 뒤 각 aggregate path를 실행당 최대 한 번만 fresh-fetch → idempotent merge → fresh-SHA update한다.
   - 순서: `data/videos.jsonl` → `data/learning_queue.jsonl` → `data/claims.jsonl`.
   - 관련 knowledge는 실행당 한 번 묶어서 반영한다.
   - `knowledge/gomhee-framework.md`와 synthesis/PDF는 effective canonical이 10의 배수를 새로 통과한 경우에만 처리한다.
   - `state/progress.json`은 종료 직전 한 번만 갱신한다.
   - aggregate update 실패는 `compaction_pending`이며 이미 성공한 canonical event를 되돌리지 않는다.
6. **RUN EVENT / RELEASE**
   - unique run event는 매 writer run 종료 시 1개만 남긴다.
   - 자신의 lease만 release한다.

### 처리량 보호 규칙
- 한 canonical document/event 또는 aggregate write가 실패해도 다음 source-backed 영상 분석을 계속한다.
- pending_sync는 재분석하지 않는다.
- aggregate compaction 실패를 이유로 실행을 조기 종료하지 않는다.
- 목표 40편은 source availability와 tool/execution 한도에 의해서만 줄어든다.
- 40편 기준 저장 write amplification을 줄이기 위해 aggregate를 영상별로 반복 rewrite하는 방식은 금지한다.

## Canonical source / 실행 시작 규칙
모든 예약·수동 실행은 **이전 채팅의 보고나 `state/progress.json` 요약만 믿고 이어서 작업하지 않는다.**
실행 시작 시 최신 `main`에서 아래를 fresh-fetch하고 실제 상태를 다시 계산한다.

- `WORKFLOW.md` — 유일한 운영규칙
- `VIDEO_INVENTORY_2026-10-07.md` — 2026-10-07 확정 전수 roster (791개 / 롱폼 703 / Shorts 88)
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

**[RETIRED 2026-10-07]** 이 절은 과거 794개 추정 baseline을 완성하기 위한 규칙이었다. `VIDEO_INVENTORY_2026-10-07.md` 791개 전수 roster 확정으로 완료·대체되었으며, 더 이상 content analysis를 차단하지 않는다. 아래 내용은 과거 실행기록/호환성 참고용이다.

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
- baseline 미완성의 **일반 discovery 실행은 execution lock을 획득하거나 갱신하지 않는다.** inventory event만 append하고 종료한다. 따라서 routine hourly discovery에서 `state/execution_lock.json` update를 호출하지 않는다.
- 반면 `data/channel_snapshot_2026-10-06.jsonl`, meta, learning queue, inventory_control, progress 등 **공유 mutable aggregate 수정은 기존 single-writer lease가 필수**다.
- aggregate compaction은 매 실행마다 하지 않고 다음 checkpoint에서만 시도한다: (a) compact되지 않은 inventory event가 50개 이상, (b) effective inventory가 794/794 도달, (c) 사용자가 명시적으로 compaction/정합성 정리를 요청.
- checkpoint compaction에서만 execution lock을 fresh-fetch하고 필요 시 획득한다. lock write가 상위 safety check로 차단되면 fresh-refetch 후 정확히 1회만 재시도하고, 다시 차단되면 compaction을 보류한다. 같은 실행에서 lock write를 더 반복하지 않는다.
- lock/compaction이 차단되어도 inventory discovery와 inventory-event create를 중단하지 않는다.
- event create 성공은 inventory progress 성공이다. aggregate compaction 실패/보류는 `compaction_pending`일 뿐 discovery failure가 아니다.
- 이후 lease를 정상 획득한 checkpoint 실행이 inventory events를 snapshot/queue/meta/progress에 idempotent하게 compact한다.

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
최우선 목표는 **791 roster 내 미분석 롱폼의 실제 콘텐츠 분석 처리량**이다.

- roster long-form 703편을 유일한 분석 universe로 사용한다.
- 794 baseline, inventory reservoir, 신규 inventory discovery는 운영 목표에서 제외한다.
- source-backed 후보가 있으면 최대 40편까지 분석하고, source 미확보 후보는 즉시 skip한다.
- 날짜 보강·legacy reconciliation·aggregate compaction은 콘텐츠 분석의 선행조건이 아니다.

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
매 실행에서 roster 롱폼 기준으로 다음 순서를 사용한다.

1. `roster long_form` 중 effective canonical에 없고 content analysis가 없는 source-backed 후보
2. 이미 분석문이 존재하는 `pending_sync`는 재분석하지 않고 write phase에서 sync-only 처리
3. source 미확보 후보는 source-acquisition/verification 상태로 넘기고 즉시 다음 roster 후보로 이동
4. 게시일 미확인 후보도 exact Video ID가 있으면 제외하지 않는다.
5. roster 밖 신규 discovery는 이 프로젝트의 기본 분석 실행에서 수행하지 않는다.

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
**[RETIRED 2026-10-07]** 791개 전수 roster 확정으로 신규 inventory discovery는 기본 분석 실행에서 사용하지 않는다. 향후 실제 2026-10-07 이후 신규 업로드를 별도 증분 roster에 추가할 때만 별도 작업으로 수행한다.

## 선행 inventory reservoir — 분석 대상을 미리 목록화
**[RETIRED 2026-10-07]** 과거 exact-ID reservoir 60/100 기준, inventory bootstrap, source inventory 보충 규칙은 791개 roster 확정으로 폐기되었다. 분석 후보 수 계산과 실행 분기에 사용하지 않는다.

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
예약 실행은 아래 6단계만 따른다.

1. **START** — roster, base canonical, canonical events, pending analysis artifacts, lock을 fresh-fetch하고 effective canonical 및 roster remaining을 재계산한다.
2. **ANALYZE** — roster long-form 미분석 후보에서 source-backed 영상을 최대 40편 분석한다. source 미확보는 skip한다. 이 단계에서는 aggregate를 쓰지 않는다.
3. **WRITE LOCK** — 저장할 분석 결과가 있을 때만 single-writer lease를 1회 획득한다. 획득 후 effective canonical/max sequence를 다시 읽어 중복을 제거한다.
4. **MINIMAL CANONICAL WRITE** — 영상별 concise analysis artifact와 immutable canonical event만 직렬 생성한다. 실패한 영상은 fallback structured analysis artifact를 1회 시도하고, 그래도 실패하면 pending_sync로 남기고 다음 영상을 계속한다.
5. **BATCH COMPACTION** — 모든 영상 event 처리가 끝난 뒤 aggregate path별 최대 1회만 compact한다. canonical event가 이미 성공한 영상은 aggregate 실패로 되돌리지 않는다.
6. **END** — checkpoint 필요 시 한 번 처리하고 progress 1회, unique run event 1회, 자신의 lease release 1회로 종료한다.

결정 규칙:
- 794 baseline/inventory reservoir/discovery 상태로 분기하지 않는다.
- 영상 사이 aggregate update를 하지 않는다.
- write 실패는 다음 영상 content analysis의 stop condition이 아니다.
- actual canonical + event overlay가 progress보다 우선한다.

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
canonical 저장은 event-first를 유지하되 **per-video aggregate compaction은 금지**한다.

### Canonical event
- `data/canonical_events/NNN_<video_id>.json`은 immutable canonical ledger다.
- 분석 artifact가 존재하고 event create가 성공하면 해당 영상은 canonical 완료다.
- 동일 video_id 또는 sequence event 중복 생성은 금지한다.

### Effective canonical state
- effective canonical = compacted `data/videos.jsonl` + base에 없는 canonical event overlay.
- sequence와 processed 계산은 항상 effective state에서 한다.

### Batch compaction
- event 생성들을 먼저 끝낸 뒤 실행 말미에 path별 최대 한 번만 compact한다.
- 기본 순서: `data/videos.jsonl` → `data/learning_queue.jsonl` → `data/claims.jsonl`.
- knowledge는 실행당 한 번 묶어서 반영하고 framework/synthesis/PDF는 10편 checkpoint에서만 갱신한다.
- aggregate update 실패는 `compaction_pending`이며 canonical event 성공을 취소하지 않는다.

### Run event
- writer run 종료 시 unique `state/run_events/<timestamp>_<run_id>.json` 1개를 append-only로 남긴다.
- progress update가 실패해도 run event를 남기고 canonical count는 event overlay에서 복원한다.

## 순서 불명확 시 전체 미확인 영상 스캔 fallback
roster에 exact Video ID가 이미 확정되어 있으므로 별도 전체 미확인 discovery scan을 하지 않는다.

- 게시일이 있으면 오래된 순서를 선호한다.
- 게시일이 없으면 roster 번호, 그 다음 video_id를 결정론적 tie-breaker로 사용한다.
- chronology 보강은 분석 선행조건이 아니다.
- effective canonical에 이미 있는 ID와 content-analyzed pending_sync ID는 후보에서 제외한다.

## 2026-10-06 고정 채널 snapshot
**[RETIRED 2026-10-07]** 과거 794개 추정 baseline snapshot 규칙은 `VIDEO_INVENTORY_2026-10-07.md`의 791개 확정 roster로 대체되었다. 이 절의 옛 target·bootstrap·completeness 값은 실행 제어에 사용하지 않는다.
