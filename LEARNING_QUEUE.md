# 박곰희TV 학습 목록 — Master Inventory v3

- 갱신일: 2026-10-06
- 기준 채널: `@gomhee`
- 현재 공개 채널 총 업로드 수(제3자 공개 통계 관측값): **794개** — Shorts 포함
- Video ID까지 식별된 롱폼 후보: **174편**
- canonical processed: **139편**
- identified_unprocessed: **35편**
- 이 중 콘텐츠 분석 완료·canonical sync 대기: **0편**
- source acquisition 대기: **22편**
- source 미확보 verification_needed: **13편**
- 게시일 값 확보: **70편** (strict `date_verified` 38편)
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
현재 identified_unprocessed 35편은 재분석 backlog가 아니다.
- **0편:** 기존 분석문 sync backlog 없음
- **22편:** exact ID 선확보 후 source_acquisition_needed
- **13편:** source 미확보로 verification_needed

따라서 다음 콘텐츠 분석은 위 backlog의 반복 재검색이 아니라 **신규 discovery에서 확보한 source-backed 롱폼**부터 이어간다.

## 완전성
현재 master queue는 운영 기준 목록이며 YouTube 전체 롱폼 ID 전수확정 목록이라고 주장하지 않는다.
새 ID가 발견되면 Video ID 중복을 확인해 계속 누적한다.

앞으로는 just-in-time discovery 대신 **선행 inventory reservoir**를 유지한다.
- exact-ID 미처리 buffer 목표: 100편
- 최소 안전 buffer: 60편
- buffer가 60 미만이면 inventory bootstrap을 우선해 최대 40개 exact ID를 먼저 등록
- full source가 아직 없으면 `source_acquisition_needed`로 등록하고 제목만으로 분석하지 않음
- source acquisition은 최대 20편씩 별도 배치
- 상세 규칙: `data/inventory_control.json`, `WORKFLOW.md`


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

- 2026-10-05 `JwoiWyec7ks`는 canonical sequence 64로 index/queue/claim/framework 정합화를 완료했다.

- 2026-10-05 `Q3OrWpOVS2E`는 event-first canonical sequence 65로 승격 후 base index/queue/claim/IRP/framework까지 compaction 완료했다.

- 2026-10-05 `iy7_HMMSLGc`는 event-first canonical sequence 66으로 승격 후 base index/queue/claim/ISA·연금저축/framework compaction을 완료했다.

- 2026-10-05 `Gk3-ZC9W3vw`는 canonical sequence 67로 event-first 승격 후 외국납부세액 tax-location 지식과 base compaction을 완료했다.

- 2026-10-05 `0Qt8rm01SOg`는 canonical sequence 68로 event-first 승격 후 ISA 월배당 feedback-loop 지식을 반영했다.

- 2026-10-05 `sqh-919UMVk`는 canonical sequence 69로 승격하고 KRX 현행 서킷브레이커 규칙을 공식 검증했다.

- 2026-10-05 `FPA12oQeQbc`는 canonical sequence 70으로 승격하고 Batch 007 (61~70) synthesis/PDF 체크포인트를 완료했다.


## 2026-10-06 inventory-wide fallback 전환
순차 chronology가 불완전할 때 더 이상 분석을 멈추지 않는다. effective canonical과 전체 exact-ID inventory를 대조해 미확인 source-backed 롱폼을 직접 선택한다.

이번 수동 진단에서 queue의 `n1hVZlHq-RA`가 `source_backed_ready`로 남아 있었지만 canonical event 071이 이미 존재하는 stale-state를 발견했다. 이를 재분석하지 않고 base index와 queue에 compact해 정합화했다.

전체 inventory discovery에서 기존 queue에 없던 source-backed 롱폼 6편을 신규 분석·canonicalize했다.
- 072 `-3iNxrjeQak` — 곰희책방#2 | 부에 이르는 가장 단순한 길
- 073 `GmwmPKFY4PY` — 월급300만원으로 1억 만드는 계획 | ASK곰희 ver.2026
- 074 `yl0UyfkvaHs` — 추석특집 투자초보편 몰아보기
- 075 `_vo1uqkk1yo` — 절세계좌 3개 나눠서 투자하는 방법 | 1편
- 076 `H04y8gmBtqk` — 절세계좌 3개 나눠서 투자하는 방법 | 2편
- 077 `-71DQQIcTlc` — 연금저축을 통한 장기 현금흐름 만들기 (상세 보존자료 제목; YouTube 정확 제목 미확정)

