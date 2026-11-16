# V116 — P0-1 의미 분해 → P0-3 현행 금융근거 → P0-2·P0-4 복구/계측 → P1 읽기전용 지식 연결

기준: **2026-11-14 KST**. 연구용 검증 브랜치 `verify/ire-v6-p1-atomic-host-batch-20261109` 전용. `main`, 기존 Master116·P4·V5 지식, V115 영수증은 **변경하지 않는다**. 이 파일은 소유자 비공개 원본의 SHA·건수·검문 결과만 기록하며, 사용자 자막/비공개 의미 주석을 공개하지 않는다. 전체 투자 연구 또는 독립 품질 인증 **NO-GO**.

## 1. 원본과 V115 대비 실제 새 연구

- `1-70.zip` 원본 SHA-256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`, #영상 `7RRWNL0V6As` SRT SHA-256 `4515d3446c4874d3a376d86b1dd46ab89446e992911b0d42b52aa0df5ffb3c83`을 다시 검사했다.
- 원본 **152/152 cue**는 V115의 20개 담화 부모·29개 잠정 의미 단위에 계속 연결된다. **원본 귀속 100%는 의미 주장 재현율 100%와 동치가 아니다.**
- 이 약점을 겨냥해 ChatGPT 단일 채팅에서 원본 152개를 재검토하고 **16개 복합 주장/반박/예외 검문, 총 36개 세부 의미 측면(facet)**을 추가 작성했다. 서로 중복된 원천 근거도 있으므로 36개는 서로 독립적인 새 승인 금융 주장 수가 아니다. 16개 검문은 원본 **135개 고유 cue 위치**를 참조하고, **9개는 여러 V115 부모/주장을 연결**, **고·매우 높은 위험 11개**다. 16개 검문 전부 출처 SHA·화자/검토자 구분·OPEN을 다시 검사했다.
- 핵심 발견: (1) 소수점 편입주식 소유와 ETF 분배금 수령의 질문/설명, (2) PR/TR **수익률지수 산식 vs ETF 실제 분배정책**, (3) 미지급 이익의 **NAV 반영 vs 시장가격 상승**, (4) 기업/ETF의 **변동 분배액 vs 전액 지급 주장**, (5) 분배락 **기준가격 조정 vs 실제 매매가격·결제/세금**, (6) ETF 좌당 가격 **vs AUM vs 총수익**을 반드시 분리해야 한다.
- 특히 cues **67–68, 84–86**에 반복된 TR ETF 전면 소멸 일반화는 **원본 발화로서 보존**하면서 **검토자가 만든 현행 법령 예외**를 별개 `REVIEWER_EXCEPTION`으로 기록했다. 의미상 정정을 원래 화자의 확정 발언으로 바꾸지 않았다.

## 2. P0-3 현행 금융규정: 교차 검토했지만 원문 실물 인증은 미완료

- 현행 소득세법 시행령 **제26조의2**, 법령 검색 결과상 **2026-10-01 시행**(대통령령 제36737호, 2026-09-30 일부개정). 2025-07-01 이후 발생한 이자·배당 관련 TR ETF 분배 방식 변경과 국내주식형 TR ETF의 **분배유보 예외**를 구별한다.
- 법령정보센터를 2026-11-14 직접 조회하니 11월 13일 21:00~14일 21:00 **시스템 점검 페이지**로 이동했다. `official_body_bytes_verified=false`, `original_law_html_sha256=null`이며 법령 검색 **색인/캐시** 조회를 공식 HTML 원문 바이트 SHA 재검증이라고 주장하지 않는다.
- PLUS ETF 공지(2025-06-24), RISE ETF 공지(2025-06-23)는 검색 색인으로 내용·출처를 확인했으나 Firecrawl 직접 재방문은 실패했다. 따라서 별도 `ISSUER_NOTICE_SEARCH_INDEX_ONLY`, `raw_source_body_sha256=null`로 기록했다.
- V115의 기존 **금융 교육/사실 후보 26건은 전부 OPEN 보존**. 이번 16개 복합 주장에는 각각 금융근거 또는 명시적 `NO_DOCUMENT_SOURCE_OPEN`을 한 개씩 매핑했다. 법령/운용사/거래소 출처 포인터 **4개**는 출처 분류상 연결됐으나 개인 계좌/ETF 실물/원음·원화면/원문 바이트 인증 및 새로운 금융 사실 승인은 0이다.
- 직접 대조 출처 포인터: [국가법령정보센터 제26조의2](https://www.law.go.kr/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1001063330), [PLUS ETF 공지](https://www.plusetf.co.kr/customer/notice/detail?n=29585), [RISE ETF 공지](https://www.riseetf.co.kr/cust/notice/123?page=1), [KRX ETF 분배 설명](https://regulation.krx.co.kr/contents/RGL/03/03060101/RGL03060101.jsp).

## 3. P0-2 연속 실행과 P0-4 성능 계측: 측정·복구 범위를 분리

- **사전에 현 채팅이 검토·작성한 V115 원장 + V116 잠정 의미 분해 + 조건부 근거표 + 이전 지식 관계**를 실제 비공개 파일에서 읽고 5단계 `SOURCE→SEMANTIC→FINANCE→METRICS→KNOWLEDGE`에 연결하여 SHA 체인/SQLite 체크포인트 **5/5**를 생성했다.
- 동일 자료로 재실행하면 **새 이벤트 0건**(멱등). `SOURCE+SEMANTIC`까지 저장된 별도 작업의 재실행은 **남은 3단계를 이어서 기록**. 저장된 의미 분석 내용을 무단으로 바꾸는 재시도는 거부했다. SQLite `integrity_check=ok`.
- 실물 검문의 로컬 `perf_counter_ns` 결과는 공개 SHA 영수증 `measured_local_stage_wall_ns`에 있다. 분리된 `source_original_replay_and_semantic_challenge_audit_ns`, `official_pointer_scope_audit_ns`, `historical_readonly_candidate_audit_ns`, `full_local_validation_ns`는 **소프트웨어 검사시간**이며, ChatGPT가 새 의미를 이해·작성하는 시간은 포함되지 않는다.
- `chat_model_semantic_inference_ns`, `law_site_live_fetch_ns`, `original_audio_video_resolution_ns`, `independent_gold_decision_ns`는 전부 **null**. Python 자체에서 ChatGPT 모델을 API 없이 무인 호출·계속 실행하는 기능은 없다. `model_calls_automated=false` 유지. 791편 완성 기한 예측은 불가하다.

## 4. P1 기존 지식 통합 — 실물 GitHub 읽기·후보 연결만 수행

- GitHub 보호 `data/claims.jsonl` 원본 Master116 Git blob `ab5af7eea02e65d5e36174546a2a94f4cc642d92`, 기존 P4 22개 원장 Git blob `bfb446ffb1dd40caa1ed03088d088c9a1ba7490f`를 읽어 관련 기존 ID를 확인했다.
- 이번 영상에서 실제 구간에 출처가 있는 주제 관련 **잠정 후보 11건**을 이 두 집합의 관련 ID 5개(`GOMHEE-C17`, `GOMHEE-C24`, `GOMHEE-C34`, `EDU-ETF-NAV-TRACKING`, `EDU-ETF-TOTAL-COST-DECISION`)와 **읽기 전용**으로 연결했다.
- `TOPIC_RELATED_PENDING`은 문맥 관련성일 뿐, 원자 주장 동치/지식승인/금융 법령 적법성 인증이 아니다. 각 후보 ID·근거 자막·원본 SHA·비공개 설명은 소유자 복구 ZIP에만 둔다.
- V75 **404건의 원장 ID 자체는 복구되지 않았다**. V78~V80의 그림자 자료는 `v75_membership_verified=false`이므로 V75 정식 복원이라고 계상하지 않는다. 과거 전수 중복 제거 및 지식 병합 **0건** 유지.

## 5. 구현과 회귀·산출물

- `v116_semantic_finance_integration.py`: 원본 SRT → V115 원장 완전성 → 16개 세부 의미/화자 반박·법령 예외 SHA 대조 → 규정·발행사 출처 분기 → 기존 지식 관계 제한 → 시간계측·공개 결과 검문. 원문은 **메모리 내에서만 처리**, 공개 결괏값은 SHA와 건수만 반환.
- `test_v116_semantic_finance_integration.py`: 원본 수정, 부모 연결 재지정, 세부 주장 누락, 화자/검토자 바뀜, 법령 전면소멸 위조, 법령 시행일 변조, 공식 URL 가장, 분배 화면 누락, V75/116/22 거짓 지식 승격, 가짜 독립 재현율, 임의 모델 계측, 체크포인트 장애 등 적대적 합성 테스트 **50개**를 로컬 실행해 전부 통과. GitHub CI 결과는 최종 SHA에서 별도로 확인한다.
- 비공개 소유자 복구 ZIP: V116의 16개 검문·36개 의미 측면, 현재 법령 출처 포인터, 11개 이전 지식 연결, 실물 원본 검증 스크립트·SQLite 이벤트 원장을 보관. 원본 SRT와 개인 원장을 GitHub에 올리지 않는다.

**최종 진척:** P0-1의 복합 주장 누락 탐지·원문-반박 분리 개선 실증, P0-3의 실효일/예외 처리·현재 공식 색인 대조, P0-2의 5단계 복구, P0-4의 CPU/검문 시간 분리, P1의 기존 원장 읽기전용 후보 연결을 수행. 그러나 독립 **precision/recall/high-risk-recall = NO-SCORE**, 공식 최신 HTML 바이트·원음/화면 검증 미완료, 실제 ChatGPT 무인 자동 호출 미구현. `p0_go=false`, `research_complete=false`, 신규 금융지식/개인 자문 자동 승인 0건.
