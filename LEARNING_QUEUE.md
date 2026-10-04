# 박곰희TV 학습 목록 — Master Inventory v3

- 갱신일: 2026-10-04
- 기준 채널: `@gomhee`
- 현재 공개 채널 총 업로드 수(제3자 공개 통계 관측값): **794개** — Shorts 포함
- Video ID까지 식별된 롱폼 후보: **141편**
- canonical processed: **63편**
- identified_unprocessed: **78편**
- 이 중 콘텐츠 분석 완료·canonical sync 대기: **69편**
- source 미확보 verification_needed: **9편**
- 게시일 값 확보: **67편** (strict `date_verified` 36편)
- 제목/게시일은 확인됐지만 Video ID 미해결: **2편**
- Shorts: 학습 본체에서 제외
- 중복 기준: Video ID

## 파일 역할
- 식별 완료 master queue: `data/learning_queue.jsonl`
- ID 미해결 롱폼: `data/learning_queue_unresolved.jsonl`
- canonical 완료 index: `data/videos.jsonl`
- 실행상태: `state/progress.json`

## 상태 정의
- `processed`: 개별 분석과 canonical index 반영이 완료된 영상
- `identified_unprocessed`: Video ID는 확인됐지만 canonical 완료 전
- `canonical_sync_status=pending_sync`: 콘텐츠 분석문은 이미 있으므로 **재분석 금지**, sync lane에서만 처리
- `analysis_status=verification_needed`: 신뢰 가능한 원문/자막/상세자료가 없어 분석을 보류
- `date_unverified`: 날짜만 미확정. 분석 가능한 source가 있으면 날짜 때문에 콘텐츠 분석을 막지 않는다.
- `video_id_unresolved`: 제목/날짜는 있으나 Video ID 미해결
- Shorts는 별도 보조자료로만 취급

## 지연 방지 선택 규칙
1. 기존 queue에 **source-backed + 실제 콘텐츠 분석 미완료** 영상이 있으면 즉시 분석한다.
2. `pending_sync` 영상은 재분석하지 않는다. sync 실패는 그대로 두고 다음 콘텐츠로 이동한다.
3. `verification_needed`는 `next_source_retry_at` 전에는 재검색하지 않는다.
4. source-backed 분석 후보가 0이면 **즉시 신규/누락 롱폼 discovery**를 수행해 master queue를 확장한다.
5. 신규 Video ID를 등록한 뒤 source-backed 후보부터 분석을 재개한다.
6. chronology repair, 날짜 보강, unresolved 전수정리는 분석 가능한 콘텐츠가 있는 동안 후순위다.

## verification_needed 재시도
기본 재시도 간격은 **30일**이다. 다음 경우에만 그 전에 재검증할 수 있다.
- 새로운 원문/자막/보존자료 신호가 발견됨
- 사용자가 원문 또는 링크를 제공
- 기존 source 접근성 변화가 확인됨

동일 blocked 영상을 매 실행마다 반복 검색하지 않는다.

## 신규 discovery
기존 분석 가능 큐가 비면 '더 이상 영상이 없음'으로 해석하지 않는다.
박곰희TV(@gomhee)의 최신/누락 롱폼을 추가 탐색하고:
- Video ID 중복 확인
- Shorts 제외
- 광고·인터뷰·몰아보기·교육시리즈 등 롱폼 포함
- 게시일은 확보 가능한 범위에서 기록
- 분석 전 master queue 등록
- 신뢰 가능한 source 확보 시 즉시 콘텐츠 분석

신규 discovery 1패스에서도 source-backed 후보가 없고 tool/time 한도에 도달한 경우에만 0편 종료가 허용된다.

## 현재 backlog 해석
현재 identified_unprocessed 78편은 '80편을 처음부터 다시 분석해야 한다'는 뜻이 아니다.
- **69편:** 기존 분석문이 존재하며 canonical sync만 필요
- **9편:** source 미확보로 verification_needed

따라서 다음 콘텐츠 분석은 위 backlog의 반복 재검색이 아니라 **신규 discovery에서 확보한 source-backed 롱폼**부터 이어간다.

## 완전성
현재 master queue는 운영 기준 목록이며 YouTube 전체 롱폼 ID 전수확정 목록이라고 주장하지 않는다.
새 ID가 발견되면 Video ID 중복을 확인해 계속 누적한다. 전수 inventory 대조는 콘텐츠 분석 처리량을 막지 않는다.


## source identity correction
- `videos/pending/O8YUK1OugHs.md`는 오연결 방지 tombstone이며 분석 완료 문서로 계산하지 않는다.
- 정확한 2026-10-02 Video ID는 `6VEfKF7BzZU`이고, 현재 `verification_needed`다.
- `YNOSY15ppf8`는 source-backed 분석 완료 후 `pending_sync` 상태다.


## 최근 신규 discovery
- 2026-10-04 수동 예약 실행 검증에서 `a-890uldXeo` — 「연금저축 사용설명서 | 연말정산 세액공제 가능한 연금저축펀드 | ver.2026」를 신규 식별·분석·canonical 61번으로 반영했다.
- 기존 unresolved 2026-07-24 항목을 해당 Video ID로 해소했다.

## 최근 canonical sync
- 2026-10-04 재개 실행에서 `YNOSY15ppf8` — 「엔화가 쌀 땐 무엇을 하면 좋을까? | 엔화투자방법 1편」의 기존 source-backed 분석을 재분석 없이 canonical 62번으로 승격했다.
- fresh-SHA 직렬 저장 규칙을 적용했고 stale SHA를 재사용하지 않았다.

- 2026-10-05 write 진단에서 `0xMspE3Y2OQ` queue sync가 fresh-SHA 단일 트랜잭션으로 정상 성공하여 canonical 63번으로 정합화했다.
