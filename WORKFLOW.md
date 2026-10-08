# pensionport 운영 규칙 — 단일 활성 워크플로 (2026-10-08)

이 문서는 수동 및 예약 박곰희TV 영상 연구의 **유일한 실행 계약**이다. 과거 794-baseline discovery, READ/ANALYZE-BEFORE-LOCK, WRITE-AT-END, 매 실행 aggregate compaction, 3편 상한 등의 규칙은 **폐기**한다. 오류 복구보다 콘텐츠 분석을 우선하되, 검증되지 않은 분석을 완료로 세지 않는다.

## 1. 확정 대상과 진실의 원장

- 확정 roster: `VIDEO_INVENTORY_2026-10-07.md`의 791개 고유 Video ID, 그중 **롱폼 703편**을 분석 대상으로 한다. Shorts 88편은 별도 요청이 없으면 분석하지 않는다.
- 분석 후보는 **로스터의 미분석 롱폼 Video ID**만 사용한다. 게시일/순서는 선호 조건이지 blocker가 아니다. 옛 794-baseline, reservoir, channel snapshot, 추가 목록 발견은 시작 조건이 아니다.
- canonical의 근거 데이터: `data/videos.jsonl`의 unique `video_id` 합집합 `data/canonical_events/*.json`의 unique `video_id`. `state/progress.json`은 캐시된 요약이며, 실제 합집합과 다르면 **항상 원장이 우선**한다.
- canonical event filename 및 event 내부 `sequence`는 **event sequence**로서 distinct canonical 수와 다르다. 다음 번호 = 실제 event sequence 최댓값 + 1. base의 `sequence`는 historical canonical ordinal이다. `data/canonical_event_reconciliation.json`은 역사적 매핑 참고자료이며 내부 snapshot 숫자를 현재치로 가정하지 않는다.
- base에 있던 ID와 canonical event에 있는 ID는 중복 분석하지 않는다. roster 밖 기존 분석은 보존하되 **703편 완료율에서 제외**한다. 품질 등급이 낮은 기존 canonical은 정기 재학습 lane에서 따로 검토한다.
- 과거 생성된 aggregate `data/videos.jsonl`, `data/learning_queue.jsonl`, `data/claims.jsonl`은 일반 예약/수동 학습 회차에서 **READ-ONLY / FROZEN CACHE**다. compaction은 사용자의 별도 유지보수 요청에서만 수행하며, cache와 event의 일시적인 불일치를 오류로 세지 않는다.

## 2. 정확한 실행 순서 — LOCK → SOURCE → ANALYZE → SAVE → VERIFY → RELEASE

