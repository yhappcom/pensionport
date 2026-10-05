# lqTJB2NXSKg — 포트폴리오 관리 기능이 있는 앱을 찾았습니다!! | 내돈내손 앱리뷰 | FunETF

- type: long_form
- content_tag: app_review / non_advertisement
- source_status: official video description + service feature records; partial-source
- knowledge_change: EXTEND, TIME_SENSITIVE

## 핵심 분석
영상 설명에서 박곰희는 콘텐츠 제작 시 투자정보를 확인하기 위해 기존 '펀드솔루션'을 사용해 왔고, 포트폴리오 관리 기능이 있는 서비스로 소개한다. 투자 앱의 역할은 종목을 대신 골라주는 것이 아니라 여러 ETF·펀드를 비교하고 자신이 정한 포트폴리오의 비중과 성과를 추적하는 실행보조 도구다.

## 확인된 기능
당시 펀드솔루션 계열 서비스는 국내 운용사의 펀드·ETF 정보 비교, 분배금 정보, 투자 콘텐츠, 직접 포트폴리오 구성과 성과 확인 기능을 제공했다. 이후 서비스는 FunETF로 명칭/서비스가 이전되었고, 현재 공개된 FunETF 프로젝트 설명도 ETF 랭킹·구성종목 검색·필터검색·분배금 정보·포트폴리오 생성/관리 기능을 명시한다.

## 투자 프로세스상 의미
앱 → 투자전략 순이 아니라 목표/자산배분 → 필요한 상품정보 → 포트폴리오 기록 → 비중 이탈 확인 → 리밸런싱의 순서다. 도구가 편리해도 투자판단의 책임과 원칙은 사용자에게 남는다.

## 위험
앱 이름·운영주체·기능·가격·데이터 범위는 TIME_SENSITIVE다. 실제로 기존 펀드솔루션은 종료되고 FunETF로 이전되었으므로 과거 영상의 앱 상태를 현재 서비스로 그대로 이해하면 안 된다.

## 프레임워크
목표비중 → 구현상품 → 기록/모니터링 도구 → 비중점검 → 리밸런싱이라는 portfolio-observability layer를 추가한다.

## Canonicalization
- canonical_sequence: 123
- canonicalized_at: 2026-10-06
- sync_mode: backlog_compaction_without_reanalysis
