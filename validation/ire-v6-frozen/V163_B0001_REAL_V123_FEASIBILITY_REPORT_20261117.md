# V163 — B0001 16개 원자 원문 우선 재검증 및 최종 V123 승인 가능성 판정

**2026-11-17 KST · 영상 #1 `5NvtBlmt93Y` · 기존 승인 Master116/P4 / main / 포트폴리오 변경 없음**

## 실물 원본·호스트·금융근거 확인

- 소유자 SRT 원본 1,481개 자막 SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`, B0001 자막 1~120번 전수 재검토.
- 기존 B0001 잠정 15개 원자에서 자막 5번의 **투자 확신에 관한 질문**이 `NO_ATOM` 처리된 실제 누락을 찾아 **C00293 QUESTION 추가**, B0001 16개로 수정. 다른 12개 구간과 기존 승인 원장은 보존.
- 새로운 B0001 실제 V6 `submit_host_atomic_batch` 성공, 멱등성 재실행·SQLite 무결성 통과. 최종 이벤트 SHA-256 `b37643f6e3f14db7be1bde31985a13b4d0530d3899f2a6bb3481f3b8eb241141`.
- 출판사 원문 HTTPS 바이트 확인:
  - Wiley 영문 원서/저자 소개 HTML 61,883 bytes, SHA `0b444a35f1f3d6a4355188c4dcfd0d7327c00ba73e75e4c6c0cccb1379525bd2`, https://www.wiley-vch.de/en/areas-interest/finance-economics-law/finance-investments-13fi/investments-securities-13fi3/the-dhandho-investor-978-0-470-04389-9
  - Wiley 1장 발췌 PDF 277,191 bytes, SHA `870be11899036a19351d1ce8644f833748e9b9618d67233d6a0c162144397024`, https://catalogimages.wiley.com/images/db/pdf/9780470043899.excerpt.pdf
  - 한국어 공공도서관 서지 실제 HTTPS 바이트 확보 시도는 `HOLD_HTTP_OR_CONTENT`; C00002 정식 승인 보류.

## B0001 원자별 실제 V123 판정

- 원본 120 cue + B0001 16개 원자 모두 source-first 심사 기록이 있음.
- **7 `ACCEPT_FOR_RESEARCH`**: 기존 4 + 신규 **C00007**(저자가 책에 쓴 Dhandho 어원 설명), **C00008**(책이 소개하는 제한적 손실/비대칭 전략이라는 *서술*), **C00011**(Wiley 저자 소개의 Buffett Partnership 모델). 투자 수익률·손실 보증 또는 법적 개인 자문 진실 인증이 아니라 **원문 귀속이 확인된 제한적 연구 후보**다.
- **1 `EXCLUDE_FROM_RESEARCH`**: C00012 저자 자산순위 추측. 실제 원문은 보존하면서 객관적 순위/기준 시점·원전 미확보로 연구 지식에서 출처 고정 격리. 범용 OPEN 일괄 제외 아님.
- **8 `OPEN`**:
  - C00001: 큰 비중으로 투자했다 손실이 생겼을 때 어떻게 하느냐는 *질문*; 사실 검증과 발언 확인의 증거 유형 구분 필요
  - C00002: 한국어 도서 제목/저자; 국내 서지 원문 응답 바이트·ASR 철자 확인 필요
  - C00003: 투자에 사업 관점을 적용하자는 *제안*; 발언과 전략 효용/개인 적합성 혼동 금지
  - C00009: 버핏 주주서한을 엮은 책에 대한 과도한 범위의 서술; 원서 편집 범위 별도 확인
  - C00010: 초기 Buffett Partnership 운용액·성과 관련 역사적 주장; 해당 연도 원서한과 숫자 교차검증 필요
  - C00277: 낮은 가격/안전마진의 손실 감소 *조건부 가설*; 결과나 보장으로 승격 금지
  - C00285: 화자의 개인 독서 난이도 *의견*; V161의 source-only는 발행 권한 없음
  - C00293: 새로 복구한 투자 확신의 의미에 대한 *질문*; 질문 사실과 객관적 금융 사실 구분 필요

이 **8개 중 금융 관련 발화/의견/가설 범주 5개(C00001·C00003·C00277·C00285·C00293)**를 기존 V123의 `_is_finance` 어휘 하한으로 현행 금융 법규나 시장 사실처럼 검증하는 것은 부적절. 나머지 **3개(C00002·C00009·C00010)**는 실제 출판 원전/버핏 원서한·비교자료가 더 필요하다. 임의 원자 일괄 격리나 모호한 출판 페이지로 승인하지 않았다.

## 최종 구조적 승인 조건과 결과

- 새 V6 호스트로 실제 V123 심사: **B0001 7 수용 / 8 OPEN / 1 격리**, `CHAT_FINAL_HOLD_OPEN`; `require_chat_final_release` 실패-폐쇄 통과.
- 실제 V127.1 13 child checkpoint는 **13 HOLD**. V128 반환 `HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE`; SQLite 확인 지식/이벤트/부분발행 **0/0/0**.
- 영상 #1 전체 실물 집계: **잠정 293 원자, 50 제한적 연구 후보 수용, 242 OPEN, 1 격리, 127 금융근거 OPEN, V123 PASS 0/13, V128 신규 발행 0**.
- 여전히 B0001 기존 V123의 `unresolved_high_risk_omissions=12`와 `disagreements_adjudicated=false`; 리포트 `high_risk_open=20`은 OPEN 8+종전 고위험 누락 카운터 12의 합성치이며 실제 고위험 오류 20건 증명이 아님.
- 독립 블라인드 gold와 실제 정밀도 95%·재현율 98%, zero high-risk FN 인증 없음.

**승인 가능성 판정:** *동결된 현행 V123 그대로라면 B0001 전체 PASS 불가능.* 출판 원전 확충으로 역사적 사실 3건은 해결할 수 있으나, 질문·의견·조건부 가설 다섯 건을 오직 현행 금융 1차 원문 바이트/시행일로 검증하려는 계약을 보완해야 한다. 버전 분리형 **V123 차기 typed final semantic release**를 별도로 설계·실증하되 이전 동결 코드/역사적 SHA/고위험 누락 제약은 유지한다. V128의 13개 구간 all-or-nothing 발행 금지를 풀거나 임의 PASS를 생성하지 않는다.

## 원본 보관과 재현성

- 소유자 비공개 원문/원자/ChatGPT 개별 리뷰/13 child hold/실제 V128 knowledge SQLite 포함 ZIP: `V163_PRIVATE_B0001_16_ATOMS_7_ACCEPTED_8_OPEN_NATIVE_HOLD.zip`, SHA-256 `7b5469cfe0cd73126f8e32499f657f3e23b70d7fd428c9bc3ad43c702bb738d1`. 전체 1,481 cue SRT는 기존 소유자 원본 ZIP으로 연결.
- 개별 원문 바이트/호스트/13 child/SQLite를 독립 *기계적* 읽기 전용 재검증한 JSON SHA-256 `69cde60f2b9fc5296390530bac5760168f64b1225e63382a49d56a16957d224d` (독립 정답셋이나 모델 품질 인증 아님).
- GitHub에는 공개자료 원문/원자 문장/소유자 SRT/개인정보/비공개 원장 등을 올리지 않음. `main` 수정 없음.

**최종 실증: B0001의 개별 OPEN 12개는 정식 원자별 판정/사유 기록으로 검문 완료. 최종 B0001 승인 0, V128 0. 안전하게 승인할 수 있는 근거를 더 모으되 V123 구조적 의미 분류 계약 보완 필요.**
