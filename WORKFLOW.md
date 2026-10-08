# 박곰희TV 영상 학습 워크플로 — V3 단일 저장 (2026-10-08)

## 목적 및 확정 범위
박곰희TV 원본 콘텐츠를 근거 기반으로 분석하고 장기 투자 지식을 축적한다. 목표는 인프라 기록이 아니라 실제 영상 분석이다.
- 확정 로스터 `VIDEO_INVENTORY_2026-10-07.md`: 791개 고유 영상, 롱폼 703개, Shorts 88개. 별도 지시 없으면 재수집하지 않는다.
- 기존 `data/videos.jsonl`, `data/canonical_events/`, `data/analysis_events/`, `knowledge/`, `synthesis/`는 보존한다. 과거의 canonical 등록을 심층 검증 완료와 혼동하지 않는다.
- **V3부터 신규 영상의 canonical 학습 기록은 검증된 단일 `data/analysis_events/<video_id>.json` 파일이다. 신규 `data/canonical_events/` 등록은 하지 않는다.** 이는 차단된 쓰기를 다른 이름으로 재시도하는 것이 아니라 불필요한 이중 기록 요건을 없애는 데이터 모델 변경이다.

## 기존 기록과 신규 기록의 구분
1. 레거시 등록 집합 L: `data/videos.jsonl`의 video_id와 **기존** `data/canonical_events/*.json`의 video_id의 합집합. 이벤트 순번은 레거시 감사 목적으로만 유지한다.
2. V3 유효 분석 집합 A: `data/analysis_events/<video_id>.json` 중 실제 재조회가 가능하고 JSON이 유효하며, 파일명 video_id와 내부 ID 및 source_url의 YouTube ID가 일치하고, 제목·출처 수준·분석 근거·핵심 주장·실행 지침·전제·위험·검증상태·한계가 확인되는 기록. 자동 전사 품질 문제와 미검증 수치는 명시해야 한다. 분석 본문이 빈 파일 또는 출처가 확인되지 않은 파일은 제외한다.
3. **완료 ID 집합 = L ∪ A_complete**. 롱폼 완료 수는 이 집합과 확정 로스터의 롱폼 ID의 교집합 수이다. 같은 영상은 어느 자료에 몇 번 있어도 1편이다. 로스터 외 레거시 12편은 분모·분자에서 제외한다. `state/progress.json`의 스냅샷은 현재 사실로 쓰지 않는다.
4. V3에서 `A_complete`는 영상의 원문 전사 또는 동일 영상 ID의 신뢰할 수 있는 충분한 본문을 검토하여 주장을 설명할 수 있는 분석이다. 전사 없이 설명·챕터만 확인한 제한적 결과는 `analysis_status: "PARTIAL"`로 저장할 수 있으나 V3 신규 완료 수에는 넣지 않는다. 출처 기반 분석 완료는 시각적 영상 프레임 검토 완료와 구분한다.
5. 역사적 event 번호 231까지는 수정하지 않는다. **`09R29vsv6to`는 기존 분석 파일의 video_id·원문 출처·13개 주장·위험 및 검증 상태를 확인한 V3 완료 기록**이다. 과거에 차단된 event #232를 생성·복구하려 하지 않는다. 기존 pending_sync는 유효 분석 파일인지 판정하여 미완료/완료 상태를 재분류한다. 새로운 번호를 산출할 필요 없다.

