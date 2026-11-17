# V166 E4 제8차 — B0001 C00011·C00284 원문 의미 차등 검문 및 Pabrai 공식 원전

**기준일: 2026-11-18 KST. 공식 단계 E1/E2/E3 PASS, E4 FAIL, E5–E7 NOT_RUN, 전체 NO-GO.**
실제 사용자 영상 신규 승인 지식 발행 **0건**. 기존 동결 V123/V126/V128, `main`, 비공개 SRT와 포트폴리오 미변경.

## 1. C00011 — 사업모델 모방과 투자 성공의 인과관계를 엄격하게 구분

실제 원본 #1 B0001 120cue/16원자 중 `C00011`의 원문 `source_refs` 112–115는 저자가 초기 버핏 파트너십의 비즈니스 모델을 벤치마킹하여 성공했다고 소개한다. V6 원자 **FACT, stance UNRESOLVED**, 동결 V123 기존 `ACCEPT_FOR_RESEARCH`(영수증 변경하지 않음).

새 실물 **1차 근거**: 펀드 운용회사 공식 사이트 `https://pabraifunds.com/about/`가 **Pabrai Investment Funds의 펀드 운영 규칙이 초기 1950년대 Buffett Partnerships를 참고했고 해당 운영규칙의 근접한 복제본이라고 자사 입장으로 설명**. 이 출처만으로 다음 사항은 **입증 불가능**하다.

- 개별 주식 선택·시장 타이밍·포트폴리오 성과까지 버핏과 동일했다는 주장
- **모방 때문에 투자에 성공했다**는 인과관계 또는 초과수익률의 외부 독립회계 인증
- 영상의 한국어 자동전사된 저자 이름의 정확한 원음

신규 `v166_e4_pabrai_partnership_context.py`: 엄격한 HTTPS 1차 발행기관 URL·원문 원자/direct cue·V123 원자 SHA/상태·첫-party 발언을 검사해 **'펀드 운영 구조는 출처로 지지됨/성공의 인과관계는 미입증'**을 별도 결과로 산출한다. 과거 `C00011` 자체를 정식 PASS로 수정하거나 부모 E4 발행을 허용하지 않는다. 합성 소스 위조·원문 인용 변조·V123 OPEN 승격·정부법령 혼입 차단 **8개** 기본 테스트와 아래 원문 버전 테스트 **2개 PASS**.

실제 라이브 원문 관측(서로 다른 GitHub Actions 실행):

| 검문 | 원문 bytes | HTTPS raw SHA-256 | 정규화된 핵심 운영규칙 문구 SHA-256 |
|---|---:|---|---|
| 1차 | 42,095 | `c131348e07f36d7c35b61fc2bd78db0854725a29b9c94c63a0c3906d041b8bfd` | 초기 원문 바이트만 기록 |
| 2차 | 42,095 | `c8f309ea21c42659f44c39758e5b4b88e1e8ab0fc80fa523f4016e40eb92e6ae` | 초기 원문 바이트만 기록 |
| 3차 | 42,095 | `c46f8cdce75ccc95e6b4f195e7a6be3f04445ec13273d6bca5e39630fed9054c` | `8cc57219c395bb9b260807788e54850b5c576e43fda56af463dec63110a681d2` |
| 4차 | 42,095 | `db246df36e263d148993b6cf3ba7d332aba39a252df90c62f2d5c779cdd00ef9` | `8cc57219c395bb9b260807788e54850b5c576e43fda56af463dec63110a681d2` |

**중요한 실제 원인 발견:** *같은 원전 URL, 동일한 바이트 수, 동일한 핵심 의미 문구인데도 매 요청의 HTML 원시 SHA가 달라질 수 있다*. 웹페이지 동적 데이터 때문에 **정규화 주장 문구 SHA와 전체 HTTPS 원시 SHA를 동시에 보존**하도록 개선. **정규화 문구 일치가 동결 V123의 원시 바이트 해시를 대체하는 것 또는 자동 승격하는 것은 절대 금지**. 원전 스냅샷별 원시 바이트/시각을 보존하고 ChatGPT 최종 재검토·새 영수증 버전 승인 전까지 정식 지식 출판 불가.

