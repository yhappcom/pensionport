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

### 고속 배치 실행 — LOCK-FIRST / FROZEN AGGREGATE (2026-10-08)
이 절은 같은 문서에 남은 오래된 READ/ANALYZE-BEFORE-LOCK, WRITE-AT-END, BATCH COMPACTION 규칙보다 우선한다.

1. **LOCK-FIRST, BEFORE SOURCE ACQUISITION** — 회차 시작 시 최신 `main` HEAD와 `state/execution_lock.json`부터 fresh-fetch한다. 다른 run의 유효한 active lease가 있으면 자막 수집/콘텐츠 분석/쓰기 없이 즉시 종료한다. 만료된 active lease는 최근 해당 writer의 커밋/실제 작업 여부를 확인한 후 안전하게 인수 가능할 때에만 fresh-SHA로 새 45분 lease를 획득한다. 다시 읽어 자기 run_id가 holder인지 확인한다. 획득 실패 시 콘텐츠 수집·분석 없이 종료하며 read-only actual-count 집계는 가능하다. connector safety/policy 오류는 우회하지 않는다.
2. **ACTUAL STATE AFTER LEASE** — lease 획득 후 roster, base, `data/canonical_events/` 전체를 fresh-fetch한다. effective canonical = unique base IDs ∪ unique event IDs. event sequence와 canonical unique count를 구분하고, progress 요약보다 actual ledger를 우선한다. 이미 canonical인 roster ID는 재분석하지 않는다. legacy roster-outside IDs는 reconciliation backlog일 뿐 실행 blocker가 아니다.
3. **SOURCE-BACKED BATCH** — roster 롱폼 exact YouTube watch URL을 사용한다. 영상 위치 discovery를 반복하지 않는다. 원본 자막/상세 원문/신뢰할 만한 exact-ID 보존자료가 확보된 영상만 분석하며 제목 또는 챕터 목록/짧은 설명만으로 미발언 세부 주장·수치·전략을 추정하지 않는다. source 부족 후보는 기록 가능한 검증 대기 상태로 넘기고 다음 후보로 이동한다. 최대 40편은 상한이다.
4. **DURABLE EVENT-FIRST WRITE** — 영상별 분석 핵심·원문 provenance·시점/위험·정량정보·NEW/REINFORCE/EXTEND/CHANGE/CONFLICT/TIME_SENSITIVE를 작은 `videos/...` 또는 `data/analysis_events/<video_id>.json`로 먼저 저장한다. 그다음 **base 및 event에서 unique Video ID가 아님을 재확인**하고 next max event sequence의 immutable `data/canonical_events/NNN_<video_id>.json`을 생성한다. artifact만 있고 event가 없는 경우에만 sync-only. 분석이 메모리에서 끝났고 durable artifact가 없다면 canonical 또는 pending_sync로 세지 않는다.
5. **FROZEN AGGREGATE** — scheduled/manual fast-path 분석 회차 중 `data/videos.jsonl`, `data/learning_queue.jsonl`, `data/claims.jsonl`은 READ-ONLY compacted base/cache다. connector safety block을 반복하는 이들 파일의 전체 rewrite/compaction을 하지 않는다. event overlay 자체가 영구 canonical 데이터이므로 이들 cache의 미반영은 `compaction_pending` 오류가 아니다. 별도의 명시적 maintenance 작업에서만 compaction을 다룬다.
6. **CHECKPOINT / SUMMARY / RELEASE** — effective canonical unique count가 새로 10의 배수에 도달했을 때에만 knowledge checkpoint를 만든다. 새 영상 수집·분석은 lease 획득 후 20분 시점에 중단하고 25분 안에 종료를 우선한다. 종료 때 actual base+event를 재계산해 작은 `state/progress.json`을 fresh-SHA로 1회 갱신하고 가능하면 unique run event 1개를 남긴다. **다른 write보다 자신의 lease release를 최우선으로 보장**하며, 소유자 재확인 후 release 결과를 재확인한다. 절대 다른 run의 lease를 해제하지 않는다.
7. **ERROR CLASSIFICATION** — `active_writer`, `expired_lease_reclaim_safety_failed`, `source_unavailable`, `artifact_write_failed`, `event_write_failed`, `progress_stale`, `release_failed`를 구별한다. 실제 raw connector error와 시각·파일만 보고한다. 임의로 `OpenAI safety checks`를 우회하거나 모든 GitHub 쓰기가 불가능하다고 일반화하지 않는다.

## Canonical source / 실행 시작 규칙
모든 예약·수동 실행은 이전 채팅이나 progress 요약을 그대로 이어서 사용하지 않는다. 최신 `main`에서 current roster 운영에 필요한 파일만 fresh-fetch하고 actual state를 다시 계산한다.

