# V6 현행 운영 기준 — ChatGPT 최종 연구 검증 관문

**효력 기준:** 2026-11-15 KST · **적용 범위:** `yhappcom/pensionport` 검증 브랜치의 **신규 V6 연구 지식 후보** · **변경 이력:** V123.3 문서·CI 일치 검문.

## 1. 최종 승인 권한과 연구 절차

**ChatGPT 채팅이 최종 품질 검토자다.** 외부 검토자, 별도 모델 API, 외부 신원기관은 이 프로젝트의 채팅 내부 연구를 진행하기 위한 필수조건이 아니다. 엔진 CI 성공, 구조적 SRT 귀속률 100%, V6 ACID 저장 영수증, 기존 지식 후보 관계 검문만으로 신규 연구 지식을 승인하지 않는다.

1. **원본 고정:** 비공개 원본 SRT/ZIP, 영상 ID, cue 범위·시간, SHA-256, 소유자 인벤토리와 창별 소유권을 먼저 검증한다. 고정 불가 시 `HOLD`.
2. **엔진·채팅 입력:** 원자 주장 후보, 질문·인용·반박·부정·정정, 조건·예외, 금액·기간·세율·수치와 출처 구간을 추출한다. 기존 자료와의 동치·충돌·중복 관계는 *잠정* 상태로 연결한다.
3. **V6 구조 검문:** `atomic_exchange`의 원본 인용·숫자·cue별 disposition 검문과 `host_batch`의 현재 DB HEAD·소유자 핀·창별 증거·ACID/멱등성 검문을 거친다. 이 단계의 성공은 **ChatGPT 최종 승인 아님**. 소프트웨어 PASS는 연구 지식 승인 근거가 아니다.
4. **ChatGPT 최종 재검토:** 전체 원본 cue와 **각 원자 주장**을 원문 우선(A), 반례 재검토(B), 불일치 조정으로 확인한다. 화자와 검토자의 견해, 복합 분할, 조건·예외·부정·수치·기간, 원음/화면 미확보, 고위험 누락을 개별 확인한다. 사전 예측을 이미 봤으면 완전 블라인드라고 표기하지 않는다.
5. **현행 금융 근거:** 금융 주장에 대해 공식 원문 **실제 바이트의 해시 재검증**, 시행일·대상·예외·상품/계좌 제한과 ChatGPT의 적용 범위 판단을 연결한다. URL이나 SHA 문자열만으로 근거 확인 완료라고 하지 않는다. 진위·발행기관 인증까지 검증됐다는 주장도 금지한다. 확보하지 못한 근거는 `OPEN`.
6. **ChatGPT 최종 판정 후 활용:** 아래 상태표에 따라 **신규 V6 연구 후보의 P1 읽기 전용 미리보기**만 허용한다. 승인되지 않은 항목을 Master116/P4/V5 또는 개인 포트폴리오 자문에 자동 편입하지 않는다.

## 2. 최종 판정과 실제 차단 규칙

| 상태 | 성립 조건 | 허용되는 활용 |
| --- | --- | --- |
| `HOLD_MISSING_V6_HOST_BATCH_OR_STORE` | 실제 소유자 원본에 대한 V6 DB·최신 HEAD·창별 검문 영수증이 없음 | 신규 후보 반출 불가 |
| `HOLD_MISSING_CHAT_FINAL_REVIEW` | 완전한 ChatGPT 최종 검토표가 없음 | 신규 후보 반출 불가 |
| `CHAT_FINAL_HOLD_OPEN` | cue/주장·조건/예외·고위험 FN·원음/화면·금융 원문 중 필수 확인이 OPEN | 신규 후보 반출 불가, 근거·미해결 사유 보존 |
| `CHAT_FINAL_REJECTED` | ChatGPT가 원자 주장 하나 이상을 반려 | 해당 배치 신규 후보 반출 불가, 수정 후 새 검토 |
| `CHAT_FINAL_PASS_RESEARCH_CANDIDATES_ONLY` | 실제 V6 원본·DB 영수증 및 전수 ChatGPT 검토가 일치하고 모든 필수 OPEN이 해소 | **P1 읽기 전용 신규 연구 후보 미리보기만** 허용 |

ChatGPT 최종 검토는 **연구 후보 반출의 마지막 필수 품질 관문**이다. 통과해도 **정식 금융 사실 승인, Master116/P4 병합, 개인 투자자문·주문 실행, 외부 독립 정확도 인증, 791편 연구 완료 또는 전체 P0 GO가 아니다**. 별도 승인 게이트를 거치지 않은 모든 후속 활용은 금지한다.

