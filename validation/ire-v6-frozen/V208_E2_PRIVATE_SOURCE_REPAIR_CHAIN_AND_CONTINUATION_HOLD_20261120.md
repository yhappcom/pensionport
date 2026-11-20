# V208 — 원본 E2 검토 → 명시적 ChatGPT 정정 → 비공개 SHA 원장 → 재개 연결 실증

**판정:** E2 소프트웨어 구조 개선 PASS / **E2 금융·언어 의미 품질 최종 판정 HOLD**  
**GitHub branch:** `verify/ire-v6-e2-source-census-adversarial-20261120` / Draft PR #75  
**기준:** 2026-11-20 KST, E1 최종 PASS 유지; E3–E5 미진행.

## 개선한 실제 단절

V206은 원본 SRT 전체 cue를 의미 재검문하고 원본 사실이 `QUESTION`/`QUOTE`에서 누락되면 `HOLD`를 기록한다. V207은 ChatGPT가 별도로 제시하는 출처 연결·조건/예외/반박/숫자 보존 정정 계획을 검증하여 **미승인 후보**를 만들었다. 그러나 이전에는 **V207의 명시적 정정 결과 자체가 V206의 비공개 자막 검토 SQLite와 연결되지 않았다**. 중단 후 검토 원장과 정정안이 동일 ChatGPT 검토 출처인지 재현하기 어려웠다.

이번 `v208_e2_private_source_repair_journal.py`는 **한 개의 비공개 SQLite DB**에 다음을 기록한다.

1. 사용자의 V176 원문 SHA/manifest/head에 묶인 V206 원본자막 E2 검토 이벤트
2. 해당 검토 이벤트의 `event_sha256`와 `census_head_sha256`를 확인한 후에만 허용되는 V207 ChatGPT 정정안
3. 정정안의 원본 자막 인용·claim 종류·질문/인용 발언 귀속·조건/예외/반박/숫자·미승인 projection 해시
4. 별도의 SHA 연결 이벤트 원장과 외부에 고정할 수 있는 `repair_head_sha256`
5. 동일 요청의 멱등 재생, 상이한 재판정의 무단 덮어쓰기 거부, 원본 head 변경 차단

빈 원본 검토, 출처가 다른 검토 응답, 사전 저장되지 않은 cue, 동일 cue의 다른 ChatGPT 판정, 연속 해시 위조, 잘못된 DB 파일, 고장난 종속 필드는 **저장하지 않는다**. source→E2 원장→정정 원장의 순서가 뒤집힌 시간적 관계도 막는다. private SQLite에서 기존 `source_cue_sha256`과 `source_text_sha256` 혼동을 막고, 해시 필드가 리스트 같은 잘못된 유형이어도 `TypeError` 대신 `InvalidInput`으로 거절한다.

원본 V176·정식 V6 원자·V123 승인 상태를 **어떤 방식으로도 자동 변경하지 않는다**. `review_executor=CHATGPT_IN_CHAT`는 형식 필드이며 독립 검토자의 실제 서명이나 모델/API 실행의 인증을 의미하지 않는다.

## 실제 코드를 실행한 시험

- 정상 경로: V176 source → V206 original cue review → V207 explicit ChatGPT synthetic repair → V208 PRIVATE `e2_events`+ `e2_repairs` → 다른 SQLite 연결로 재열기 → 원문/정정 해시 검증
- 음성 검증: 원본 cue review 없는 정정, 다른 E2 답변에 연결된 정정, 승인·투자조언 위조, 이전 판정 덮어쓰기, 오래된 원장 head, 외부 고정 head 불일치, 손상된 SQLite 이벤트 내용/해시, 비문자·비해시 필드, **정정이 참조하는 원본 자막보다 과거의 census head** 불일치
- 기존 V206·V207 질문/인용 의미 격리, 조건·예외·반박 연계 회귀와 E1 정상 연결 회귀도 그대로 재실행
- 초기 E2 V208 fixture에서 너무 짧은 `8%` 단독 인용문을 사용해 원본 인용 최소 길이 검증에 걸린 RED 기록 [44733688387](https://github.com/yhappcom/pensionport/actions/runs/44733688387)은 보존한다. 원문에 존재하는 `8%가`로 테스트를 교정했으며 검증 기준은 완화하지 않았다.

**최종 확인된 CI:** [E2 run 44734562026](https://github.com/yhappcom/pensionport/actions/runs/44734562026) — **158/158 PASS** (신규·기존 E2 87, V166/V176 회귀 53, E1 V203–V205 회귀 18). 이는 합성 자막·가짜 심사 응답으로 실제 소프트웨어를 실행한 결과다.

## E2 전체 합격에 필요한 잔여 업무

- 실제 사용자 원본 SRT/기존 V176 source journal의 현재 바이트·헤드 확보 및 모든 cue의 의미 판정 (이번 코드 검증 중 실물 비공개 원본 바이트는 확보하지 못함).
- 사용자가 요구한 원자 주장 누락·인용·반박·숫자·조건·예외의 전체 재판정과 **원본 의미상 올바른 정식 원자**의 append-only 정정 연결. V208은 안전한 *미승인 정정 영수증*까지만 지원하며 실제 원자의 승인 가능한 수정 완결을 주장하지 않는다.
- ChatGPT 두 독립 심사 단계의 실제 근거/불일치 해소와 사전 고정 정답셋 확보, 목표 정밀도≥95%, 재현율≥98%, 고위험 누락 0에 대한 실측. CI 통과만으로 의미 정확도 인증 금지.
- E2의 원본 13구간 전체 전수 합격 전 E3 진행 금지. E4 금융 근거·E5 지식 발행과 개인 포트폴리오 자문 비활성화 유지.

**공식 상태:** E1 PASS (합성 구조), **E2 IN_PROGRESS/HOLD_REAL_SOURCE_AND_INDEPENDENT_GOLD**, E3/E4/E5 NOT_RUN. `main`, E1 검증 브랜치, 동결 V123/V126/V127/V128, 비공개 사용자 데이터는 수정하지 않았다.