필수:
- `WORKFLOW.md`
- `VIDEO_INVENTORY_2026-10-07.md`
- `data/videos.jsonl`
- `data/canonical_events/`
- `data/canonical_event_reconciliation.json` — historical event sequence ↔ canonical ordinal mapping
- `state/progress.json`
- `state/execution_lock.json`

필요 시:
- `data/learning_queue.jsonl` — legacy queue reconciliation / source 상태 참고
- `data/learning_queue_unresolved.jsonl` — unresolved 참고
- `state/run_events/` — 최근 writer 실행 감사

과거 `data/inventory_control.json`, `data/channel_snapshot_2026-10-06*.json*`, 794 baseline 관련 파일은 **legacy reconciliation 전용**이며 일반 content-analysis 실행의 START 분기에는 읽지 않는다.

### 현재 상태 재계산
- base canonical count / base max **canonical ordinal**
- canonical event overlay / max **event sequence**
- effective canonical unique count
- roster long-form canonical count / remaining count
- durable pending-sync artifact count
- verification/source-blocked 후보
- next checkpoint

우선순위는 항상 **actual base + canonical-event overlay > progress summary > chat/report memory**다.
과거 duplicate/upgrade event 해석은 `data/canonical_event_reconciliation.json`을 따른다. reconciliation ledger가 있으면 immutable historical event payload의 오래된 필드명보다 이 매핑을 우선한다.

## Baseline inventory event-first mode
**[RETIRED 2026-10-07 — DO NOT EXECUTE]**

과거 794개 추정 baseline inventory를 위한 모든 discovery/event/compaction/lock 예외 규칙은 `VIDEO_INVENTORY_2026-10-07.md`의 791개 확정 roster로 대체되었다. 일반 분석 실행은 이 절의 옛 숫자·조건·파일을 읽거나 분기 기준으로 사용하지 않는다.

## 단일 writer 실행 lease
여러 채팅과 예약작업이 같은 `main`의 공유 mutable state를 동시에 수정하지 않도록 canonical/aggregate/progress write 전에 `state/execution_lock.json` lease를 획득한다. retired baseline inventory 예외는 더 이상 실행 규칙으로 사용하지 않는다.

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
- 저장 실패 시 **durable analysis artifact가 이미 저장된 경우에만** `pending_sync`로 보낸다. durable artifact가 하나도 없으면 `reanalysis_required`로 두고 즉시 다음 분석 가능한 영상으로 이동한다.

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
### 영상별 최소 저장
- concise canonical analysis artifact
- immutable `data/canonical_events/NNN_<video_id>.json`

canonical analysis Markdown이 raw safety block으로 1회 retry까지 실패하면 compact structured `data/analysis_events/<video_id>.json` fallback을 허용한다.
**durable analysis artifact가 하나도 없는 상태는 pending_sync로 표시하지 않는다.** 저장되지 않은 transient 분석은 다음 실행에서 재분석 가능한 후보로 남긴다.

### 실행 말미 batch 저장
영상별 event 생성이 끝난 뒤에만 아래 aggregate를 path당 최대 1회 갱신한다.
- `data/videos.jsonl`
- `data/learning_queue.jsonl`
- `data/claims.jsonl`
- 관련 knowledge 묶음
- checkpoint일 때만 framework/synthesis/PDF
- `state/progress.json`

aggregate 실패는 `compaction_pending`이며 이미 성공한 canonical event를 취소하지 않는다.

## 10편 체크포인트
**effective canonical unique-video count**가 10의 배수에 새로 도달하면 그 영상 반영 직후 누적지식을 재종합한다. event sequence 번호 자체가 10의 배수인지는 checkpoint 조건이 아니다.
- 반복원칙·예외·변화·충돌
- 연금저축·IRP·ISA·국민연금·세금·인출·자산배분
- 전체 박곰희 프레임워크
- 해당 10편 구간 변화와 누적결론 한국어 PDF

synthesis/framework/state의 GitHub 저장이 실패하면 산출물은 `pending_sync`로 기록하되 콘텐츠 분석 lane 전체를 중단하지 않는다.

## 실행 종료 조건
다음 중 하나일 때만 종료한다.
- 실행시간/도구 한도 도달
- 이번 실행에서 roster 미분석 후보를 충분히 스캔했지만 더 이상 source-backed 분석 가능 후보가 없음
- 최대 신규 분석 목표 40편 도달

다음 사유만으로는 종료하지 않는다.
- GitHub aggregate write 실패
- 특정 영상 source 미확보
- chronology 미정
- legacy queue/inventory 불일치
- unresolved ID 존재

**신규 inventory discovery 1패스는 종료조건이 아니다.** 791 roster가 이미 확정되어 있으므로 기본 분석 실행에서 신규 discovery를 요구하지 않는다.

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
- 모든 writer 실행은 종료 시 unique `state/run_events/<timestamp>_<run_id>.json` 1개를 append-only로 남긴다.
- 최소 필드:
  - `run_id`, `source`
  - `started_at`, `finished_at`
  - `start_effective_canonical`, `end_effective_canonical`
  - `newly_analyzed_count`
  - `sync_only_count`
  - `durable_pending_sync_count`
  - `last_run_result`
  - `write_failure`