## 3. 실행 진입점과 동결된 코드 경계

- 소프트웨어 V6 기초 원본·원자·저장 검문은 기존 `ire/v6/atomic_exchange.py`, `ire/v6/host_batch.py`를 그대로 사용한다.
- **최종 ChatGPT 필수 관문:** `validation/ire-v6-frozen/v123_chat_final_gate.py`의 `assess_chat_final_gate` / `require_chat_final_release`.
- **지원되는 V6 신규 후보 반출 경로:** `validation/ire-v6-frozen/v123_chat_validated_knowledge_preview.py`의 `preview_chat_validated_candidates`. 이 함수가 `require_chat_final_release`를 먼저 호출한다.
- **검증 코드:** `validation/ire-v6-frozen/test_v123_chat_final_gate.py` 및 문서·실행 경로 일치 검사 `test_v123_final_protocol_docs.py`.
- `ire/v6` 동결 파일 집합은 변경하지 않는다. 기존 V3/V5의 별도 수동·레거시 경로까지 V123 검문이 자동 적용된다고 주장하지 않는다. 신규 통합 경로를 추가할 때는 동일 최종 관문을 별도로 연결·시험한다.

## 4. 공개/비공개 증빙과 승인 책임

원본 자막·문장별 판정·공식 원문 바이트·개인 계좌 정보는 비공개 보관한다. 공개 GitHub에는 SHA, 건수, 판정 범위와 *개인 정보를 포함하지 않는* 합성 회귀시험만 저장한다. 데이터가 존재하지 않으면 비공개 사실을 암묵적으로 생성하지 않는다. ChatGPT의 검토 기록은 실제 채팅에서 수행한 판단일 뿐 제3자의 독립 블라인드 정답셋이 아니다.

**반드시 기록할 최소 증빙:** `video_id`, `source_sha256`, `manifest_sha256`, `host_bundle_sha256`, `host_event_sha256`, `chat_final_review_digest_sha256`, 전수 cue·원자 주장 수, ACCEPT/REJECT/OPEN 개수, 금융 OPEN·고위험 OPEN, 적용 기준일, 공식 원문 바이트 SHA, 보류 사유, 최신 DB HEAD와 CI 커밋 SHA.

## 5. 역사적 자료의 해석과 미완료 현황

- V103/V105/V107 외부 서명 검문은 외부 인증 등급에만 선택 적용되는 역사적 경로다. V109/V119의 **채팅 내부 검토** 결정이 현행 정책이며 이 문서가 V123의 **최종 관문 적용**을 상세화한다.
- V120~V122의 동일 채팅 내부 참조 점수는 외부 독립 정밀도·재현율이 아니다. 점수로 최종 관문을 자동 통과시키지 않는다.
- **V122 ISA 영상 47개 cue / 금융 OPEN 12건:** 원본 실물 V6 `host_batch` 영수증 미완비로 현재 `HOLD_MISSING_V6_HOST_BATCH_OR_STORE`; 영수증을 확보해도 금융 OPEN 해소 전에는 `CHAT_FINAL_HOLD_OPEN`. 신규 승인 0, P0 `NO_GO`.
- V123.2까지 합성 시험의 성공은 소프트웨어 보안·무결성 PASS이며, 전체 791편에 대한 연구 정확도 입증이 아니다.

**우선순위:** 새 원본의 V6 저장과 근거 확보 → ChatGPT 전수 검토 → `HOLD` 해결·거부 수정 → 최종 관문 재실행 → PASS인 범위에 한해 읽기 전용 연구 후보 확인.

## 6. V123.4 실물 47-cue/금융 OPEN 12건 재검문 기록 (2026-11-15)

