# pensionport

박곰희TV의 투자·연금·자산관리 영상을 **검증 가능한 원문에 기반해 개별 분석하고, 투자 원칙과 전략을 누적 통합**하는 저장소입니다.

## 현재 운영 기준 (2026-10-08)

- 고정 영상 roster: [VIDEO_INVENTORY_2026-10-07.md](VIDEO_INVENTORY_2026-10-07.md) — 791편(롱폼 **703편**, Shorts 88편). 기본 영상 분석 대상은 롱폼만입니다.
- 유일한 활성 실행 계약: [WORKFLOW.md](WORKFLOW.md). 오래된 794-baseline 목록화, 매 실행 aggregate compaction, 시간당 3편 고정 제한은 폐기했습니다.
- 원본: exact YouTube ID의 한국어 전사(가능한 경우) → 해당 영상 제작자 설명/챕터 → 신뢰할 만한 상세 보존자료. 출처 범위를 기록하고 자동 전사의 숫자/고유명사 오류는 공식자료로 검증합니다.
- 저장: **1편 분석 → `data/analysis_events/<video_id>.json` → `data/canonical_events/<event_sequence>_<video_id>.json` → 실제 재조회 검증**, 각 쓰기는 단일 writer lease 내에서만 진행합니다.
- 회차당 초기 목표 3~5편(1편 end-to-end 선검증), 연속 정상 동작 후 점진 확대; **최대 40편은 상한**입니다. 지식 종합은 유니크 canonical 수 **10편 증가 구간의 checkpoint**에서 실시합니다.
- `data/videos.jsonl`, `data/learning_queue.jsonl`, `data/claims.jsonl`은 일반 회차에서 **읽기 전용 캐시**입니다.
- 진행률은 base와 immutable event의 **중복 제거한 고유 Video ID 합집합**으로 계산합니다. `state/progress.json`은 요약일 뿐입니다. canonical 등록과 심층 학습 품질은 별도로 평가합니다.
- 2026-10-08 원본 확보 실험은 [data/source_acquisition/youtube_read_pilot_20261008.json](data/source_acquisition/youtube_read_pilot_20261008.json)에 기록했습니다. 실험 7편 성공은 전체 영상 성공 보장이 아닙니다.
- 공용 GitHub에는 보호되는 전사 전문을 대량으로 복제하지 않고, 출처·근거·핵심 분석과 검증 여부를 보존합니다.

**주의:** `WORKFLOW.md`와 실제 event ledger가 다른 파일의 오래된 진행 요약보다 우선합니다.
