# V166 E4 제9차 개선 — B0001 OPEN 3원자 원전 부분근거·과잉승인 차단

**기준 2026-11-18 KST · E1~E3 PASS / E4 FAIL / E5~E7 NOT_RUN / 전체 엔진 NO-GO.**

## 1. 비공개 소유자 원본을 정확히 재검증

비공개 `1-70.zip`의 1번 영상 `5NvtBlmt93Y` 원본 **1,481 SRT cue**, SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`.

동결 V164에 보관한 V163 16원자 `source_input/V163_B0001_16_ATOMS_EXCHANGE.json` 및 `V163_B0001_FROZEN_NATIVE_V123_REVIEW.json`을 동일한 원본 파일과 다시 비교했다. 공개 GitHub에 원문/ASR·동결 검토문을 업로드하지 않았다.

- 원본 16원자·1,481자막 일치, atom별 canonical SHA-256과 동결 V123 verdict SHA 일치.
- `C00002` 원문 cue **30–32 (3개)**; `C00009` cue **98–106 (9개)**; `C00010` cue **107–111 (5개)** 직접 인용 총 **17/17 실제 cue 본문과 일치**.
- 동결 V123 원래 연구분류 **7 ACCEPT_FOR_RESEARCH / 8 OPEN / 1 EXCLUDE_FROM_RESEARCH**, 전체 **CHAT_FINAL_HOLD_OPEN**. 이는 이후 source-only 격리를 반영한 7/3/6 운영상 정리와 다른 버전이며 절대 혼합하지 않는다.
- 비공개 신규 소유자 연구 영수증 `/mnt/data/v166-private/V166_E4_PRIVATE_B0001_THREE_OPEN_PARTIAL_SOURCE_FIRST_20261118.json` SHA-256 **`da8155c73b46b2b1e0cd24e7113712c1a4227ad6dfe1fc78128c246543f06a3e`**. 각 cue·직접 인용은 해시만 남겨 유출 방지, 원자별 추가 미해결 조건을 명시. 이 파일은 배포 저장소가 아니라 비공개 작업 환경에만 있다.

## 2. ChatGPT 출처 우선 실제 의미 검토: 확인된 일부와 미확정 분리

| 원자 | 현재 확인 가능한 제한적 근거 | 결론과 남은 검문 |
|---|---|---|
| `C00002` (원서·한국어 이름 소개) | 실제 영어 원서 출판사 Wiley 보관 HTML SHA-256 `0b444a35f1f3d6a4355188c4dcfd0d7327c00ba73e75e4c6c0cccb1379525bd2`. 원제 `The Dhandho Investor`, 저자 `Mohnish Pabrai`. 2018 한국출판인회의/출판협회 신간목록과 한국 도서 서지에서 `투자를 어떻게 할 것인가`, 저자 `모니시 파브라이`, 역자 `김인정`, 이레미디어, ISBN `9791188279210` 확인 | 출판물 제목·정식 철자만 문헌 귀속 가능. **영상 한국어 자동전사의 고유명사 '바브라'가 실제 발음이었는지 음원 미대조**. 한국 목록은 원저자 영어 표기의 발화 오디오 진위를 인증하지 않음. **OPEN 유지** |
| `C00009` (버핏 주주서한 관련 책들의 범위 주장) | 버크셔 공식 `https://www.berkshirehathaway.com/letters/letters.html` 페이지는 웹 연도별 1977 이후 서한을 노출하며, **1965–2024 전체 미편집 서한을 모은 책**도 소개 | 화자가 특정한 '바이블/선집'의 정식 판본·서지 확인 안 됨. '대부분 자본 증가 후'라는 말은 다른 시기의 서한 수록·시가총액 변화 확인 없이 일반화할 수 없음. **출처 일부는 오히려 포괄적 진술의 반례**. **OPEN 유지** |
| `C00010` (초기 파트너십 규모·운용·공격성·목표) | 제3자 재게시된 **1957 Buffett partnership letter**는 초기 저평가 주식과 특별상황 투자, 투자 비중 조정 및 수익 목표를 보여주는 정황 자료 | 발행인 본인의 원본 서명·바이트 경로 인증이 아닌 **제3자 전사/재게시**. '공격적' 평가, 개별 연도 목표와 실현 수익률, 대담 화자 경계가 독립 검증되지 않음. **OPEN 유지** |

출처 분리:
- Wiley 영문 원본: https://www.wiley.com/en-us/The%2BDhandho%2BInvestor%3A%2BThe%2BLow%2BRisk%2BValue%2BMethod%2Bto%2BHigh%2BReturns-p-9780470043899
- 한국출판 관련 2018 도서 등록 목록: https://member.kpa21.or.kr/wp-content/uploads/sites/2/2018/08/2018%EB%85%84-7%EC%9B%94%EC%9D%98-%EC%8B%A0%EA%B0%84.pdf (서지 보조근거, 해당 PDF 원본 바이트 SHA-256 미인증).
- 제3자 도서 서지: https://www.yes24.com/product/goods/61941283
- 버크셔 회사 공식 원문: https://www.berkshirehathaway.com/letters/letters.html (기존 live CI의 실제 HTTPS byte SHA 증명과 구별).
- 1957 서한 제3자 복제본: https://buffett-letters.com/en/02-letters/partnership/1957-Partnership-Letter (버크셔 공식 원문이 **아니며**, 서명·원본 바이트 인증 **없음**).