1. **LOCK-FIRST:** 최신 `main`과 `state/execution_lock.json`을 읽는다. 다른 실행의 유효한 active lease가 있으면 **자막 수집·분석·쓰기 없이 종료**한다. active가 만료되었더라도 최근 owner 활동을 확인하고 안전한 경우에만 인수한다. released 상태에서는 fresh blob SHA로 자신의 고유 `run_id`, started_at, lease_until(45분)을 갱신한 뒤 반드시 재조회해 자신의 active 소유권을 확인한다. 실패하면 읽기 전용 집계만 가능하다.
2. **FRESH LEDGER:** lease 획득 후 roster, `WORKFLOW.md`, base, canonical event 목록, 분석 artifact 목록, progress, source 원장을 조회하고 유니크 ID 및 event 최대 번호를 **실제 파일**로 재계산한다. 중복 ID는 분석 후보에서 뺀다. 기존 durable artifact만 있고 event가 없는 것은 분석보다 먼저 sync-only로 복구한다.
3. **SOURCE:** 후보의 정확한 YouTube watch URL로 `Firecrawl Alexandria youtube/read`를 우선 시도한다. `language=ko`, `formats=['markdown']`이고 응답의 `## Transcript`를 실제 검사한다. 검증 표본 7편에서 작동한 경로지만 703편 전체 성공을 보장하지 않는다. 도구가 지원되지 않는 실행 환경이면 가능한 정상 접근 경로(원래 영상·공개 제작자 설명·챕터·exact-ID 상세 보존자료)를 확인한다. 실패한 영상은 출처 대기 대상으로 넘긴다. 동일한 정책 차단을 우회하거나 반복하지 않는다.
4. **ANALYZE:** 원문을 실제로 읽고 투자 철학, 핵심 주장, 적용 전제·조건, 상품/계좌 사용법, 위험·예외, 숫자·세율·기간, 이전 영상과의 NEW/REINFORCE/EXTEND/CHANGE/CONFLICT/TIME_SENSITIVE 관계를 추출한다. 자동 음성인식(ASR)은 수치·고유명사에 오류가 있으므로 불명확한 숫자는 미확정으로 보류한다. 연금/IRP/ISA/세금/건보료/거래소·법령 등 시간의존 주장만 필요한 범위에서 최신 공식 1차자료로 검증한다. **당시 설명과 현재 적용법을 구분**하고, 외부자료의 내용을 화자의 실제 발언으로 귀속하지 않는다. 자막을 읽은 것만으로 영상 프레임까지 분석했다고 기록하지 않는다.
5. **PER-VIDEO SAVE, NO LOSS:** 영상 **1편을 분석한 즉시** 검증 가능한 소형 `data/analysis_events/<video_id>.json`을 생성/업데이트해 실제 재조회한다. 이미 존재하면 SHA 및 내용으로 재사용한다. 생성 성공 후 fresh ledger를 확인하여 base/event에 없는 ID일 때만 유일한 `data/canonical_events/<next_sequence>_<video_id>.json`을 생성한다. event와 artifact 둘 다 재조회 성공한 경우에만 `newly_analyzed_count += 1`. artifact가 있고 event만 실패한 경우 **durable_pending_sync**(다음 회차 event만 작성)로 기록한다. artifact 생성 자체가 실패한 경우 **reanalysis_required**, 신규 분석 완료 0편으로 취급한다. 메모리의 전사·추론 결과를 완료로 세지 않는다.
6. **CONTROLLED THROUGHPUT:** 새 저장 경로 검증 단계에서는 1편 먼저 end-to-end 성공시키고, 안정화 기간에는 회차당 **3~5편 목표**로 운영한다. 연속 2회 이상 정상 저장·해제 성공을 확인한 뒤 10편, 그다음 최대 40편으로 확장할 수 있다. 최대 40은 *상한*일 뿐 강제 할당이 아니다. 20분이 지나면 신규 원본 확보를 중단하고 약 25분 내 종료 절차를 우선한다. 저장 장애가 발생한 경우에는 같은 회차에서 추가 영상 분석을 쌓아 놓지 않는다.
7. **SUMMARY/RELEASE:** 저장된 artifact + canonical event의 실제 합집합으로 `state/progress.json`의 작은 수치만 fresh-SHA 재조회·merge 갱신한다. 가능하면 고유 `state/run_events/<timestamp>_<run_id>.json`에 신규 canonical 수, 출처 시도·성공, 저장 실패 상태, 종료 결과를 남긴다. 진행 요약이나 run-event 쓰기가 실패하더라도 **자신의 lock 해제 및 해제 확인이 최우선**이다. 절대 다른 실행의 active lease를 해제하지 않는다.

## 3. 쓰기 실패와 재시도 원칙

