# V140.1 — P0-1 정답셋 자기선언 허위 합격 경로 수정

**기준:** 2026-11-16 KST · **변경 위치:** `validation/ire-v6-frozen/v139_p0_qualification.py` (검증·품질 게이트, V6 동결 코어는 변경하지 않음)

## 실결함과 재현

기존 `score_atoms()`는 전달한 JSON에 `complete=True`, `external_independent=True`, `covered_cue_count=720`, 동일한 `source_sha256`과 원자 ID가 있으면 실제 개별 원문 720개 자막의 정답 여부가 인증되지 않아도 TP/FP/FN 및 `p0_1_pass=True`를 계산할 수 있었다. 예: 금표와 예측표에 **임의 원자 ID 1개씩**만 담아도 정밀도 100%, 재현율 100%, 고위험 FN=0 및 가짜 P0 합격이 가능했다.

이는 데이터 유실이나 공개 정보 유출 문제가 아니라 **성능 인증을 잘못 승격할 위험**이다. 사용자가 요구한 전수 원문 재검토·독립 정확도 평가 기준에 부합하지 않았다.

## 수정

- `score_atoms`는 선언된 ID 집합의 산술 중복만 측정하고, `numeric_targets_met_on_declared_units_only`를 별도 표시한다.
- **`p0_1_pass=False`를 유지**한다. 진짜 720 cue 독립 정답셋과 의미 동치·주장 누락 검문이 다른 신뢰 경로로 입증되기 전에는 인증 불가하다.
- `status=DECLARED_UNIT_OVERLAP_ARITHMETIC_ONLY_UNVERIFIED_GOLD`와 `genuine_720_source_gold_authenticated=False`를 추가했다.
- 기존 수학 비교 TP/FP/FN 계산은 합성 테스트/진단용으로 유지하되, 실물 연구 성능 인증으로 전달하지 않는다.

## 재현 검사

- 새로운 회귀 3건: 위조된 1원자/720 cue 정답셋의 허위 P0 PASS 차단, TP/FP/FN 수학값 유지 및 불합격 표시, 동일 채팅의 비독립 정답에서 정밀도 미측정 확인 → **3/3 PASS (로컬)**.
- 기존 V139 품질·승인 차단 회귀시험 **10/10 PASS (로컬)**.
- 기존 V140 실물 원본 감사와 공개 위험·금융 안전검사의 결과를 정식 P0 통과로 승격하지 않았다.

**최종 판정:** P0 NO-GO, V123 정식 승인 0/13, 정식 통합 지식 저장 0건. 이 수정은 원천적으로 무근거한 성능 합격을 막기 위한 방어 개선이지 95%/98% 목표를 충족했다는 증거가 아니다.
