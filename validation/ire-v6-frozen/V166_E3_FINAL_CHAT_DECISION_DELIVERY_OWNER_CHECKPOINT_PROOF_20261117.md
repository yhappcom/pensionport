# V166 E3 — ChatGPT 최종 판정 승인·보류·격리 전달 종단간 검증

**2026-11-17 KST · 사용자 확정 E3 기준: "승인·보류·격리 결과가 정확히 전달"**  
**판정 권고: E3 PASS (V166 버전형 공식 전달 진입점에 한함). E4~E7은 NOT_RUN.**

## 1. 실제 발견한 결함과 수정 방식

**발견:** 동결하지 않는 구 V128 `run_all_video_scopes_in_chat`는 V127.1 체크포인트에 기록된 **명시적 `REJECT`도 일반 `HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE`로 평탄화**했다. V127.1의 실물 SQLite에는 `PASS/HOLD/REJECT`가 서로 다르게 저장되고 있었지만 상위 사용자 전달에는 구분이 없었다. 이를 '거부'와 '추가근거가 필요한 보류'의 동일 상태로 오해할 위험이 있다.

**수정:** `v166_e3_chat_decision_delivery.py`에 두 함수를 추가.

- `replay_chat_decision_envelope(case)`: ChatGPT가 사전 작성한 실제 source-binded `chat_review`를 **변경하지 않은 V123** `assess_chat_final_gate`로 다시 검문. 모든 원자에 대해 `ACCEPT_RESEARCH_CANDIDATE_ONLY`, `OPEN_UNRELEASED`, `REJECTED`, `QUARANTINED_NOT_RESEARCH_KNOWLEDGE`의 개별 유형 및 검토 메모 SHA·원자 SHA·격리 사유를 전달하고 V123 반환과 원자 수·상태를 전수 대조. 한 건이라도 거부됐다면 부모는 `REJECTED` 우선, OPEN은 `HOLD`, 정상 V123 PASS도 **일반 연구용 후보**일 뿐 금융 사실 승인 아님.
- `run_full_video_with_e3_decisions(...)`: **공식 V166 E3 호출 진입점**으로 기존 V128을 실제 1회 호출하며, 그 결과를 임의 수정하지 않고 V127.1 SQLite에 저장된 `chat_review_sha256`, `gate_receipt_sha256`, V6 host event/bundle SHA와 전수 재대조한다. 새 외부 전달값은 `CHILD_REJECTED_FINAL_CHAT`, `CHILD_HOLD_UNRELEASED`, `PUBLISHED_RESEARCH_CANDIDATES_ONLY`; 원래 V128의 `native_v128_status`도 그대로 포함한다.
- 이 E3 진입점을 사용하지 않고 **기존 구 V128 반환만 읽으면 REJECT↔HOLD의 정보손실은 여전히 존재**한다. E4~E7에서 이 V166 진입점을 사용해야 하고, 직접 V128 상태를 금융 자문 답변으로 해석해서는 안 된다. 구 V123/V126/V127/V128 코드를 수정하거나 우회하지 않았음.
- 소유자 자막·검토 영수증은 비공개, 공개 GitHub에는 버전형 어댑터·합성 회귀시험·메타데이터만 저장.

## 2. 실측 GitHub CI: 8개 jobs success

- **최종 E3 실행 URL:** https://github.com/yhappcom/pensionport/actions/runs/44034800842
- E3 신규 회귀 `test_v166_e3_chat_decision_delivery.py` 10개: (1) 정상 원자 승인 PASS→V128 원자적 연구후보 저장, (2) 외부 원전 누락 HOLD→지식 0, (3) 명시적 `REJECT`→V127.1 REJECT이며 구 V128은 HOLD, 새 E3는 REJECTED, (4) 한 자식의 REJECT+OPEN 동시 존재 시 거부 우선, (5) ChatGPT 최종 리뷰 누락 차단, (6) 이미 PASS된 자식 검토 메모 변경 후 재발행 차단, (7) REJECT된 자식의 임의 PASS 바꿔치기 차단(명시적 revision 없으면 실패), (8) 원자/원문/검토 노트 digest 보존, (9) V164 유형별 가설 출처 격리 후 연구용 후보 2개만 지식으로 발행, (10) 위조 격리 사유 차단.
- 처음 CI에서는 복합 `REJECT+OPEN` 반례가 원자 1개짜리 합성 B0002의 **존재하지 않는 두 번째 원자**를 수정해 실행 설정 오류 발생: https://github.com/yhappcom/pensionport/actions/runs/44034692850. 이를 원자 2개짜리 B0001 합성 입력으로 정정하고 **동일 회귀를 전량 재실행해 통과**했다.
- 기존 E1/E2 원형 회귀 + E3를 포함해 **8 jobs 모두 SUCCESS**, 보호된 V123/V146 및 기존 V128 스토어 경로 회귀 PASS.

