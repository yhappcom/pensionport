# V166 E4 네 번째 개선 — 원문-원전 의역 의미계약·봉인 검증 조회·B0001 반례

**2026-11-17 KST · 사용자 확정 E4 판정: FAIL (개선 진행, E5 NOT_RUN).**  
**실제 사용자 B0001에는 정식 V123 최종 승인/발행을 신규로 기록하지 않았다.**

## 1. 기존 정확 원문 인용만 허용하던 E4의 구조적 한계 보완

신규 `v166_e4_semantic_entailment.py`, `v166_e4_primary_approval_gate.py` 연결:

- 원문 영상의 금융주장이 공식 자료의 문구와 **완전히 동일하지 않아도**, ChatGPT가 **원자 ID·원문 source_ref cue·cue SHA/전체 문맥 SHA·원자 SHA·V123 chat-review SHA·공식 HTTPS 실제 원문 SHA·원문 속 인용구·시행일**을 한 묶음으로 검문한 **조건부 의미 지지** 증빙을 제출할 수 있도록 함.
- `EXACT_PRIMARY_QUOTE`에는 의미 증빙을 섞지 않고, `CHATGPT_CUE_TO_PRIMARY_ENTAILMENT`만 강화된 계약으로 처리. 미검증 의역은 거부.
- 원자 원문 발언의 숫자/비율/단위를 개수까지 전수 대조: `10%`와 `8%`가 뒤바뀌거나 퍼센트가 금액 단위로 재분류되면 차단. **영상이 말하지 않은 적용연도를 공식자료 시행일에서 역으로 만들어 원문 주장에 덧씌우는 경우도 차단**. 발언에 연도가 명시된 경우 양쪽 원문에 그 연도가 실제 있어야 함.
- 조건·예외 자막 cue 인덱스 그대로 보존, 공식 원전의 조건·예외 인용 문장도 **다운로드된 원전 바이트에 실제 존재하는지 검사**. 문맥이 `CONDITIONAL`, `CORRECTED`, `QUESTION` 등인 원자가 무조건 사실로 변경되면 거부.
- 검토자 판단은 `CHATGPT_IN_CHAT`로 명시, 이견·반례·조건·적용시점 검토 기록과 개별 note SHA 요구. 자동 최종 법령진위, 외부 독립 gold, 개인자문 승인은 항상 False.
- **중요한 발견:** 기존 E4 원문 인용 인덱스는 원자의 `context_cue_indices`에만 속하면 인접 **다른 원자의 발화**도 같은 주장의 직접 근거로 쓸 수 있었다. `source_refs[].cue_index`에 해당하는 실제 원자 직접 인용으로 조건을 강화. 관련 합성 회귀 성공.
- **E4 합성 양성/음성 회귀:** 기존 가짜 문서가 아니라 **실제 V123/V6 검증 코드+모의 공식 HTTPS 본문**으로 정상 의역 3원자 연구후보 PASS 및 누락·변조 반례 차단. 공식 금융법 실물에 대한 ChatGPT 의미 판정의 정확성을 독립 인증한 것은 아님.

## 2. E4 인증 지식 조회까지 실전 코드로 연결

`v166_e4_sealed_knowledge.py`에 `certified_e2_source_separated_context(...)` 추가:

- 외부에서 별도 보관한 최신 소유자 `owner_pin_sha256`과 HMAC 키로 **인증된 V126/V128 SQLite 스냅샷을 조회 전/후 두 차례** 검증.
- V126 레거시 원자 `proposition` 원문을 답변 근거로 그대로 노출하지 않고 E2의 **실제 원문 SRT 직접 인용 / ChatGPT 발언 요약 / 검토자 주의사항**이 서로 분리된 패킷만 반환.
- 일치하지 않는 다른 자식 구간의 원자 ID, 위조 E2 reviewer-note SHA, 무효 외부 pin, 같은 DB 파일을 일반 SQLite로 변조하는 경우 모두 FAIL-CLOSED.
- 실제 `V128→V126` **합성 2자식·3원자·부모 1건 SQLite 발행 후 E4 seal과 E2 결합 조회** 5건 테스트 성공. 결과는 **검토자용 연구근거 조회**이며 E7 최종 개인투자자문 답변이 아님.
- 운영용 키·소유자 pin 배포/외부 고정·전체 서비스 호출 경로 적용은 여전히 미실행.

## 3. 실제 B0001의 3개 미승인 원자 — ChatGPT source-first 반례 검토

