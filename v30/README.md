# V3.0 통합 연구 엔진

**작업 시작:** 2026-10-31 · **현재 상태:** 연구 아키텍처 계약 + 검증 가능한 초기 실행 기반, **운영 BLOCKED**.

[V3.0 통합 아키텍처·구현 계획](ARCHITECTURE_AND_DELIVERY_PLAN_20261031.md)에서 모든 모듈의 역할, 기존 연구 재활용 기준, 구현이 끝나지 않은 부분, 출시 게이트를 구분한다.

## 실행 가능한 시작 구성

| 파일 | 책임 |
|---|---|
| [엔진 계약](contracts/integrated_engine_v1.json) | 8단계, 입력 주장 계약, 증거 필수조건, 기존 코드 보존, 승인 금지 |
| [독립 평가 계약](contracts/evaluation_protocol_v1.json) | #1~#20 개발 / #21 이후 미사용, 독립 블라인드 심사·표본·성능 목표 |
| [실행 엔진](../scripts/v30_integrated_research.py) | 4,120개 역사 주장·39개 가족 검증, 주제별 읽기전용 검색, #19·#20 출처 고정 연구 의무, 명시적 금융 역할 비교, 숫자 산식 |
| [적대적 검증](../scripts/verify_v30_integrated_research.py) | 원본 해시·출처·주제별 후보·기초 정량모형·정정격리·미사용 영상 접근 차단 |
| [GitHub Actions](../.github/workflows/v30-integrated-research-gate.yml) | 위 코드·원본 V5 완결성 관문·개인자료 부재를 전수 자동검사 |

```bash
python -B scripts/v30_integrated_research.py --root . --validate-baseline
python -B scripts/v30_integrated_research.py --root . --prefilter-family ISA_PENSION_TRANSFER --limit 15
python -B scripts/v30_integrated_research.py --root . --plan-development-video 19
python -B scripts/v30_integrated_research.py --root . --plan-development-video 20
python -B scripts/verify_v30_integrated_research.py --root .
```

`--prefilter-family`는 명시적으로 입력된 **역사 주제군**으로만 읽기전용 후보를 반환한다. 주제 일치는 의미 동일성이나 금융 사실의 증명이 아니다. 반환된 과거 `CONTRADICTED` 주장은 정정 전용이며 자동 병합 금지.

`--plan-development-video`는 **과거 검증에 이미 노출된 #19 또는 #20만** 허용한다. 역사 V3 핵심 주장 12/6개를 모두 `BLOCKED` 연구 의무로 작성하며 원본 사용자 SRT/원음 재검증, 신뢰 가능한 전체 원자화, 최신 법령·계약·실증 자료 검증을 했다고 주장하지 않는다. #21 이후는 명령으로 열지 못한다.

`compare_explicit_frames`는 **개발 중인 저수준 순수 비교 함수**다. 사람이 제공한 프레임과 주장 ID를 구조적으로 검사하지만 별도 원본 저장소 조회·독립 검토자 인증까지 이 함수 자체에서 수행하지 않는다. 반환값에 이러한 미인증 한계와 자동 승인 금지가 명시돼 있다. 완성된 관계 승인 API가 아니라 다음 단계의 출처 결합과 인간 심사를 기다리는 중간 모듈이다.

**다음 구현 게이트:** 안전한 원본 SRT 전구간 수집·원자화 증명, 금융 명제 구조화 검토, 공식자료 실제 문맥·발효일 검증, 정량과 공개 실증 데이터 재현, 전체 지식 의미 검색, 독립 관계 검토, V5 완료 인증 + append-only 통합 어댑터를 하나의 재현 가능한 파이프라인으로 연결. 이 기능이 모두 검증되기 전까지 새 영상 연구를 엔진에 위임하거나 운영 승인을 선언하지 않는다.


## 심층 독립 검토 — 2026-10-31

[심층 감사 보고서](audits/V30_DEEP_ENGINE_AUDIT_AND_REDESIGN_20261031.md), [재현된 결함 증거 10건](audits/v30_deep_findings_v1.json), [읽기 전용 적대적 감사 코드](../scripts/audit_v30_deep_readonly.py).

현재 **P0 구조·운영 차단사항 3건**과 **P1 중요 설계결함 7건**을 확인했다. 시험 성과의 PASS는 취약점 존재를 재현한 감사기가 성공했다는 뜻이며, 프로덕션 연구 엔진 승인 결과가 아니다. 특히 보호 목록 자체를 지울 수 있는 정책검사 허점, 출처 미인증 비교, 수치 문자열 오판, 모든 단계의 실제 증거·통합 실행기 미구현을 기록했다.

감사 동안 V3.0 엔진 원본 Git blob 7924ad51058abc1129eef2ec91df97589b412f63은 수정하지 않았다. 기존 4,120개 연구 원장과 main도 변경하지 않았다. 이 결함을 변경·수정하기 전 G0~G7 수용 기준을 먼저 고정하고, 실제 동결 엔진·검색 인덱스·독립 검증 데이터를 분리해 평가하도록 권고한다. 운영 승인 **BLOCKED** 유지.

