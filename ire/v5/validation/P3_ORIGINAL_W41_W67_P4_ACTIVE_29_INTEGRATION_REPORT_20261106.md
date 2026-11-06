# V5 P3 원본 재검증 확정 범위 및 P4 29노드 실사용 지식 통합

**기준일:** 2026-11-06 (Asia/Seoul)  
**연구 대상:** 박곰희TV #1 `sz5N9WJS310`, `W00041`–`W00067`, SRT cue #710–#1195 (27창, 486 cue)  
**상태:** `SOURCE_CUE_REVIEW_COMPLETED / SCOPED_EDUCATION_INTEGRATED / FORMAL_FINANCIAL_FACT_RELEASE_BLOCKED`

## 원본 출처 확인

- 사용자 Google Drive 기존 보관함 `박곰희TV_SRT_원본보관함`에서 `1-100.zip`을 읽기 전용으로 다시 확보했다. 원본 ZIP 파일 ID는 `1sSHXfWHbzoG5ZT4t0Hc47Jd7SXG_D0OX`이며 내용을 공개 GitHub에 업로드하지 않았다.
- 현재 ZIP SHA-256: `088869c583b2d3ed93d68e4dd5348b1f506877ea2bdc1d66466c199ec80e7716`. 과거 `1-70` 연구 원장 ZIP SHA-256 `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`와 다르다. **동일한 ZIP이라고 보증하지 않는다.**
- #1 SRT `1-100/youtube-transcript-sz5N9WJS310.srt`는 92,252 bytes, 1,195 cue, SHA-256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`; 기존 V5 연구 SRT 해시와 정확하게 일치한다.
- 기존 연구의 창 분할 결과와 #1 전체 67/67개 창의 시작·끝 cue 및 텍스트 SHA가 모두 일치했다. 이번 신규 심사 범위 `W00041`–`W00067`의 486 cue를 원문 대조했다.
- `ire/v5/p3_original_27_source_gate.py`는 GitHub CI에서 원장·해시·주장 범위·검토 제한을 검증한다. 소유자의 사적 ZIP을 명시적으로 제공하는 `--source-zip` 옵션일 때에만 그 실행에서 **원본 바이트 재생 검사 완료**라고 발행한다. 일반 GitHub CI에서 원본 재생 여부는 `false`.

## P3 원자 주장 후보 89건 — 내용 및 해석 판정

| 유형 | 건수 | 처분 |
|---|---:|---|
| 공식 근거의 한정된 범위와 부합하는 설명 | 10 | 교육 문맥 사용 가능, 전체 금융 사실 정식 승인 아님 |
| 금융규정 일반화·과세 선택 오류 | 14 | 자동 사실 승인 금지, 정정 및 제한 조건을 지식에 연결 |
| 투자 판단/전략 의견 | 28 | 개인별 보편적 최적 전략으로 전환 금지 |
| 수치·예시 가정 | 15 | 가정·수익률·과세원금 구분, 미래성과 보장 금지 |
| 질문·당시 역사적 맥락·비금융 내용 | 16 | 규정 사실로 취급하지 않음 |
| 약관 미확인 보험상품 주장 | 4 | 개인 상품 계약 원본 확인 전 사실 승인 금지 |
| 자막 숫자·문맥 모호성 | 2 | 별도 원음 대조 필요 |
| **합계** | **89** | **전 항목 cue anchor 보유, 정식 금융사실 0** |

