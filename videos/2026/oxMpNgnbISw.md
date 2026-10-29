# oxMpNgnbISw — 마켓타이밍 필요없는 마음 편히 할 수 있는 투자 | 자산배분 사용설명서 | ver2026

- published_at: 2026-08-28
- duration: 27:05
- type: long_form
- source_status: public briefing/metadata
- knowledge_change: REINFORCE, EXTEND

## 핵심 분석
자산배분은 단기 시장방향을 반복 예측하는 대신 서로 다른 위험요인을 가진 자산을 목표비중으로 보유하고 정기적으로 리밸런싱하는 접근이다. 영상의 핵심 프레임은 '예측보다 구조'다.

## 구현
투자목표/기간 → 위험예산 → 주식·채권·금·달러 등 자산군 → 목표비중 → 저비용 상품 → 정기 리밸런싱 → 장기유지 순으로 구현한다. 60/40, 영구포트폴리오, 올웨더 등은 서로 다른 위험배분 방식의 사례다.

## 위험
자산간 상관관계는 고정되지 않으며 위기 시 여러 자산이 동시에 하락할 수 있다. 자산배분은 손실을 없애는 전략이 아니라 최대낙폭·행동오류·단일시나리오 의존도를 관리하는 전략이다.

## 숫자 주의
과거 장기 백테스트에서 제시되는 연평균 수익률은 역사적 결과이며 미래수익을 보장하지 않는다. 구체 수치를 현재 기대수익률로 재사용하지 않는다.

## 프레임워크
목표/기간 → risk budget → 자산군 목표비중 → 구현상품 → 리밸런싱 → 장기유지의 핵심 자산배분 contract를 강화한다.

## Canonicalization
- canonical_sequence: 88
- canonicalized_at: 2026-10-06
- sync_mode: backlog_compaction_without_reanalysis