[실제 최초 라이브 CI](https://github.com/yhappcom/pensionport/actions/runs/44182224665) · [정규화 SHA 안정성 재실측 CI](https://github.com/yhappcom/pensionport/actions/runs/44182875395).

## 2. C00284 — 번역 이유에 대한 출처 없는 추측은 *추측 발언*으로만

실제 원본 자막 source refs 83·84·85에 **'아마'**, **'제목이 바뀐게 아닐까'**, **'생각'** 표현이 있다. V6 `OPINION, stance UNRESOLVED`, 기존 V123 `ACCEPT_FOR_RESEARCH`, 원문은 번역 제목이 그렇게 된 **출판사 내부 결정 사유의 객관적 증거가 아니다**.

E4 `v166_e4_typed_nonstatutory.py` 소스-only 경로에 **해당 원자 `C00284`만을 위한 엄격한 추측 문맥 모드** `SPECULATIVE_TITLE_REASON_SOURCE_ONLY_NOT_PUBLISHER_FACT` 추가:

- 영상 원문의 직접 source_refs에 위 세 표현 존재 필수
- 검토자 메모에 **'추측'/'출판사'/'확인'** 한계를 명시하고 원문 SHA와 별도 결합
- 숫자·세법·보장 수익률·원금보장 관련 주장은 이 모드를 이용해 객관적 사실 검문에서 회피 불가능
- 다른 `UNRESOLVED` 원자는 동일 예외를 빌릴 수 없음
- 원본 V123 `OPEN`은 계속 `OPEN`이며, 해당 출처 분류가 자동 ACCEPT로 변경 불가능

합성 positive·확정적 제목 원인·고위험 금융주장을 추측으로 우회·OPEN 승격 등 **4개 추가 시험 PASS**.

## 3. 비공개 B0001 실물 원본·기존 V123 재확인

실물 `1-70.zip`에서 영상 SRT bytes SHA-256 **`638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`**, cue census **1,481**, V163 B0001 V6 16원자 원문 `source_refs` **69/69개 정확한 SRT 원문과 일치**. C00011 source cue112–115, C00284 cue83–85 원문·의미구조·동결 원자 지위 원천 검문.

원본 V123 **7 ACCEPT_FOR_RESEARCH / 8 OPEN / 1 EXCLUDE_FROM_RESEARCH**; 최종 `CHAT_FINAL_HOLD_OPEN`. 후속 source-only view의 7/3/6도 별도 기록이므로 혼합 금지. *C00011의 첫-party 운영규칙 참조 입증*과 *C00284의 추측 발화 확인*만 추가한 상태이며, **실제 V123 재승인·V128 원자 지식 발행은 수행하지 않았다.**

비공개 영수증 `/mnt/data/v166-private/V166_E4_PRIVATE_B0001_C00011_C00284_PRIMARY_SCOPE_20261118.json` SHA-256 **`080a070f9e8fe48df7d0145ad54da4c9bbc29666903231667c6eeba42f0e9405`**. GitHub에는 원문/SRT/음성·개인 검토 문구를 올리지 않고 SHA만 기재.

## 4. 코드 CI 및 단계 판정

[최신 전체 ordered E1–E4 CI](https://github.com/yhappcom/pensionport/actions/runs/44182875495) **9/9 jobs PASS**. [최신 실물 원전 HTTPS Wiley·NTS·Berkshire·Pabrai](https://github.com/yhappcom/pensionport/actions/runs/44182875395) **5/5 jobs PASS**. 합성 검문 성공, 공식원전 실물 체크, 실제 사용자 영상의 최종 승인 상태는 **서로 다른 증거 수준**이다.

**E4의 남은 미완료 핵심:** B0001 `C00002`(저자 이름 ASR), `C00009`(주주서한 선집 실제 구성), `C00010`(초기 파트너십 투자 성격), `C00011`의 '벤치마킹 때문에 성공' 관계, 실제 법령 주장 적용시점 원전 검증, 13개 child 전수 native V123 최종 검토, 운영키·독립 최신 owner PIN의 실물 배치·자문 조회 전수 강제. E4 전체 PASS/실물 부모발행 0이므로 **E5 시작 불가**.

main, 동결 V123/V126/V128, 보호된 증거와 사용자 포트폴리오는 수정하지 않았으며 PR #54는 draft 미병합.