- **GitHub create/update 요청이 실제 실패했을 때만** `artifact_write_failed`, `event_write_failed`, `lock_update_failed` 등으로 보고한다. 오류 자료는 대상 경로, 호출 action, 실제 오류 문자열/클래스, fresh-refetch 결과, 최종 상태를 포함한다.
- GitHub 409/422 등 **충돌·stale SHA로 확인되는 복구 가능한 오류에 한해서** 대상 파일을 fresh-fetch하고 원하는 상태가 이미 반영됐는지 먼저 확인한 뒤 최대 1회만 정상 재시도한다.
- **`OpenAI safety checks` 등 안전/정책 검사 차단**은 SHA 충돌과 **다른 분류**다. 동일·변형 payload로 재호출하거나 대상/문구를 바꿔 우회하지 않는다. 정확한 실패 target을 기록하고 신규 콘텐츠 분석·일반 write를 중단하며, 자신의 lock 해제만 우선한다. 정책 차단 이유를 증거 없이 단정하지 않는다.
- artifact 실패 시 다음 후보 4편을 계속 분석해서 결과를 메모리에 쌓지 않는다. 실패 artifact를 canonical이나 `pending_sync`로 세지 않는다. event 실패 후 durable artifact가 존재할 때에만 `pending_sync`로 센다.
- 도구 호출 전 차단/미호출 등 raw error가 없다면 성공 또는 실패를 추정하지 않고 `write_status_unknown`이라고 보고한다. 필요하면 read-only 상태확인을 통해 정확한 판정을 한다.
- 같은 파일 write는 직렬, `fetch_file(target) → merge → update_file(fresh sha)` 순서를 사용한다. 다른 실행이 실제 쓰고 있으면 중단한다. 내용이 이미 반영됐으면 재쓰기하지 않는다.
- 경과시간이 과도하거나 lock release에서 오류가 나더라도 다른 owner에게 강제 변경하지 않는다. lease 만료는 자동으로 파일을 `released`로 바꾸는 기능이 아니다. 불확실하면 상태와 owner를 보고한다.

## 4. 영상별 보존 품질과 완료율

- 결과의 최소 기록: Video ID/정확한 원본 URL/업로드일/원본 종류 및 범위/언어/ASR 품질·화면 확인 여부/핵심 주장/적용 전제/실행 방법/정량정보와 공식 교차검증/위험과 예외/관련 주제·기존 지식/미확인 사항.
- 음성·전사 전체 확보 `TRANSCRIPT_BASED`, 음성/영상 화면까지 확인 `AUDIO_VISUAL_REVIEWED`, 상세 설명 등 부분자료 `PARTIAL`, 출처 미확보 `SOURCE_PENDING`를 구분한다. 전사 섹션만 존재해서 영상 **전체/화면 분석 완료**로 단정하지 않는다.
- **canonical 등록 완료율**과 **품질 심사 통과 심층 학습률**은 별개의 지표다. 옛 canonical에 필수 항목이 빠졌다고 영구 원장에서 삭제하지 않으며, 별도 `REVIEW_REQUIRED`로 품질 개선 대상으로 남긴다. 과거 기록을 재검토하는 작업을 신규 unique 영상으로 세지 않는다.
- 저작권/이용조건을 준수하고 공개 저장소에 저작권 보호되는 전사 전문을 대량으로 복제하지 않는다. 영상 식별자와 출처, 검증 가능한 독자적 분석만 저장한다.

## 5. 체크포인트, 보고, 회복

- **effective unique canonical**이 새로 10의 배수에 도달할 때만 지식 종합(checkpoint)을 갱신한다. event sequence 번호가 10의 배수인지와 혼동하지 않는다. checkpoint 오류가 있어도 이미 저장된 영상 분석을 무효화하지 않는다.
- 매 실행 보고: 실제 신규 unique 영상 수와 ID, 원문 전사 성공/실패, 분석 핵심, 검증된 역사적/현행 주장, 저장 artifact/event 각각의 성공 여부, 현재 로스터 내 `완료/703` 및 잔여, lock 해제 확인, 다음 영상과 blocker를 기록한다. 성공하지 않은 저장은 completed라고 하지 않는다.
- 기본 다음 후보(이미 분석/이벤트 존재 시 건너뜀): `axkP0idg-kA`, `09R29vsv6to`, `eTOOtll0VPc`, `PW1EuMtw18o`, `2GjGjwkHrMA`, `fnLgP_KCv8A`. 2026-10-08 전사 접근 실험은 `data/source_acquisition/youtube_read_pilot_20261008.json`을 참고한다.
- 신규 분석보다 infrastructure 문서 점검만 무한 반복하지 않는다. 정상 실행에서는 **소형 영상 1편의 실제 저장·재조회**부터 시작한다.
- 이 문서는 기존 `data/canonical_event_reconciliation.json`의 역사적 중복 event 157·158, 기존 저장 영상, 로스터를 삭제하거나 바꾸지 않는다.