중요 정정:
- **W00045, cue #787–#793**: “1,500만원 조금 초과 시 전체가 무조건 종합과세”는 2026년 국세청의 해당 사적연금 15% 선택적 분리과세 안내와 충돌한다. 국세 15%와 지방소득세를 구분하고 비공제원금·이연퇴직소득 등 소득 재원 구분이 필수다. [국세청 연금소득](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6452)
- **W00041–W00044**: 8억원에 연 6% 현금 분배 가정은 월 400만원이지만 원금 유지·영구 분배·안전인출·과세제외원금 잔액을 확정하지 않는다. [국세청 연금계좌](https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7885&mi=6605)
- **W00048–W00050**: 일반계좌 국내주식형 ETF 매매차익과 IRP 운용수익의 인출과세는 다른 분류이며, 이연퇴직소득·과세제외금액·운용수익을 일률적으로 혼합해서는 안 된다. [KRX ETF 세제](https://regulation.krx.co.kr/contents/RGL/03/03060105/RGL03060105.jsp) (과거 자료 속 세율을 최신 세율로 고정하지 않음)
- **W00057–W00062**: 과거 보험계약의 5%, 6.5~7.5% 보증은 **실제 보험증권·약관 원본 부재**로 보증 사실 승인 불가. 납입기간, 보증이율 적용대상, 해지환급금과 비용 확인 필요.
- **W00064–W00067**: ISA의 50년 투자·손실 자동 이월·모든 후속 수익 무제한 비과세를 일반 법규로 해석할 수 없다. 법정 손익통산 대상, 계약기간, 연장/해지 시점 및 가입자격을 조건별 확인한다. [조특법 제91조의18](https://law.go.kr/LSW/lsLinkCommonInfo.do?lsJoLnkSeq=1024359131), [금융투자협회 ISA 손익통산 기준](https://law.kofia.or.kr/service/law/lawFullScreenContent.do?historySeq=1483&seq=317)

## P4 신규 지식 7개 — 실제 P3 답변 연결

기존 **22개** 범위 제한 교육 노드(13개 선행 교육 + #1 첫40창 9개)에 원본 cue 기반 교육 노드 **7개**를 추가해, 새 런타임 조회 인덱스에서 **29개**를 사용한다.

| 신규 노드 | 기능 | 기존 지식과 연결 |
|---|---|---|
| `P3-001-DISTRIBUTION-IS-NOT-PRESERVED-PRINCIPAL` | 현금 분배율 ≠ 원금보존·안전인출 | 기존 은퇴자금 교육 보완 |
| `P3-001-PRIVATE-PENSION-1500-CHOICE` | 사적연금 1,500만원 초과 과세 선택 정정 | 기존 사적연금 1,500만원 노드 보완 |
| `P3-001-IRP-DOMESTIC-STOCK-ETF-TAX-DISTINCTION` | 국내주식형 ETF 과세와 IRP 인출재원 차이 | 이연과세·IRP 교육 보완 |
| `P3-001-OLD-PENSION-INSURANCE-TRANSFER-CHECKLIST` | 연금저축보험 계약별 이전·유지 검토 | 계좌 이전·계약 실사 교육 보완 |
| `P3-001-ISA-NETTING-SCOPE-NO-50YEAR-GUARANTEE` | ISA 50년 자동 손실통산·무제한 비과세 오해 차단 | ISA 세제 교육 보완 |
| `P3-001-ISA-RENEWAL-VS-REENTRY-LIMITS` | ISA 재가입·연장 시 세제·자격 조건 비교 | ISA 한도·전환 교육 보완 |
| `P3-001-RETIREMENT-SUFFICIENCY-IS-NOT-GUARANTEE` | 명목 노후자산 금액의 충분성 오해 차단 | 은퇴 검토 교육 보완 |

실제 코드: `ire/v5/p4_p3_source_integration.py`, `ire/v5/advisory_answer_pipeline.py`; 데이터: `ire/v5/advisory_knowledge/p4_p3_incremental_education29_20261106.json`.

- 질문 유형·키워드에 따라 신규 7개 노드를 답변 후보에 연결. 개인별 매매 명령과 무조건 수익 보장 질문은 승인 경로 차단.
- 89개 원본 주장 후보 전체를 투자 지식으로 합치지 않고, **7개 재사용 가능한 교육용 개념으로 통합**한다. 각 개념의 원문 cue 주장 ID, 기존 노드 ID, 출처와 한계를 유지한다.
- 기존 `data/claims.jsonl` 116개 수정 0, 정식 원장 `B04` 자동 병합 0, 신규 금융법률 사실 공식 인증 0, 자동 주문 0.

## 실행 영수증과 QA

GitHub PR `#15`에는 별도 `ire/v5/tests/test_p3_original_27_source_gate.py` 및 `test_p4_p3_source_integration.py`가 포함된다. 두 검사 모듈이 정식 `preflight`에 추가됐으며 `ONE_TURN_RESEARCH_RECEIPT`에 P3 486/89와 P4 22+7=29 현황이 기록된다.

GitHub Actions (커밋 `21fe716aa3d838d9eea23d8352de89b5a521a792`):
- [V5 P3/P4 원턴 통합 게이트](https://github.com/yhappcom/pensionport/actions/runs/42178525001): **성공**, P0~P4 사전검사 48/48, V5 단위 테스트 636건 중 634 PASS, 2 SKIP, 0 FAIL.
- [독립 클린룸 검증](https://github.com/yhappcom/pensionport/actions/runs/42178525102): **성공**.
- 독립 모델 평가자에 의한 원자 주장 완전재현율과 최종 자문 성능 검증이 통과한 것은 아니며, 두 SKIP은 사적 원본을 GitHub CI에서 확인하지 못하는 범위다.

## 추가 완료 조건

- #1 W41~W67 원본 SRT에 한정한 **텍스트 재검토는 수행**, **원음 확인 필요 2건**과 **독립 주장 추출 재현율**은 미완료.
- 현재 법규의 정확한 사용자별 적용성, 각 투자 계좌의 실제 과세재원, 옛 보험계약 보증 조건은 자료 없이 확정 불가.
- #1~#5 전체 288개 창과 5,129 cue의 정식 연구 종료/금융사실 정식 승인은 별도 단계. CI의 기초 통과로 신규 자료 연구 확장이나 개인 거래를 자동 허용하지 않음.

**최종 판정:** `P3_ORIGINAL_SOURCE_AND_CUE_ANCHORED_REVIEW_COMPLETE_WITH_OPEN_QUALITY_LIMITS` + `P4_SCOPED_EDUCATION29_ACTIVE_IN_P3_ADVISORY_PIPELINE`. 원본 음성 또는 추가 독립 평가 없이 더 높은 금융사실·개인자문 인증 레벨로 승격하지 않는다.