- 이번 채팅에서 비공개 V122 원본 아카이브를 다시 열어 **47개 SRT cue와 봉인된 SHA-256의 정확한 일치, 파일별 ZIP SHA와 V114 5단계 재현**을 검문했다.
- ChatGPT가 원본 전체 cue·기존 17개 참조 주장·금융 12개 반례/적용 제한을 다시 검토하고, 검토 결과 전문은 **비공개 로컬 파일**로 남겼다. 공개 GitHub에는 비공개 검토표의 SHA와 범위·보류 상태만 기록했다: [V123.4 공개 영수증](V123_4_V122_OWNER_CHAT_REVIEW_SHA_ONLY.json), [실물 검문 보고서](V6_V123_4_REAL_47CUE_FINANCE12_CHAT_REVIEW_HOLD_REPORT.md).
- **현재 실물 V6 `host_batch` 소유자 DB 최신 HEAD·완전한 창별 증거는 미검증**, 공식 금융 원문 HTTP 바이트·시행일 및 상품 적용성 확정도 미완료다. 실제 `assess_chat_final_gate`의 소유자 운영 저장소 판정을 수행했다고 주장하지 않는다.
- 따라서 현재 준비도 판정은 `HOLD_MISSING_V6_HOST_BATCH_OR_STORE`이며, 저장 근거가 확보되더라도 금융 OPEN 12건을 해소하지 않으면 `CHAT_FINAL_HOLD_OPEN`이다. **읽기 전용 신규 연구 후보 반출 0, 금융사실 승인 0, 전체 P0 NO-GO**다.
- V123.4 SHA-only 영수증과 운영기준서 간 무결성은 `test_v1234_real_owner_rereview_checkpoint.py`로 별도 회귀검사한다. 이는 실물 금융 의미 정답/공식 원문 인증 시험의 대체물이 아니다.


## 7. V123.6 실물 V6 격리 저장 및 ChatGPT 관문 실행 (2026-11-15)

- [V123.6 실물 검증 기록](V6_V123_6_REAL_SOURCE_HOST_BATCH_STAGING_CHAT_FINAL_HOLD_REPORT.md), [SHA 전용 영수증](V123_6_V122_REAL_NATIVE_V6_SHA_ONLY_RESULT.json): 사용자 비공개 V122 원본 47 cue와 동일 채팅 참조 17개 원자 후보를 실제 V6 `atomic_exchange`·`host_batch`에 적용. 새 **격리된 비공개 운영자 잠정 DB**에서 `W00001` 모델·구조 영수증 1/1 원자 저장, HEAD 검증, 멱등 재실행 성공. 실제 `assess_chat_final_gate` 실행 결과는 **`CHAT_FINAL_HOLD_OPEN`**, 읽기 전용 반출 0.
- 이 DB는 기존 소유자 운영 DB가 아니며, 인벤토리 핀은 ChatGPT가 사용자 보관 원본에서 생성한 **운영자 유래 잠정 핀**으로 소유자 독립 서명이 아니다. 기존 소유자 운영 DB의 최신 HEAD 검증을 대신하지 않는다. V123.4의 `HOLD_MISSING_V6_HOST_BATCH_OR_STORE`는 당시의 준비도 분류로 유지하고, 이번 격리 실물 실행이 반환한 상태와 구분한다.
- 금융 OPEN 12건은 기존 고위험 증거 원장 기준이며, V123 관문은 17개 후보 전부를 보수적으로 금융 민감 `OPEN`으로 분류했다. 원음·화면 확인, 조건 cue 32 누락 위험, 숫자 범위 cue 14, 공식 원문 HTTP 바이트와 현행 법령 적용성은 미종결. 따라서 **정식 금융 승인 0, Master116/P4/V5 편입 0, P0 NO-GO**를 유지한다.
- 비공개 원본·검토표·SQLite 스냅샷은 사용자 비공개 Library에 저장하고, GitHub에는 SHA 및 보류 사유만 저장한다. 공개 CI의 회귀검사는 **메타데이터 일치**만 확인하며 실제 비공개 실증을 재수행했다고 주장하지 않는다.

## 8. V123.6.1 32번 조건 누락 수정 및 과거 정부 원문 바이트 실측 검문

- [V123.6.1 SHA-only 영수증](V123_6_1_V122_CUE32_OFFICIAL_RAW2_SHA_ONLY.json): 원문 47 cue에 대한 별도 V6 실물 격리 DB 재저장으로 cue 32 조건절을 원자 주장에 연결했다. 위험 경고 1건 해소, 의미 검토 대상 31 → 30. 다중 숫자 cue 14와 음성/영상 및 전수 의미 OPEN은 미해소다.
- 보존된 2026-11-08 정부 원문 HTTP 바이트 2건의 실제 SHA-256을 다시 검증했다. 이것은 원문 바이트 **기존 아카이브 재현 PASS**이지 영상별 현행 법령·발행자 서명·개인상품 적용성의 검증 완료가 아니다. 금융 OPEN 원장 12건과 현재 V123 분류 17개 OPEN은 그대로 유지한다.
- V123 최종 관문 두 번째 실제 격리 DB 반환 상태 `CHAT_FINAL_HOLD_OPEN`, 정식 연구/금융 승인 0, P0 NO-GO. 기존 소유자 운영 DB와 별도 인벤토리 독립 서명은 계속 미검증이다.