## V3.0 실행 파이프라인 보완 — 2026-10-31

[전체 구현 내용·8단계 모듈 대조 및 실제 운영에 필요한 근거](FULL_PIPELINE_IMPLEMENTATION_AND_REMAINING_GATES_20261031.md).

**현재 개발용 실행 진입점:** [v30_research_pipeline.py](../scripts/v30_research_pipeline.py). 최초 [v30_integrated_research.py](../scripts/v30_integrated_research.py)는 기존 취약점 재현·역사 출처 스모크 테스트용 **동결 초기 프로토타입**이며 신규 실제 연구에 단독 적용하지 않는다.

- [원본 SRT·금융 명제·출처 검증](../scripts/v30_verified_core.py), [자막 전구간 원자 주장 후보 추출](../scripts/v30_claim_extraction.py)
- [공식자료·재무계산·실증 CSV 검증](../scripts/v30_evidence_services.py), [한국어/금융 역할/주제/선택적 임베딩 검색](../scripts/v30_hybrid_search.py)
- [8단계 승인 불변 상태기계](../scripts/v30_state_machine.py), [V5 BLOCKED 인증·지식통합 검토대기 이벤트](../scripts/v30_v5_bridge.py)
- [원본·공식자료·의미 검색·V5 통합의 통합 적대적 테스트](../scripts/verify_v30_full_research.py), [외부 블라인드·진단 표본 분리 평가기](../scripts/v30_independent_evaluator.py), [브랜치 원장 보존·개인정보 검증](../scripts/verify_v30_repository_safety.py)
- [#19 원본 비공개 SRT를 포함하지 않은 역사 출처 manifest](examples/019_readonly_source_manifest.json).

**제한:** 실제 외부 공식 증거·독립 심사자·원본 전체의 최종 검토·진짜 미노출 신규 성능 자료는 이 브랜치에 확보되지 않았다. 따라서 모든 신규 지식/매매 자동 승인은 0건이고 운영은 **BLOCKED**. CI의 합성 테스트 성공은 실제 금융 사실검증 완료가 아니다. #21 이후 신규영상은 개발코드에서 접근을 차단한 상태다.


**코드·계약 동결:** [V3.0 전체 12개 소스/계약 Git blob 고정 원장](contracts/v30_development_freeze_20261031_v1.json). GitHub CI에서 47개 개발 시험과 이 원장을 함께 검사한다. 외부 독립 블라인드 시험을 통과하기 전 신규 원본 동영상 분석·운영 승인은 계속 금지한다.


## #1~#5 실제 SRT·기존 V3/V5 독립 재실행 (2026-10-31)

[재실행 종합 보고](validation/V30_001_005_INDEPENDENT_REPLAY_20261031.md) · [원본 SRT 바이트를 제외한 로컬 원본 검증](validation/retro_001_005_local_source_replay_v1.json) · [예측 전 등록 44개 관계 평가쌍](validation/retro_001_005_diagnostic_cases_v1.json) · [V2.3/V3.0 비교 전체 예측](validation/retro_001_005_replay_result_v1.json).

실제 #1~#5 SRT 5,129구간과 기존 62개 핵심 주장의 계보가 일치하고 V3.0 원자 후보가 7,054건 생성되었으나, 의미 검토는 완료되지 않았다. 두 검색기의 44쌍 개발 진단에서 V3.0 정밀도·재현율 모두 75%, 기존 V2.3은 정밀도 94.4%·재현율 70.8%. 이 결과는 비블라인드 후향적 진단이며 V3.0 의미 검색 개선 또는 신규 실전 성능의 증거가 아니다. 명목 연이율과 실효 연이율 모델 차이도 별도 결함으로 기록했다. **운영 BLOCKED 유지**.


## V3.1 → V3.2 결함 수정·첫 사용 성능검증 결과 (2026-10-31)

[분리 검증 종합 보고](validation/V31_V32_CORRECTIONS_AND_SEPARATE_HOLDOUT_20261031.md) · [실제 #61~#65 첫 사용 실패 결과](validation/v31_061_065_realcohort_result_v1.json) · [실제 #66~#70 첫 사용 실패 결과](validation/v32_066_070_real_firstuse_result_v1.json) · [V3.2 최종 릴리스 차단 원장](contracts/v32_release_gate_after_66_70_v1.json).

기존 92개 관련·무관 쌍을 참고한 개발 검사는 92/92 일치했지만, **이후 분리한 기존 실제 영상**에서 V3.1 재현율은 8/24(33.3%), V3.2 상위10 검색 재현율은 5/24(20.8%)다. 두 실제 집합 모두 프로젝트 역사 지식원장에 이미 포함됐고 외부 블라인드 심사가 없으므로 완전 미노출 성능검증은 아니다. 금융 명제 유형을 아직 충분히 추출하지 못한다. 기존 V3.0/V2.3 및 V5 자동지식통합관문은 동결, **V3.1·V3.2 운영 승인 BLOCKED**, 자동 지식병합 0건. 다음 실제 신규 영상의 자동 연구를 진행하지 않는다.
