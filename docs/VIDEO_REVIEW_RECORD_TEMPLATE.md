# 영상별 연구·추가 검증 기록 템플릿

아래 항목은 사람이 작성할 때 사용하는 **계약 표준**이며, 정식 기계 판독 JSON 스키마를 대체하지 않는다. 새로 분석할 때 사용자 원본 SRT를 확인한 경우 원문 전문을 여기에 옮기지 않는다.

## A. 신규 영상 체크리스트 (예: 영상 ID)

- 영상 식별: video_id / 로스터 번호 / 영상명 / 원본 출처 YouTube URL / 영상 게시일(확인된 경우).
- 소스: 비공개 원본 SRT 경로의 **등록 SHA-256**, 전체 cue 수, 마지막 시각, 전 구간 실제 검토 여부. 독립 공개 자막·원음·프레임을 각각 실제로 열어보았는지 **개별 사실값**.
- 주장별: claim_id, 실제 근거 SRT 시간, 의미 요약(원문 복제 금지), `PRIMARY_CONFIRMED | QUALIFIED | HYPOTHETICAL | CONTRADICTED`, 1차자료 URL·발효일·확인일, 정정/조건/범위, 계산 가능하면 수식과 단위·기간.
- 결론: 핵심 지식, 개인적 적용에 필요한 조건, 모든 중요한 손실·세금·중도매각·수익률 가정.
- `analysis_status=COMPLETE`는 충분한 음성 검증 때문이 아니라 **교육적 핵심 주장 검토** 통과로 결정. 자료가 없어 핵심 주장의 사실여부와 제한 범위를 쓰기 어렵다면 `PARTIAL`로 남긴다.
- 저장: `data/subtitles/pilots/<id>.json` (초안 상태 유지) → `data/analysis_events/<id>.json` (정식 V3) → GitHub 재조회·자동검사 → `docs/SUBTITLE_VERIFICATION_QUEUE_20261010.md` 최신 섹션.
- 법률·상품·지식 전반을 바꾸는 **확정된 정정**이 발견되면 `knowledge/`(재사용 규칙), 필요 시 `synthesis/`(교차 영상 정리)에 업데이트: 변경 전/후, 영향을 받는 영상, 1차자료, 기준시점과 예외를 기재한다.

## B. 선택적 후속 검증 항목 (OPEN) — 필요할 때만 생성

**기록 위치:** `data/subtitles/optional_verification_register_20261012.json`의 `items[]` (확정 근거 후 `resolved_items[]`에 이관 가능)

| 필드 | 작성법 |
|---|---|
| `video_id`, `claim_ids` | 로스터에 존재하는 정확한 영상 ID·주장 ID |
| `verification_kind` | AUDIO_NUMERIC / SCREEN_EXAMPLE / PRODUCT_TAX_EFFECTIVE_RATE / LEGAL_TRANSACTION_FACTS / ORIGINAL_BACKTEST_SOURCE_DATA / 기타 |
| `status` | OPEN / RESOLVED_WITH_SCOPE / INAPPLICABLE_WITH_REASON 등 |
| `importance` | HIGH / MEDIUM / LOW (투자판단에 미치는 영향) |
| `blocks_whole_video_analysis` | true는 전체 핵심 지식의 의미가 불명확한 경우에만 |
| `why_open` | 어떤 특정 자료가 없어서 무엇을 확정할 수 없는지 |
| `review_again_when` | 원본 음성/화면 구간, 공식 법령·세무 해석, 원본 엑셀 등 실제로 얻을 수 있을 때 |
| `evidence_references` | 관련 초안/정식분석/1차자료 URL; 출처가 없다면 없다고 기록 |
| `observed_at` | 검토날짜 YYYY-MM-DD |

**완료 판정 예외:** 원음·영상 화면을 보지 않았다는 사실 하나만으로 모든 영상 분석을 보류하지 않는다. 책의 성과 수치를 실제로 검증하지 않았다면 정확한 성과 비교주장만 `OPEN`으로 둔다. 추적 차이·세율·보수·원금 보장 여부에 오류가 있으면 공식 출처로 먼저 정정한다.

## C. 변경시 저장 우선순위

1. **기존 자료의 오류** → 영향을 받는 주장 파일을 수정하고 정식 V3에서도 같은 내용을 정정한다.
2. **전 영상에 영향을 주는 투자규정 변화** → 그 주장의 법령 효력일과 특정 상품/계좌의 적용 요건을 `knowledge/`에 기록한다. 과거 영상 주장 내용은 과거 시점으로 보존한다.
3. **미완성 후속 검증** → 선택 검증 등록부에만 추가하고 다른 영상 연구로 계속 진행한다.
4. **수치나 해석을 뒷받침하는 신규 자료** → 선택 검증 항목을 갱신하고 필요한 영상 주장·분석·관련 knowledge/문서를 동기화한다.
5. **진척 변경** → 누적 상태는 GitHub 감사 CLI의 최신 집계를 기준으로 갱신하고, 옛 진행 수치는 당시 스냅샷으로 명시한다.

**영향 범위 밖:** 이 연구의 어떤 자동 문서 기록도 실제 투자 주문, 계좌 자금 이동, KIS 동기화, 사용자 세금 신고를 실행하지 않는다.

## D. 2026-10-30 신규 V4 심층 연구 전용 추가 필드 (기존 V3 불변)

[품질·의사결정 게이트](V4_RESEARCH_SYSTEM_QUALITY_GATE_20261030.md)를 우선 참조한다. #11 이후 신규 `v4_NNN_*deep/decision/quantitative*review*.json` 작성 시 `quality_gate`에 다음을 별도 저장한다.

- `policy_version=V4_RESEARCH_GOVERNANCE_20261030`; `source_provenance={source_kind, scope_note, raw_hash_recomputed_this_cycle:bool, audio_checked:bool, frames_checked:bool}`. 등록 SHA를 읽기만 하고 원본 파일을 재검증하지 않았으면 bool=false.
- `claim_coverage={rechecked_ids:[], reused_ids:[], contradicted_ids:[]}`. 각 ID는 정확히 한 번 포함하며 반박된 주장 ID는 반드시 정정 전파에 연결한다.
- `model_scope={model_ids:[], arithmetic_status:PASS|OPEN|NOT_APPLICABLE, semantic_status:PASS|OPEN|NOT_APPLICABLE, legal_product_status:PASS|OPEN|NOT_APPLICABLE, tax_basis:SEGREGATED|OPEN|NOT_APPLICABLE, limits:설명}`. 세제·수익률 가정의 실제 타당성과 산술 검사를 구별한다.
- `knowledge_integration={relation:NEW|REINFORCE|EXTEND|CHANGE|CONFLICT|CORRECT|NONE, conflict_ids:[], correction_ids:[], contradicted_blocked:true}`.
- `decision_status={research_status:IN_PROGRESS|CLOSED_WITH_SOURCE_LIMITATIONS|EVIDENCE_BLOCKED, evidence_status:VERIFIED|QUALIFIED|OPEN, max_use:L1|L2, L3_approved:false, L4_approved:false}`.
- `open_blockers=[{id, claim_ids:[], needed, blocked_use, reopen_trigger}]`. 기존 `external_open`가 있으면 각각의 ID와 정확히 연결. 확인할 자료와 해제조건 없는 OPEN은 금지.

신규 리뷰마다 기존 계보/모형 검증 외에 `scripts/verify_v4_research_governance.py` 자동검사를 실행한다. 통과는 구조·상태 차단 확인일 뿐 공식 법령 해석·개인 적합성 승인이 아니다.