## 9. V123.7 복합 기간 원자 주장 정정 및 금융 OPEN 12건 재검문

- [V123.7 실물 검증 기록](V6_V123_7_OWNER_SOURCE_NUMERIC_SPLIT_FINANCE12_DOCKET_HOLD_REPORT.md), [공개 SHA 전용 영수증](V123_7_V122_REAL_47CUE_18ATOM_CHAT_HOLD_SHA_ONLY.json). V122 실제 47 cue 중 14~16번의 기간(ISA 3~5년 대 연금계좌 20·30·50년)을 한 주장으로 결합했던 입력을 서로 다른 **두 의미 원자**로 분해했다. 연금계좌 장기 운용기간은 보장이나 법정 고정기한이 아니라 조건부 예시로 보류한다. 전체 잠정 원자 후보 17 → 18, 32번 조건절 연결 수정은 유지.
- 실제 비공개 원본·불변 Master116/P4·V6 동결 실행 코드로 **새 격리 SQLite 저장**을 시행했다. cue 구조 귀속 47/47, 모델·증명 1/1, 현행 격리 HEAD·멱등 재실행 및 SQLite 백업 검사 PASS. **기존 소유자 운영 DB가 아니며 소유자 독립 서명 인벤토리는 미확보**.
- 본 ChatGPT V123 최종 관문 실제 반환 `CHAT_FINAL_HOLD_OPEN`: 제안 원자 18건 OPEN, 금융 민감 후보 18건 OPEN, 기존 고위험 금융 원장 OPEN 12건. 12건에 대해 공식 페이지·법령 문맥을 재점검했으나 문서 발행·시행·상품 범위의 주장별 원문 바이트를 완비하지 못했다. 앞서 보존한 정부 원문 바이트 2건의 SHA 재현 성공은 **12건 공식 승인 근거가 아님**.
- 사용자 비공개 원본·원자 입력·평가표·SQLite 스냅샷·금융 OPEN 12건 상세 근거는 비공개 Library ZIP에 보존. 연구 후보 반출 0, 금융 사실 공식 승인 0, 기존 V5·Master116·P4 변경 0, P0 NO-GO 유지. 공개 CI의 V123.7 테스트는 비공개 원본 재실행이나 독립 의미 정확도 인증을 대신하지 않는다.

## 10. V124 증거 원문-주장 연결 검문 (2026-11-15)