비공개 실제 원본 `1-70.zip` 영상 `5NvtBlmt93Y` **1,481 cue**, SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`. 과거 V163/V164 16원자, 동결 V123 원자별 verdict와 source refs를 실제 비공개 원본 cue에 재대조.

비공개 원문 인용 및 ChatGPT 반례 메모를 보존한 JSON SHA-256: **`59394f9f99dafb63571bda7c9a98825a85b38fc923730f7180eb4e35a5d281bd`**. 이는 **ChatGPT 추가 반례 검토**, 정식 V123 수정·독립 블라인드 gold·신규 ChatGPT 최종 승인 영수증이 아니다. 저장 경로는 소유자 비공개 연구 작업 공간, GitHub에는 SHA만 기록.

| 원자 | 원문 문맥 및 근거 확인 | 이번 판정 |
|---|---|---|
| `C00002` | cue30–32 서지·저자 언급. 원서 Wiley의 *The Dhandho Investor*, 저자 *Mohnish Pabrai* 실물 1차 근거 존재. 다만 영상의 한국어 자동전사 저자 음역은 정확한 원음과 대조하지 못함 | **OPEN 유지** |
| `C00009` | cue98–106에서 특정 주주서한 관련 책이 규모 증가 후 버핏 발언 중심이라는 **화자 해석**. Berkshire Hathaway **회사 공식 주주서한 목록은 1977~2024**이고, 같은 페이지에 **1965~2024 전체 편지를 수록한 출판물** 소개가 존재. 이 공식 목록 자체는 특정 책의 편집 범위·당시 자본 규모·전반적인 화자 평가를 입증하지 않음. 포괄적 진술의 반례·한정 조건이 필요 | **OPEN 유지** |
| `C00010` | cue107–111 초기 Buffett partnership의 적은 자본/공격성/수익률 목표에 대한 **평가적·교차 화자 발언**. 1957 partnership letter의 제3자 재게시에서 당시 포트폴리오와 수익 목표 일부 참고 가능하나 **원문 발행기관 인증/화자 명확성/공격적의 의미 판정 부족** | **OPEN 유지** |

### 실제 회사 1차 원문 증명

- 공식 회사 페이지: `https://www.berkshirehathaway.com/letters/letters.html` (회사 원자료, 서한 연혁만 검증).
- 신규 `v166_e4_corporate_historical_primary.py` 및 `test_v166_e4_live_berkshire_primary.py`: GitHub runner에서 **회사 원문 HTTPS 53,854 bytes**, SHA-256 `329a5087fa6c2beb5ce4863bde163d5923cb283690fc2b16f5318bf071e93a9c` 직접 확인. 원자 `C00009/C00010`을 자동 승인하지 않음.
- 실행 증명: https://github.com/yhappcom/pensionport/actions/runs/44071857584 (국세청, Wiley, Berkshire 실물 원문 수집 3 jobs PASS).
- 초기 1957 partner letter 재게시 예: `https://www.buffett-letters.com/en/02-letters/partnership/1957-Partnership-Letter` — **제3자 복제본**으로 정확히 표기, Berkshire 공식 발행 원문과 혼동 금지.

## 4. 실제 실행검증

최신 종합 CI https://github.com/yhappcom/pensionport/actions/runs/44072177360 **9 jobs 모두 SUCCESS**:
- E4 공식근거 게이트+V123 실 코드 단위·정상/부정 **71건**.
- E4 서명 SQLite **19건** 포함 각종 위조/무단수정/원본 발행 증명.
- E4 실제 V128→V126→E2 원문 분리 안전조회 신규 **5건**.
- E4 영상 책 8건 + Berkshire 공식 회사 연혁 4건, 원전 출처 분류 검증.
- E1/E2/E3 기존 회귀 전부 PASS.
- 초기 새 조회 테스트 1회 실패는 두 자식이 같은 영상 `source_sha256`를 공유하는데 다른 자식이라고 판단한 **테스트 가정 오류**였다. 이를 원자 ID / E2 검토 범위로 바로잡아 정상 재시험 성공. 초기 해당 CI https://github.com/yhappcom/pensionport/actions/runs/44070889800.

## 5. E4는 아직 합격하지 못했다

1. **정식 실제 영상 B0001이 HOLD**: `C00002, C00009, C00010` OPEN, 7 ACCEPT 후보/6 격리, 실제 지식 발행 0. 음성/도서 범위/역사적 원문 및 ChatGPT 이견조정 미완료. 이 단계에서 실제 원전 일부 확인을 V123 최종 PASS로 조작해선 안 된다.
2. **현행 금융 법규의 실제 의역 양성 사례 미완성**: 새 의역 계약으로 합성 정상/변조 사례는 검증했으나 **실제 공식 법령의 현행 적용일·조건·예외를 동일한 실제 비공개 영상 주장에 ChatGPT가 평가하여 단일 E4→E3→V128로 승인·발행한 실물 사례는 없음**. 부정확한 법령 참조를 무근거 승인하는 것보다 HOLD가 올바른 결과.
3. **운영 진입점 배포 제한**: 서명형 인증과 안전 조회 코드는 있으나 실제 사용자 서명키·외부 pin 고정/회전·전체 지식/자문 조회 경로 강제 연결은 테스트 환경만 검문. 일반 V126 조회를 E4 인증 자문으로 오인하면 안 됨.

따라서 **E1 PASS, E2 PASS, E3 PASS, E4 FAIL, E5–E7 NOT_RUN**, 전체 엔진 **NO-GO**.  
GitHub `main`, 동결 V123/기존 V126~V128 및 개인 포트폴리오 변경 없음. 다음 재개도 E4부터 수행하며 E5 이동 금지.