당시 sync-debt 정리 직후 actual data 기준:
- master queue: **152편**
- canonical/effective processed: **139편**
- remaining effective-unprocessed: **13편**
- 기존 분석 완료·sync 대기: **0편**
- verification_needed: **13편**
- effective source-backed unanalyzed ready: **0편**
- Video ID unresolved: **2편**
- 다음 synthesis checkpoint: **140편**

신규 discovery는 기존 master queue가 YouTube 전체 롱폼 전수목록이 아님을 전제로 계속 수행한다.


### 추가 exact-ID discovery — source 확인 대기
공식 채널 Shorts가 연결한 원본 롱폼 exact ID 4개를 추가 식별했다. 원본 전체 설명·자막·상세자료가 아직 부족하므로 제목을 추측하지 않고 `verification_needed`로 등록했다.
- `GFTYwKkZgoQ`
- `mZnhZM3Wc88`
- `2q6MwCgIRnY`
- `iCApyfb2CzI`

기본 source retry date는 2026-11-05이며 새로운 source 신호가 생기면 그 전에 분석할 수 있다.

## 2026-10-06 synchronization debt 제거 및 backlog 완전 compaction
- 시작 상태: master 152 / processed 77 / pending_sync 62 / verification_needed 13.
- 62편을 재분석하지 않고 canonical sequence 78~139로 승격했다.
- 각 영상에 canonical document, immutable canonical event, data/videos index, queue 상태, unique claim, knowledge ledger를 동기화했다.
- claim ID collision을 점검해 중복 0건으로 정리했다.
- 최종 actual data: master 152 / processed 139 / pending_sync 0 / verification_needed 13 / data/videos 139 / max sequence 139.
- 다음 synthesis checkpoint는 140편이다.
- 80/90/100/110/120/130 checkpoint 한국어 PDF 6개를 생성하고 170 DPI 렌더 검증에서 글자 깨짐·clipping·overlap 없음으로 통과했다.


## 2026-10-06 선행 inventory bootstrap
분석 때마다 영상을 즉석에서 찾는 구조를 중단하고, exact Video ID를 먼저 대량 목록화하는 방식으로 전환했다.

1차 공개 색인 대조에서 기존 152편 master inventory에 없던 exact ID 9개를 추가 등록했다.
- 153 `Sk1JarcNNNs` — 남은 현금은 모두 CMA에 넣어둬야 하는 이유 ver.2025
- 154 `PW1EuMtw18o` — ISA 관련 원본 영상 exact ID, 정확 제목 확인 대기
- 155 `UzoZbeqcctg` — ISA 사용 설명서
- 156 `fnLgP_KCv8A` — ISA Q&A 원본 영상 exact ID, 정확 제목 확인 대기
- 157 `a6ET79jF7Xk` — 38강 - 주식 차트 보는 법
- 158 `Dmq6Tw3Gy7Q` — IRP 안전자산 30% 관련 영상
- 159 `giJLCf3ed_s` — ISA를 할까? 연금저축을 할까?
- 160 `l5PUUXweyGs` — 주부도 연금저축 하는 게 좋을까? | ASK곰희
- 161 `wI6Kd-BJqqk` — 연금저축과 IRP의 결정적인 차이

현재:
- exact-ID master inventory: **161편**
- canonical processed: **139편**
- exact-ID 미처리 buffer: **22편**
- source acquisition 필요: **22편**
- verification_needed: **13편**
- source-backed ready: **0편**
- Video ID unresolved: **2편**

목표 buffer 100편에 도달할 때까지 다음 실행들은 신규 분석과 병행해 inventory bootstrap을 우선한다.


## 2026-10-06 전체 채널 snapshot 1차 bootstrap
- 기준 전체 공개 업로드 target: **794개**
- 현재 exact-ID snapshot: **193개 / 794개 (24.3%)**
- 이번 실행 신규 exact ID: **32개**
  - 롱폼: **13편**
  - Shorts: **19편**
- snapshot 내 현재 분류: long_form 173 / long_form_compilation 1 / short 19
- learning queue: **174편**
- canonical processed: **139편**
- learning queue 미처리: **35편**
  - source_acquisition_needed: **22편**
  - verification_needed: **13편**
- Video ID unresolved: **2편**
- 전체 snapshot 잔여 식별 목표: **601개**

이번 실행은 학습보다 목록화를 우선했다. Shorts는 학습 본체에서 제외하지만 전체 채널 snapshot에는 보존한다. 다음 목록화 실행은 193개 snapshot에서 이어서 exact ID를 추가한다.