- [V124 SHA-only 영수증](V124_REAL_FINANCE12_PRIMARY_BYTE_RELEVANCE_SHA_ONLY.json) / [검문 보고서](V6_V124_FINANCE12_PRIMARY_BODY_RELEVANCE_AND_OWNER_OPEN_REPORT.md): 실제 비공개 V123.7 소유자 영상 47 cue와 금융 OPEN 12건에 대해 2026-11-08 아카이브 정부 원문 바이트 2건의 SHA·주장 적용 가능 범위를 재검문했다.
- §40조의3 인출순서 원문은 R011의 **규정 텍스트 부분**을 확인하지만 개인의 세액공제 미적용 원금 확정까지 허가하지 않는다. R004·R010에는 법령 문맥 참고만 가능하며 일반 중도인출 자유·무벌칙 등을 입증하지 않는다. 나머지 9건은 해당 아카이브 원문 바이트에 직접 대응하는 근거가 없다. 일반 국세청 연금소득 안내를 ISA 전환 60일 기한 R014의 공식 원문 증거로 재사용해서는 안 된다.
- \`v124_finance12_primary_provenance_guard.py\`를 추가하여 이 원문 오연결·보류 상태의 잘못된 승인·중복 및 누락을 거부한다. 해당 모듈은 기존 V123 ChatGPT 최종 관문을 대신하거나 자동 금융 사실 승인하지 않는다. 개인별 상품/계좌, 시행일·종료일, 원음 및 소유자 운영 DB는 여전히 OPEN. 공식 금융 승인 0, 12건 OPEN, P0 NO-GO 유지.

## 11. V124.1 R009 과세연도 전환 특례 의미 보완 (2026-11-15)

- [V124.1 R009 SHA-only 영수증](V124_1_R009_PRIOR_TAX_YEAR_CREDIT_EXCEPTION_SHA_ONLY.json), [V124 실물 근거 보고서](V6_V124_FINANCE12_PRIMARY_BODY_RELEVANCE_AND_OWNER_OPEN_REPORT.md). R009의 과거 설명에서 **ISA 전환 연도 세액공제와 비공제 납입금의 이후 과세연도 전환 신청**을 구분하지 않은 예외 누락을 식별했다.
- 현행 소득세법 시행령 **제118조의3**([법제처](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lspttninfSeq=126655)) 및 국세청의 **서면-2024-법규소득-1973**([공식 질의회신](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=200000000000006505))에 따르면, 이전 과세기간에 공제받지 않은 적격 연금계좌 납입금에 대해 신청·요건 충족 시 해당 연도 납입금 간주 전환이 가능하고 ISA 만기 전환금액도 그 검토 대상에 포함될 수 있다. 이것은 **ISA 3~5년마다 공제 자동 반복·같은 공제한도 자동 재발생·비공제금액 무조건 공제**와 전혀 다르다.
- 해당 규정/해석의 새 2026년 원본 HTTPS 바이트·개별 계좌 공제 미적용 내역·전환 신청서·원음 확인은 여전히 미확보다. 새 **비공개 수정 판정표**만 사용자 Library에 보존하고 GitHub에는 SHA만 기록한다. R009 포함 금융 OPEN 12, 공식 승인 0, ChatGPT 최종 HOLD, P0 NO-GO 유지.

## 12. V125 사용자 최종 개발 순서 확정 — 엔진 우선·포트폴리오 후속 (2026-11-15)

- [실행 가능한 단계 차단 정책](V125_ENGINE_FIRST_PORTFOLIO_DEFERRED_POLICY.json) 및 [E1-E10 엔진 완료 정의서](V6_V125_ENGINE_FIRST_REQUIREMENTS_AND_PHASE_ORDER.md)에 따라 **Phase E 연구 엔진 완성이 선결 조건**이다.
- 신규 영상 연구 **Phase R**은 전체 영상 자동·ChatGPT 검증·증거 검증·지식 영속 누적·중복/충돌 해결·실제 질문 검색/최신규정 자문·실물 E2E 수용검사까지 성공한 뒤에만 허용한다.
- **Google Drive 포트폴리오 연계 Phase P는 엔진 완성 이후 별도 단계**다. 기존 자료의 읽기 전용 점검 기록이 있다고 해서 연계 코드를 개발하거나 포트폴리오 분석을 엔진 완성의 필수 과제로 바꾸지 않는다.
- 이 단계는 문서와 차단 정책·회귀검사만 추가하며 엔진 완성 또는 Phase R/P 승인으로 주장하지 않는다. 동결 V6 코드, `main`, V5, Master116, P4 미변경.

## 13. V126 비공개 ChatGPT 검증 지식 누적 원장 부분 구현 (2026-11-15)

- [V126 개발·실증 보고서](V6_V126_CHAT_FINAL_PRIVATE_KNOWLEDGE_ACCUMULATION_REPORT.md): [코드](v126_chat_approved_knowledge_store.py), [합성 실물 배치 및 거부 회귀검사](test_v126_chat_approved_knowledge_store.py).
- `V123 require_chat_final_release`가 실물 최신 V6 호스트 저장소에 대해 **PASS**를 내야만 `PrivateKnowledgeStore.add_chat_final_batch`가 별도 비공개 SQLite 누적원장에 후보를 저장한다. 지식 관계는 ChatGPT 추가 의견 SHA와 기존 Master116/P4 원본검문을 통해 연결하며, 충돌 격리·철회·멱등성·개정 이력을 보존한다.
- 누적 증거 조회 결과는 **ChatGPT의 추가 사실검토 및 현재 공식규정 검색을 요구하는 비공개 맥락 패킷**이지 자동 개인 투자자문이 아니다. 기존 금융 OPEN 12건과 V122 실제 ChatGPT HOLD는 그대로이므로 신규 실물 승인/반출 **0**.
- V125 E6–E8 중 신규 검증·누적·검색 부문은 프로토타입 개발을 시작했으나 미완성 상태 `OPEN`; 대량 영상 일괄 처리와 Q&A 실제 최종 답변 연결 미완성. **신규 영상 연구 및 Google Drive 포트폴리오 연결은 시작하지 않는다.**
