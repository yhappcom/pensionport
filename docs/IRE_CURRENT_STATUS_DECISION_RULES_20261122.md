# IRE 현재 상태 단일 판정 기준 (2026-11-22)

**기계 판독 단일 기준:** [IRE_CANONICAL_CURRENT_RESEARCH_STATUS_20261122.json](IRE_CANONICAL_CURRENT_RESEARCH_STATUS_20261122.json). 기존 V166/V202/V228/V242 등 과거 버전별 기록을 삭제하거나 고치지 않고 **출처로 참조**한다. 본 문서는 판정 규칙을 설명하며 독립적인 두 번째 상태 원장이 아니다.

## 1. 근거 우선권 및 시점

1. 고정 비교 기준 Git HEAD: `6cf0c8859440de11f02ae9e48966322581b59ac3`; 이후 문서/검증 코드 변경은 상태의 실물 승격을 의미하지 않는다. 상태 JSON의 `evidence_sources[*].git_blob_sha`가 실제 Git 파일 바이트 SHA와 일치해야 한다.
2. **상태 차원 구별:** `synthetic_software_route`, `actual_source_structural_host`, `end_to_end_real_owner_approval_route`, `independent_gold_status`, `official_stage_release`는 서로 독립적이다. 과거 합성 실험의 PASS로 실물 E1~E5·정밀도·재현율·적용성을 PASS로 변경하지 않는다.
3. 정식 의미·공식근거·권한·지식 발행을 증명할 새 실물 영수증이 없으면 현재 HOLD를 보존한다. 측정 불가능한 수치는 `null`이며 **명확히 관찰된 0**과 구별한다. 보호 정책 변경은 선행 순차 체크리스트 항목을 PASS한 뒤에만 수행한다.

## 2. 단계별 최신 신뢰 범위

| 단계 | 코드·구조 확인 | ETF 실물 최종 판단 |
|---|---|---|
| E1 | 합성 frozen V6→V123/V127/V128 경로 PASS. ETF 13개 로컬 구조 저장(12개 완결 local+1 B0013 잠정; 78 이벤트) | 전체 실제 승인 경로 HOLD |
| E2 | ETF 250/250 cue source-first 기록, 68개 미승인 후보, 교차원자 21개·연결 49개 보존 | 최종 금융 의미·독립 정답/고위험 누락 HOLD |
| E3 | 검증 계약/합성 시험 존재, 별도 CMA 실제 2턴 기록은 다른 원본 사례 | ETF 실제 정식 V123 **0/13**, HOLD |
| E4 | 원문·시점·권한 검사기의 제한된 합성 시험 존재 | 실물 공식 금융근거·소유자 봉인 HOLD, 승인 자식 0 |
| E5 | 합성 부모 SQLite 단일 커밋·재실행 시험 존재 | ETF 실제 부모 발행 0, 지식 발행 0 |
| 지식 기반 자문 | 레거시 교육 답변 관련 구현 존재 | 현재 법령·E5 지식·개인 적합성 연결 미증명, HOLD |

**중요:** 과거 `V166_E1_E7_STATUS.json`의 E1/E2/E3 PASS는 그 버전의 좁은 시험계약이다. 최신 실제 ETF 전체 지식 승인에 적용하지 않는다. 비공개 ETF 원본의 SHA와 기존 로컬 SQLite 영수증은 기록되어 있지만, **이번 공개 Git 재감사에서 비공개 실물 파일을 열어 재검증하지 않았다**.

## 3. 서로 다른 모집단

| 모집단 | 확인된 수 | 의미 |
|---|---:|---|
| 공식 영상 고유 ID | **791** | 2026-10-07 로스터의 전체 대상 |
| 롱폼 | **703** | 공식 로스터의 주요 연구 범위 |
| Shorts | **88** | 별도 로스터 범위 |
| 영상 등록 원장 `data/videos.jsonl` | **157행** | 레거시 등록·분석 기록, E5 승인 편수 아님 |
| 레거시 `data/claims.jsonl` | **116행** | 이전 주장의 구조 기록, 현행 V6 승인 원자 아님 |
| 학습 큐 `data/learning_queue.jsonl` | **211행** | 역사적 대기열 |
| 이전 `inventory_control.json`의 canonical 시퀀스 | **156건** | 2026-10-07 당시 구형 스냅샷이며 최신 157행과 시점/의미 차이 |
| ETF 실물 E5 승인·발행 편수 | **0편** | 특정 ETF 비교 영상 1편에 한정된 사실 |
| 791편 전체의 실제 E5 승인 완료 편수 | **미확정(null)** | 원본·개인 원장 전수 승인 결과 재검증 전 임의 0 또는 157로 표시 불가 |

과거 1,481 cue의 V149 내부 일부 정답검사 결과 precision 0.8 / recall 0.666667은 **다른 영상/범위의 내부 지표**이며 ETF 250cue 또는 전체 791편의 독립 정확도가 아니다.

## 4. 정책·자동 검사

- 단일 최신 상태 원장 JSON의 근거 파일 14개 경로를 Git blob SHA로 검증한다. `python scripts/ire_current_status_gate.py verify`가 통과해야 한다.
- `python -m unittest scripts.test_ire_current_status_gate`가 PASS/HOLD 과장, 다른 모집단 섞기, 독립 골드·개인 자문 GO 위조를 차단하는 긍정·음성 검사를 수행한다.
- **현재 개발 체크리스트 선행 관문:** [실행 체크리스트](IRE_STRICT_SEQUENTIAL_EXECUTION_CHECKLIST_20261122.md) 및 [상태 원장](IRE_STRICT_SEQUENTIAL_CHECKLIST_STATE_20261122.json). `P0-0-02`를 PASS하여 `P0-0-03`만 열기 전까지 다음 P0 개발 진행 금지. 사용자 작업 시작·종료 보고는 별도 의무다.
- 현재 통합 CI는 GitHub 관리·상태검증 위주이며 **V3/V5/V6/E1~E5 전체 pinned Python 3.11.18 소프트웨어 시험이 아님**. 전체 CI 구축·실행은 별도 `P0-0-04` 과제다.

## 5. 새로운 상태를 확정할 때의 조건

변경 전 실제 비공개 원본·공식 금융 원전·실제 사용자 2턴·owner seal·발행 DB를 **각 해당 단계**에서 다시 재생 검증하고 원자/child/영상별 승인·보류·미확정·격리를 새 append-only 영수증으로 기록한다. 원장 값과 원본 출처가 일치하는 수정만 단일 JSON에 반영하고 검증 스크립트 및 음성시험도 함께 고친다. 실패·증거 부재는 HOLD로 유지하며 **현재 상태 파일 존재만으로 금융 연구·개인 자문 GO를 허용하지 않는다**.
