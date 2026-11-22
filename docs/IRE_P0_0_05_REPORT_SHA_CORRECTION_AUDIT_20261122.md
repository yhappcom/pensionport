# P0-0-05 — 필수 보고 SHA 누락·불변 PASS 규칙 충돌 정정 이력 (2026-11-22)

## 최초 원인과 확인된 차단

- CI [44986059856](https://github.com/yhappcom/pensionport/actions/runs/44986059856)과 [44986194428](https://github.com/yhappcom/pensionport/actions/runs/44986194428)은 P0-0-05를 PASS로 승격했지만 `start_report`와 `end_report`의 필수 `baseline_sha`가 없어 **PASS_MISSING_USER_START_REPORT / PASS_MISSING_USER_END_REPORT**로 실패했다. 이 실패는 보고 형식의 불변 체크포인트 결함이며 E3/E4/E5 금융 연구 결론이 아니다.
- 교정 커밋 `530f242c77730d67e4bbd6cddb3f687abff64eb7`에서 시작·종료 보고 SHA를 각각 실제 기준 HEAD `dd9bf7fc8d6645ee4fac93e20e84cffb8d486358`, 시험 완료 HEAD `7711fb3216bc5c91ea3c302fabc39a48eef86fdf`로 보충했다. **이 교정 자체도 CI 44986267762에서 `PREVIOUS_PASS_MUTATED:P0-0-05`로 RED**를 기록했다. 이미 PASS였던 항목 내용이 바뀌었음을 보안 관문이 올바르게 감지한 것이다.

## 실증 안전 절차

1. `scripts/ire_checklist_gate.py`의 `PREVIOUS_PASS_MUTATED`, `good_report`, 선행 순차 차단 및 `--compare-parent` 코드는 **약화·삭제하지 않는다**.
2. 누락 SHA가 생겼던 기존 잘못된 PASS 커밋과 차단 로그를 Git 이력에서 그대로 보존한다. 교정된 상태 원장 SHA는 위 `530f...` 커밋부터 고정하고 더는 변경하지 않는다.
3. 별도 신규 소프트웨어 음성시험은 사후에 잘못된 PASS 보고의 SHA 필드 두 개를 보충할 때에도 불변 PASS 검사에서 RED로 차단된다는 사실을 고정한다. 즉 과거 보고의 무증빙 편집 허용이 아니다.
4. 다음 GitHub Actions는 **체크리스트 상태 원장에 어떤 변경도 없는 새 커밋**에서 관리 정책·P005 24개 이관 검증·엄격 V3/V5/V6 및 E1~E5 전 시험을 재실행한다. 그 최종 커밋의 전 작업 PASS가 확인되기 전에는 P0-0-05 종료 보고와 P0-0-06 실작업 착수를 완료로 간주하지 않는다.

### 한계

`--compare-parent`는 **직전 한 커밋 대비 변경만 검사**하므로 과거의 모든 커밋에 대해 같은 검사가 자동으로 소급 적용되는 것은 아니다. 따라서 RED/해결 영수증과 SHA 계보를 감사 증거로 영구 보존한다. 체크리스트 현재 상태는 `5/60 PASS / P0-0-06 READY`이지만 E1~E5 실물 금융 승인은 여전히 HOLD다.
