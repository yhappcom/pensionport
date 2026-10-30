# #1~#10 합성 통합 엔진: 누락·과다후보·원장 판정 교정 재평가

**2026-10-30 · 고정된 10편/122개 주장/38개 선별 진단쌍 기준**

## 재현 명령

```bash
python -B scripts/verify_v5_reaudit.py --root . --self-test
python -B scripts/verify_v5_knowledge_integration.py --root . --self-test --preview
python -B scripts/evaluate_v5_001_010_synthesis.py --root . --self-test --show-pairs
```

입력은 [원본 고정 평가 JSON](benchmark_001_010_v1.json), 평가기는 [재현 가능한 Python 코드](../../scripts/evaluate_v5_001_010_synthesis.py)이며, 이전 진단 결과와 대비하여 변경하였다. V3/V5, 4,120건 교차원장, 16개 대표개념, 12개 잠정 주제 및 원본 주장들의 Git blob SHA는 변경하지 않았다.

## 실제 재평가: 혼동행렬

| 지표 | 초기 벤치마크 | 수정 후 벤치마크 |
|---|---:|---:|
| 총 가능한 주장 쌍 | 7,381 | 7,381 |
| 엔진 후보로 반환된 쌍 | 2,209 | 2,229 |
| 분석자 선별 진단 쌍 | 38 | 38 |
| TP — 관련 후보 탐색 | 27 | 30 |
| FN — 관련 후보 누락 | 3 | 0 |
| FP — 불필요한 후보 | 4 | 0 |
| TN — 비관련 후보 제외 | 4 | 8 |
| 진단 표본 후보 정밀도 | 87.1% | 100% |
| 진단 표본 후보 재현율 | 90.0% | 100% |
| 진단 표본 비관련 제외 특이도 | 50.0% | 100% |
| 오류 주입 차단 | 16/16 | 16/16 |
| 재실행 결정성 | PASS | PASS |
| 자동 의미관계 확정 | 0 | 0 |
| 자동 승인 병합 | 0 | 0 |
| 신규 정식 완결 연구 | 0편 | 0편 |

이 수치들은 **진단 표본에 대해 규칙을 수정한 뒤 같은 표본을 재시험한 재대입(in-sample) 성능**이다. 새로운 영상, 무작위 평가쌍, 전체 7,381쌍, 791편에 대한 일반화 정밀도 또는 실제 의미관계 판정 정확도가 아니다. 선택된 38쌍 모두 자동 의미분류 `ABSTAIN`; 정식 관계 라벨의 올바름을 독립 검증하지 않았다.

### 관련 주장을 놓친 세 사례 (모두 후보 복구)

- `PAIR-07`: #1 ISA 만기·의무기간 vs #2 ISA 목돈 계획. 주제군을 넘는 `ISA_ACCOUNT` 신호.
- `PAIR-10`: #2 지수 ETF 정기매수 vs #3 퇴직 목돈 정기 분할투자. `PERIODIC_PURCHASE` 신호.
- `PAIR-13`: #2 CMA/예금 보호 설명 vs #3 파킹형 ETF 활용. `CASH_PARKING_INSTRUMENT` 신호.

### 과도하게 불러온 네 사례 (모두 후보 제외)

- `PAIR-19`: 월별 가상 예산 배분 vs 연금 세액공제 규칙 (`budget_vs_tax_rule`).
- `PAIR-30`: 일본 초단기 국채 ETF 상품위험 vs 환전 스프레드 (`instrument_vs_conversion_spread`).
- `PAIR-31`: 종목 매도 원칙 vs 집중투자 성공담 (`sale_rule_vs_success_anecdote`).
- `PAIR-38`: 복리 적립기간 계산 오류 vs 국민연금 즉시수령·연기 비교 (`accumulation_math_vs_annuity_delay`).

추가적인 명제 불일치 후보는 원래 폭넓은 영상 연관 신호와 달리 특정 투자행위/상품범위가 실제 문장에서 충돌하는지 검사한다. 범용 자연어 추론으로 간주하지 않는다.

## #6-07 판정 불일치 처리

- **불변 V3:** `3MyhYE2jmuE-07` = `HYPOTHETICAL`; 10년 동안 월 약 18.9만원 유기정기금 증여 예시. 실제 약정·할인율·신고근거·계좌이체 확인 미완료.
- **불변 V5:** 동일 claim ID·타임코드·`HYPOTHETICAL`.
- **원래 4,120건 교차원장:** `QUALIFIED`로 남아 있음. 이 원본 레코드는 소급해서 조용히 변경하지 않는다.
- **신규 보정 기록:** [verdict_reconciliation_001_010_v1.json](verdict_reconciliation_001_010_v1.json)에 V3/V5 Git blob SHA를 고정하여 원래 교차원장 판정은 과거 오류값으로 감사 가능하게 남기고, 누적 통합 비교 시 적용할 **유효 원본 판정 `HYPOTHETICAL`**을 기록.
- **게이트 변경:** `verify_v5_knowledge_integration.py`에서 두 실제 원본을 다시 읽어 변경 없는 해시·claim ID·시각·판정을 확인한 경우에만 보정값을 사용. 불일치하면 CI 차단.

판정 **계보 불일치는 운영상 정합성이 복구**되었으나, V3/V5 원본 이외의 사실관계 및 세무 적용성은 추가 확인이 필요하다. 보정은 새로운 `QUALIFIED` 판정이나 투자 지식의 독립 승인이 아니다.

## 엔진 준비 수준과 남은 검증

- 기존 122/122 주장·영상별 계보 유지; 기존 반박 4건 정정 전용 유지; 12개 잠정 주제의 고유 연결 주장 78개와 독립 보존 44개 유지.
- 기존 통합: 중복 4건 재사용, 충돌 2건 보류, 주제만 유사한 2건 제외, 새 자동 승인 0건.
- 수정된 규칙은 38개 표본에 맞춰 개발되어 **과적합 위험이 높다**. 아직 의미관계를 자동으로 SUPPORT/QUALIFY/CONTRADICTS로 판정하는 엔진도, 논리충돌의 독립 심사·동의 절차도 없다.
- 다음 검증은 수정 시 사용하지 않은 영상의 주장쌍을 독립 심사자가 선정하고, 동일 조건의 precision/recall 및 적용범위 혼동 오류를 전수 기록해야 한다. 그다음 실제 미분석 영상 1편의 수집→근거 보강→정량검증→독립승인→충돌 해소→정식 통합까지 실행해야 한다.

## CI 감사

1차 수정 완성본 GitHub Actions 실행 `41024059118`: 전 단계 성공. 출력에서 `TP=30, FN=0, FP=0, TN=8`, `universe_candidates_retrieved=2229`, `negative_corruptions_rejected=16`, `reconciled_crosswalk_verdict_deltas=1`을 확인하였다.

<https://github.com/yhappcom/pensionport/actions/runs/41024059118>

이후 7개 개별 회귀 주장쌍에 대해 시험 실패를 자동 유발하도록 명시적인 단언문을 추가하였다. 해당 후속 커밋의 CI 통과 상태는 별도로 확인한다.
