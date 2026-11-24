# P0-2-05 — 범용 ChatGPT 의미 정정 컴파일러와 V6 숫자 단위 호환

기준 2026-11-24. 이전 실제 2턴 운영 시험 실패(79 잠정 참조/26 OPEN)는 유지. 개발 샘플이며 독립 정확도 또는 신규 holdout 평가가 아니다.

## 확인한 구조 원인
- 기존 stage_repair.audit_chat_atom_splits는 분할 중심이고 동일 원자 재판정, 병합, 새로운 원자와 문맥 관계를 하나의 경로에서 생성하지 않는다. V6의 speaker/stance 단일 필드는 인용된 부정, 가정, 조건, 실제 신원을 모두 표현하지 못한다.
- 이전 70개 shadow에서 원문의 혼합 수량/금액 규모/거래 단위를 보존한 참조가 기존 audit_host_atomic_exchange의 legacy NUMBER census에서 거부됐다. 실제 frozen shadow70을 실행해 HOST_ATOM_NUMERIC_REF_NOT_IN_SOURCE 재현. 기존 68개는 통과했다.
- 숫자 전체 참조를 허용하더라도 shadow70의 전사 혼합 수량 표현을 원문과 다른 정상화된 명제로 변환한 것은 exact-unit 판정에서 거절돼야 한다. 이전 shadow70은 수정하지 않고 HOST_ATOM_COMPLETE_PROPOSITION_NUMBER_UNGROUNDED로 HOLD 유지.

## 범용 개선
- ire/v6/chat_revision.py: 실제 ChatGPT가 원문 근거와 이유를 입력하면 ADD/REVISE/SPLIT/MERGE를 새로운 V6 원자 및 cue disposition으로 컴파일. 자동 ID/owner, 수정 전후 원자 digest, 이전 문맥과 조건·예외 유지, 분할 자식에서 제외된 기존 qualifier에 대한 명시적 근거, 검토되지 않은 cue OPEN 유지. 정정·분할·병합·추가에서 원본은 불변.
- 역할과 실명 인증 분리, DIRECT/REPORTED/UNRESOLVED attribution과 polarity, modality, correction의 독립적인 private typed rows. Legacy stance가 표현할 수 없는 조건·가정은 보수적으로 UNRESOLVED 유지. typed row는 출처 발언의 채팅 해석일 뿐 사실, 신원, 독립 gold, 공식 금융 승인 아님.
- 기존 cue numeric census와 원본 영수증 digest 유지. atomic_exchange.COMPLETE_NUMBER 및 audit_complete_numeric_references는 완전한 원문 숫자/단위를 검사하고 새 typed revision은 strict 경로 사용. 원래 legacy 기록의 구조 호환을 유지하며, expanded reference 사용 시 모든 참조와 명제를 exact-unit 검사. 임의 숫자 정상화, 단위 변환, 파생 계산의 원문 숫자 위조 금지. 지원 문법의 한계는 명시적이며 전사 오류 판단은 ChatGPT 담당.
- 새 컴파일러가 실제 V6 native exchange, window_models, window_reviews를 생성한다. 기존 host store에 넘기려면 source/owner/prior relations/prequarantine 등 기존 필수 입력을 충족해야 한다. 금융 승인·지식 출판을 우회하지 않는다.

## 실제 자료 재실행
원본250·동결68·이전 shadow70 SHA 재확인. 개발 샘플의 기존 10개 원자에서 9개 정정·1개 분할, 별도 원자 1개 추가, 12개 typed replacement/added atoms. 원본68→새 미승인70. 기존 인용·조건 등 문맥 보존 및 전체 V6 native audit 통과, 2회 컴파일 동일 결과. 기존 원본의 V6 atom digest 그대로 유지. 원본의 legacy UNRESOLVED cue 177→171, UNKNOWN speaker 68→58, native UNRESOLVED stance 68→61. 이는 개발 샘플 내 구조적 상태 변화이며 의미 정확도 향상률이 아니다. 171 cue와 58/61 상태, 독립 참조 미완결, 실제 금융 승인 미완결. prior 79-reference/26 OPEN 실패 데이터도 변경하지 않음.
- 실제 source.py와 변경 전 atomic_exchange.py는 Git blob 일치. 로컬 추출 의존성 일부를 사용한 재실행이며 전체 GitHub 환경의 E1~E5 검증이라고 주장하지 않는다. 새로운 로컬 범용 시험 12개 통과. 실제 V6 SQLite host batch + idempotency를 대상으로 한 synthetic integration test 1개를 추가하여 전체 CI에서 확인할 계획; 독립 정확도 인증 아님.
- private ZIP: SHA 1daf8a6d9c32838fc3ddf0bc3a6ca2e414242952e8d34fe0f18cb4f93576964c; Library libfile_0b961d75f8b481918ea48059599e5568.
- 독립 gold 0, 정밀도·재현율·고위험 FN null, E3/E4/E5 승인 0. 현재 순서 16 PASS / P0-2-05 HOLD / 후속 43 BLOCKED. 변경 후 CI 실측과 새로운 평가자료의 사전 동결이 필요. 기존 결과/합격 기준/정식 상태 변경 금지. 추가로 해결할 수 있는 실패는 다음 항목을 열지 않고 현 항목에서 해결한다.
