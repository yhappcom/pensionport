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
