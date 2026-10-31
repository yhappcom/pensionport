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
