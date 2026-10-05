# vkYOhgHtoOs — 35강: 서킷브레이커

- type: long_form
- content_tag: 곰희스쿨/기초교육
- source_status: indexed course material/public metadata
- knowledge_change: REINFORCE, TIME_SENSITIVE

## 핵심 분석
서킷브레이커는 급격한 시장 변동 때 거래를 일시 중단해 과도한 주문 쏠림과 패닉을 완화하기 위한 시장안정장치다. 장기 투자자에게 중요한 점은 '서킷브레이커 발생=투자전략 변경 신호'가 아니라는 것이다.

## 논리
거래소의 시장안정장치와 개인의 자산배분 규칙은 별도 층이다. 급락장에서 즉흥적으로 전량매도하거나 반대로 무조건 반등을 전제해 과도한 레버리지를 쓰는 행동 모두 기존 투자규율과 충돌한다.

## 시간의존성
발동단계·지수하락률·지속시간·재개 방식은 거래소 규정에 의존하므로 현행 수치는 공식 거래소 자료로 확인해야 한다.

## 프레임워크
시장 이벤트 → 거래소 안정장치 → 개인 포트폴리오 위험예산 → 사전 리밸런싱 규칙으로 분리한다.

## Canonicalization
- canonical_sequence: 134
- canonicalized_at: 2026-10-06
- sync_mode: backlog_compaction_without_reanalysis
