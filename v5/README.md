# V5 | 투자 지식 기반 비개인화 의사결정 게이트

본 디렉터리는 영상 연구의 근거·규칙·정정·검증 코드만 보관한다. 개인 잔고, 보유 종목, 계좌 코드/번호, 입출금, 소득, 세무원장, 실제 개인 시뮬레이션 결과 등은 **GitHub에 절대 올리지 않는다**.

- [#1~#10 재검토 보고](V5_REVIEW_001_010_20261030.md)
- [122개 주장 V5 감사](reviews/v5_001_010_reaudit_20261030.json)
- [반박 4건과 보안정책](policy/v5_review_policy_20261030.json)
- 검증 `python -B scripts/verify_v5_reaudit.py --root . --self-test`.

원본 SRT 재수집·재해시·원음 재검증 없이 기존 V4 근거로 새 활용성 게이트를 마련했다. L3 개인별 추천/L4 실행은 모두 미승인이다.

## #11 이후: 한 편당 한 턴에서 V5 의사결정 연구 완결

- [자문 수준 연구를 위한 필수 절차](ADVISORY_GRADE_ONE_TURN_PROTOCOL_20261030.md): 원본·주장·공식근거·정량·반례·현실 적용조건 및 OPEN/차단을 같은 영상 연구 턴에 끝낸다.
- [비개인화 작성 규약](policy/v5_one_turn_advisory_research_policy_20261030.json) / [합성 예제](templates/v5_one_turn_synthetic_example.json).
- 신규 영상별 저장 규칙: `v5/videos/v5_NNN_<video_id>_advisory_review.json` (#11부터), 자동검사 `python -B scripts/verify_v5_one_turn_advisory_gate.py --root . --self-test`.
- 한 턴에서 못 얻는 **실제 외부 근거**는 OPEN으로 남기며 완료를 과장하지 않는다. 모듈이 충분해도 개인 맞춤형 L3 및 매매 L4는 별도 비공개 적합성 판단 대상이다.

## #1~#10 V5 근거 제한 연구 마감
[원본 ZIP 재해시·공식자료·10개 정량모형 및 20개 시나리오·미해결 사항 보고서](retrofit/V5_001_010_CLOSEOUT_20261030.md) / [기계 판독 요약](retrofit/summary_20261030.json). 원본 SRT/개인재무자료는 저장하지 않는다. 영상 연구 마감은 실제 개인자문 준비완료를 뜻하지 않는다.

## 외부근거와 비공개 개인 적합성 분리
[공개 근거 검증 및 실제 자문 차단조건](ADVISORY_PUBLIC_EVIDENCE_AND_PRIVATE_GATE_20261030.md) / [공개 출처 원장](evidence/V5_PUBLIC_EVIDENCE_20261030.json) / [개인자료 없는 적합성 입력 규약](policy/v5_private_suitability_contract_20261030.json). 외부 개인 자료와 판단 결과는 GitHub에 절대 저장하지 않는다.

## 새 필수 완료 승인 엔진 — 2026-10-30

- [완결성 계약·운영 지침](RESEARCH_COMPLETION_GATE.md)
- [판정 정책](policy/research_completion_gate_v1.json)
- [#1~#10 미승인 상태 기록](research_completion_001_010.json)
- 실행: `python -B scripts/verify_v5_research_completion.py --root . --self-test`
- #11 이후의 `v5/videos/v5_NNN_<id>_advisory_review.json`은 `v5/completion/v5_NNN_<id>_certificate.json`과 쌍을 이루어야 하며, 원문 연구 결과 SHA256과 주장 ID 전체를 검증한다.
- `RESEARCH_COMPLETE`는 4대 검증영역 모두 통과·중요 미해결 0건·실제 전략 실증·별도 출처심사 조건을 만족할 때만 가능. `RESEARCH_BLOCKED`의 CI 통과는 연구 완료가 아니다.
- 원문·공식자료의 실질적 참·거짓은 GitHub Actions의 구조 검사만으로 인증되지 않는다. 최종 연구 승인 시에는 비판적 독립 근거 심사를 추가 수행해야 한다.