- `discovery_checked_at`은 roster-only mode에서 더 이상 필수 필드가 아니다.
- `state/progress.json`은 최신 summary이고 실행이력 원장이 아니다.
- `state/run_events/`가 writer 실행이력 원장이다.

## GitHub write 안전 프로토콜
이 절은 모든 canonical write와 heartbeat write에 강제 적용한다.

- 실행 시작 시 읽은 canonical 파일의 SHA는 **충돌 확인용 snapshot**일 뿐, 실행 말미 write의 SHA로 재사용하지 않는다.
- 기존 파일을 수정하기 직전에 반드시 그 **정확한 target path를 다시 fetch**하고, 그 fetch가 반환한 최신 blob SHA로 `update_file`을 수행한다.
- 같은 파일을 한 실행에서 두 번 이상 수정할 때는 직전 성공 write가 반환한 새 content SHA를 다음 write에 사용하거나 다시 fetch한다. 오래된 SHA를 재사용하지 않는다.
- 같은 path에 대한 write/delete는 절대 병렬 실행하지 않는다. canonical write는 path 단위로 직렬화한다.
- SHA mismatch, 409/422 conflict, stale-file/safety precondition 계열 오류가 발생하면 실패로 확정하기 전에 target file을 즉시 다시 fetch하고, 최신 내용에 의도한 변경을 재적용하여 **1회 자동 재시도**한다.
- 위 재시도도 실패한 경우, durable analysis artifact가 이미 있으면 `pending_sync`/write failure로 기록한다. durable artifact가 하나도 없으면 `reanalysis_required`로 기록하고 다음 콘텐츠/다른 파일로 진행한다.
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
3. **WRITE LOCK** — 영상 source 확보·분석에 앞서 위 LOCK-FIRST 규칙에 따라 single-writer lease를 획득한다. acquired 후 effective canonical IDs와 max event sequence를 fresh-fetch해 중복을 제거한다.
4. **MINIMAL CANONICAL WRITE** — 영상별 concise analysis artifact와 immutable canonical event만 직렬 생성한다. Markdown 저장 실패 시 fallback structured analysis artifact를 1회 시도한다. fallback까지 실패하여 durable artifact가 하나도 없으면 `reanalysis_required`로 두고 다음 영상을 계속한다. durable artifact는 있으나 event/aggregate sync만 남은 경우에만 `pending_sync`다.
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
- `data/canonical_events/NNN_<video_id>.json`은 immutable event ledger다. 파일명의 `NNN`과 event의 `sequence`는 **event sequence**다.
- 분석 artifact가 존재하고 **base에 없는 video_id의 canonical event** create가 성공하면 해당 영상은 effective canonical에 추가된다.
- 동일 video_id 또는 동일 event sequence의 신규 중복 생성은 금지한다.
- 과거에 이미 생성된 중복 event(현재 157 `OlurWhrOsLs`, 158 `AzY0FU-HxME`)는 삭제·재작성하지 않고 **audit-only duplicate event**로 유지하며 effective canonical count에는 더하지 않는다.
- 다음 event sequence는 effective canonical count가 아니라 `max(모든 canonical event sequence, 기존 source_event_sequence)+1`로 계산한다.

### Effective canonical state
- effective canonical = compacted `data/videos.jsonl`의 unique video_id + base에 없는 canonical event video_id overlay.
- **effective canonical count**는 unique video_id 개수다.
- **event sequence**는 append-only ledger 순번이며 duplicate audit event 때문에 effective canonical count와 일치하지 않을 수 있다.
- `data/videos.jsonl`의 `sequence`는 **unique canonical ordinal**이며 1부터 연속으로 유지한다.
- event를 base에 compact할 때 신규 unique video는 `data/videos.sequence = 이전 unique canonical count + 1`, `source_event_sequence = event.sequence`로 저장한다.
- processed/checkpoint 계산은 effective canonical unique count를 사용하고, 다음 event 번호 계산은 max event sequence를 사용한다.

### 두 종류의 sequence — 혼동 금지
- **canonical ordinal**: `data/videos.jsonl.sequence`. unique canonical video의 순번이며 1부터 연속 유지한다.
- **event sequence**: `data/canonical_events/*.json.sequence`. append-only event ledger 순번이다.
- 역사적 duplicate upgrade event 157·158 때문에 현재 event sequence가 canonical ordinal보다 2 앞서 있다.
- 신규 unique canonical video event에는 앞으로 가능하면 `canonical_ordinal`도 함께 기록한다.
- canonical 문서의 표시 번호는 canonical ordinal을 사용하고, upgrade/sync event 번호는 별도 metadata로 표기한다.

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