## 실행 절차 — 영상 분석 중심
1. 최신 `main`에서 확정 로스터와 기존 L 및 유효 A를 조회해 미완료 롱폼 video_id를 정한다. 재분석/중복 생성 금지. 다음 우선 후보는 `PW1EuMtw18o`, `2GjGjwkHrMA`, `fnLgP_KCv8A` 등 실제 미완료 ID.
2. 정확한 원본 YouTube URL에 대해 정상 제공되는 Firecrawl Alexandria `youtube/read`의 한국어 전사를 우선 확인한다. 얻은 원문 전체를 살펴 주제, 원리, 핵심 주장, 근거, 실행 조건·예외·위험, 수치, 다른 지식과의 관계(NEW/REINFORCE/EXTEND/CHANGE/CONFLICT/TIME_SENSITIVE)를 분석한다. 영상 프레임을 보지 않았으면 보았다고 주장하지 않는다.
3. ISA·연금·세법·건강보험·증권 거래 규정 등 시점 의존 내용은 가능한 한 최신 공식 1차자료와 교차 검증한다. 영상 발행 당시 주장과 현재 유효한 사실을 구분한다. 자동 자막의 의심스러운 이름·수치는 추측하지 않고 OPEN/미확인으로 표시한다. 공개 저장소에 전체 전사를 복제하지 않는다.
4. **영상별 단 한 번 쓰기**: 생성 전에 파일 존재 여부 확인 → `data/analysis_events/<video_id>.json`을 완전한 분석과 품질 메타데이터로 신규 생성 → 파일 재조회 → JSON 및 ID/출처/내용 검증. 이 파일의 재조회와 필수 항목 검증이 성공하면 V3 신규 학습 완료 1편이다. 새 canonical event/전역 상태/작업 잠금 파일은 작성하지 않는다.
5. 필수 데이터: `schema_version`, `video_id`, `source_url`, `source_level`, `title`, `core_claims`, `actionable_guidance`, `assumptions`, `risks_and_exceptions`, `quantitative_claims`, `relations`, `verification_status`, `limitations`. 신규 파일에는 `analysis_status: "COMPLETE"` 또는 `"PARTIAL"`을 명시한다. 기존 V2 파일의 analysis_status 부재만으로 부적격 처리하지 않고 실제 내용·출처·검증 정보를 확인한다.
6. 한 실행에 3~5편을 목표로 하되 근거 품질을 우선한다. 도구·시간 제약 시 1편 가능하다. 매 10편의 실제 완료 기록 누적 후 `knowledge/`, `synthesis/`에서 지식을 통합하되 신규 분석을 계속 미루지는 않는다.

## 실패·동시성 안전 규칙
- 예약작업은 하나만 운용하며 일반 실행에서 `state/execution_lock.json`을 사용하지 않는다. 같은 video_id에 대한 수동·예약 분석이 겹칠 가능성이 있으므로 **저장 직전 현재 파일을 재조회**하고 이미 존재하면 재사용한다. 두 실행이 동시에 쓰는 경우 GitHub의 파일 중복/409/422는 멈추고 실제 파일을 확인한다.
- 기존 `data/videos.jsonl`, `data/learning_queue.jsonl`, `data/claims.jsonl`, `data/canonical_events/`, `state/progress.json` 및 잠금 파일은 일반 분석 회차에서 **읽기 전용**이다.
- 실제 `This tool call was blocked by OpenAI's safety checks`가 발생하면 해당 요청을 정책상 차단으로 기록하고 **그 실행에서 추가 쓰기를 중지**한다. 텍스트·경로·인코딩·호출 도구를 바꿔 정책 차단을 우회하지 않는다. GitHub API의 409/422 등 서버 응답과 구분한다. 이유를 특정할 수 없으면 특정하지 않는다.
- 검증된 GitHub 파일이 없다면 분석 완료로 계산하지 않는다. 작업 실행/전사 획득만으로 성과를 부풀리지 않는다. 사용자 요청 없이 예약작업을 자동 비활성화하지 말고 실제 차단을 보고한다.

## 종료 보고
첫 문장에 **이번 실행에서 GitHub에 실제 신규 저장·재조회·검증한 롱폼 영상 수, ID/제목**을 명시한다. 누적은 **(레거시 L ∪ 유효 V3 A_complete) ∩ 확정 롱폼 / 703**으로 보고한다. PARTIAL, 미검증, 레거시 기존 등록, 신규 실질 학습을 구별한다. 공식 검증과 열린 쟁점, 장애 경로·오류 원문, 다음 후보를 기록한다.

## V3 전환 사실
2026-10-08 점검 시 `data/analysis_events/09R29vsv6to.json` 분석 결과(13개 핵심 주장, 원문 전사 및 검증 메타데이터)가 존재하며 `data/canonical_events/232_09R29vsv6to.json`은 존재하지 않았다. 마지막 확인된 레거시 이벤트는 `231_eTOOtll0VPc.json`이다. 과거 기록은 변경하지 않는다. 저장소가 안전 검사의 정확한 내부 차단 사유를 표시하지 않으므로 단일 쓰기 구조 또한 무조건적인 저장 성공을 보장하지는 않는다.