## 3. E4 코드 수정 — partial support와 온전한 최종승인을 분리

1. `v166_e4_owner_open_partial_source.py` 신규. 원본 영상 `VerifiedSource`, V6 원자 digest, 정확한 개별 source_ref·cue, 동결 V123의 **OPEN**을 강제. `C00002/09/10`마다 **지원 가능한 제한된 문헌 내용과 지원하지 못하는 중요 구성요소의 고정 목록**을 반환. 원전 역할은 서로 바꿀 수 없고, 재게시 문헌을 공식 버크셔 1957 원본이라고 가장하면 거부. 외부 함수의 출처 검증 여부는 호출자 선언일 뿐 이 함수가 독립 TLS 인증했다고 가장하지 않음.
2. 전수 docket `audit_partial_open_video_census`는 3개 원자 모두 개별 SHA·원래 OPEN·미해결·사용불가 상태를 검문하여 **E4 전체 연구용 지식 발행 권한 False, E5 진입 False**만 반환. 다른 5개 기존 OPEN이 해결된 것처럼 취급할 수 없음.
3. `v166_e4_primary_approval_gate._holding` 및 공식 부모 자식 preflight에 **미승인 원자 전체 ID·OPEN 수·제외 건수**를 직접 추가해 동결 V123 HOLD의 실패 사유를 사용자/검토자에게 알 수 있게 했다. partial evidence가 전체 PASS로 변하는 로직은 없다.
4. `v166_e4_typed_nonstatutory.py`는 주주서한 선집·버핏 파트너십의 검증 가능한 역사적 주장을 **의견/화자 의견으로 위장해 source-only로 승인하는 위험**을 차단. 단일 위험 키워드가 아닌 여러 source_ref 전체 텍스트를 검사한다.
5. `v166_e4_video_book_source_custody.py`는 원래 `context_cue_indices` 범위에만 있으면 통과하던 부적절한 대체 근거를 차단해 **원자가 기록한 실제 직접 `source_refs`의 cue·문장과 일치해야 한다**.
6. **합성 positive/negative CI**: 새 `test_v166_e4_owner_open_partial_source.py` 15개, `test_v166_e4_typed_nonstatutory.py` 역사·서한 위장 추가 2개, `test_v166_e4_video_book_source_custody.py` 주변 인용 대체 차단 1개. 구 V6 테스트 헬퍼는 기본 SRT timestamp 4개라 9cue 생성 시 묵시적으로 5cue가 누락되는 현상을 발견해 새 테스트의 timestamp 9개를 명시했다.
7. 구조 변경 후 전체 GitHub V166 E1~E4 순차 CI 성공을 확인하고, 실패한 선행 개발 중간 CI와 최신 CI를 구분한다. 성공은 **코드 방어 검증**이지 실제 B0001 ChatGPT 전체 신규 승인이나 개인투자 자문 승인 아님.

## 4. 추가 개선의 타당성 및 남은 실패 원인

이번 작업으로 세 원자의 **원문 근거 실체와 외부 검증 범위**가 구체화되었지만 원음 재검토가 없고, 어느 원자도 **V123 최종 PASS**로 변경하지 않았다. 사용자 요구사항에 따라 실제 영상 분석 결과를 임의 승격하지 않는다.

- B0001 실제 8 OPEN 중 이번 3건의 추가 부분근거만 확인했고, **나머지 5 OPEN도 정식 원천 검토가 필요**하다. 기존 7 ACCEPT 후보 중에서도 전체 주장 참임을 독립적으로 승인한 것으로 볼 수 없음.
- 13개 전 구간 V123/E4 승인 및 진짜 사용자 원본의 한 편 지식 원자적 발행은 아직 증명되지 않았다.
- 운영용 signing key·external latest owner pin의 실물 장기 보관과 모든 자문 조회 경로 강제 이행도 미완료.
- **공식 판정 E1 PASS, E2 PASS, E3 PASS, E4 FAIL, E5~E7 NOT_RUN; 전체 엔진 NO-GO**. 실제 신규 승인 지식 0건. `main`, 기존 동결 V123/V126/V128, 비공개 SRT, 포트폴리오는 변경 없음.

**다음 E4 단계**는 B0001 나머지 실제 OPEN의 source-first 의미 검토, 원음이 없을 때의 독립 서지 대조와 ASR 불확실성 보존, 실제 V123 재승인 근거 확보 여부를 명확히 검문하는 것이다. 실제 발행이 불가능하면 원인과 지식 사용 제한을 유지한다.