## 3. 실제 사용자 B0001 원본 120 cue·16원자 — ChatGPT 판정 보존

사용자 비공개 `1-70.zip` 원본 SRT SHA `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`; 기존 V163 16원자 및 V164 ChatGPT 발언 확인 5개를 원문에 재고정. **바이트 동일한 동결 V123** (Git blob `17da9fae7d4fcc48087c55ca0d2031ba72a0bb3c`)을 사유별로 다시 실행.

| 원자 처분 | 실제 수 |
|---|---:|
| ACCEPT_FOR_RESEARCH → 연구용 승인 **후보** | 7 |
| OPEN → 미승인 보류 | **3** (`C00002`, `C00009`, `C00010`) |
| EXCLUDE_FROM_RESEARCH → 명시적 격리 | **6** (`C00001`, `C00003`, `C00012`, `C00277`, `C00285`, `C00293`) |
| REJECT → 명시적 거부 | 0 |
| V123 최종 결정 | **CHAT_FINAL_HOLD_OPEN** |

- 원래 ChatGPT review digest `3ac9dfe883e1f4a1f2cedb3744a24b9bc506369173a9ea764eb7221e8a2c627e`, V123 gate 결과 digest `bcf6878d554e1b581f0a873f87edf96d2a3d2b14628934681a75a1ff391822d0`. 원전 미확인 3건, 원래 고위험 OPEN 이중집계 라인 12건, 의견 불일치 미조정은 **그대로 유지**. `high_risk_open=15`는 V123의 중복 합산 값으로 15개의 새로운 독립 위험 건수가 아니다.
- 실제 B0001 승인 영수증은 원자별 해시+검토 사유와 원본 digest로 보존. 임의로 OPEN 1건을 REJECT로 바꾼 **반사실적 시험**에서 V123이 실제 `CHAT_FINAL_REJECTED`를 반환했고, 그 입력은 **실제 ChatGPT 최종 거부 판단으로 기록하지 않았다**. 허위 격리사유 및 원자 메모 digest 변조는 모두 차단됐다.
- 사용자 비공개 B0001 케이스를 **실제 V127.1 원자적 체크포인트와 V128 원본 코드(둘 다 Git SHA 일치)**에 전달. V127.1이 source/host/review/gate digest를 그대로 보존하며 **HOLD** 기록했고, V128이 `HOLD_CHILD_CHAT_SEMANTICS_OR_FINANCE`로 중단. 임시 SQLite `events=0, knowledge=0, parent_publications=0`. 다른 자식 12개는 심사를 진행하지 않았다.
- 비공개 실물 E3 영수증 SHA-256: 원자 판정 `d0f7e17ecc79745c1edeb25228d3bc355cdc5aae0bcb04cfa801bee6842e1865`, 실물 체크포인트 `5baad4c91ae264f4b89f90eaa21d5d560fb26450de88e32c3c56fdf45ec5d3b6`. 비공개 원본/자막/SQLite 전문을 GitHub에 업로드하지 않음.
- **한계:** B0001 실물에서는 frozen native V123→V127.1→V128을 실제로 실행하고 해시 동치를 대조했다. 새 E3 **상위 wrapper**의 직접 합성 검문은 CI에서 수행했지만 owner SRT 실제 인스턴스에 wrapper 함수를 *그대로* 실행한 것은 아님. 둘을 독립 수행으로 명시.

## 4. E3 합격 범위와 남은 단계

E3의 사용자 기준은 **ChatGPT 최종 판정의 전달 정확성**이다. 원자별 상태와 사유를 별도 버전형 반환에 기록하고 동결 V123/V127.1 상태에 해시 재대조했다. 실제 B0001 HOLD와 합성 PASS/REJECT/격리 네 종류를 각각 검문해 **E3 기능 PASS**로 판단할 수 있다.

**E3 PASS가 뜻하지 않는 것:** B0001 객관 역사·도서 사실 3건의 원전 진위 승인, 고위험 누락 0, 13구간 전체 승인, 새 실물 투자 지식 발행, 791편 정밀도·재현율, 투자자문 품질 인증. 이는 다음 사용자 확정 순서 **E4 — 정식 승인 관문에서 적법한 입력 PASS·부적합 입력 차단을 실물로 검문**해야 한다. E4~E7은 이 턴에서 시작하지 않는다.

**운영 원칙:** `E3=PASS`로 변경한 뒤에도 사용자용 최상위 엔진 판정은 **NO-GO**, 실제 `V128` 소유자 지식 신규 0건. 기능·연구정확도·현행 법령·개인적합성을 구분한다.
