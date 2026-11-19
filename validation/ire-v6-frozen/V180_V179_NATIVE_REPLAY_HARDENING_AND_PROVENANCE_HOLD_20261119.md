# V180 — V179 원본 실증과 V176 네이티브 재생 코드의 증빙 분리
검토일: 2026-11-19 KST. 대상: `LVE7XN_esTc`, 소유자 원본 SHA-256 `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`.
상태: **CODE_PATCH_APPLIED / SYNTHETIC_CI_69_OF_69_PASS / PRIVATE_NATIVE_PROOF_NOT_RECONCILED / V123-E4 HOLD / E5=0**.

## 확인된 GitHub 근거
- PR #71의 현재 공개 보고서는 250개 원본 자막 1차 의미검토, 62개 예비 원자, 두 턴 14개 별도 SQLite 이벤트, 12개의 최초 분류 보류를 주장하며, 실제 V176 `prepare → submit`은 NOT_RUN이라고 명시한다.
- 이전 턴에 보존된 **별도 Library 스테이징 검증 보고서**는 V176 네이티브 실물 250/250, 14개 네이티브 제출, 22개 1차 OPEN, V6 보류 24, 원자 61, 의미 누락 의심 68을 기록한다. 그러나 이 결과의 원본 판정·SQLite·비공개 실행 로그를 본 공개 브랜치에서 교차 확인하지 않았으므로, 여기서 실물 PASS로 새로 인증하지 않는다.
- 두 공개/스테이징 보고서의 별도 원장 종료 SHA가 서로 다르다: PR 보고서 `463e33f35909a1e47ecd1f11020c7caccad596508c1ad77bc58afc7cae67c23d`, 스테이징 보고서 `22c96c126a36fb93e092a2adba05aa66981ac92e4c7a6f31be50f5ef992ef53b`. 이 둘을 동일 원장이라고 간주하지 말 것.
- 12개 source-only OPEN vs 22개 1차 OPEN의 차이는 기준/이벤트/행 단위 대조 없이는 해소되지 않는다. V6의 24개 UNRESOLVED와도 서로 다른 지표이다.

## 본 PR의 코드 수정
1. `v178_coldstart_chat_packet_bridge.py`: 기존 ChatGPT 예비 원자에만 존재하는 `claim_id/evidence_verified/native_v123_approved` 필드를 두 승인 플래그가 **False**일 때만 V176 정식 필드로 투영한다. 원문의 명제·조건·예외·숫자·인용은 보존하고 다른 임의 필드나 승인 True를 거부한다. 또한 패킷 내 이전 원장 헤드와 별도 외부 핀 일치를 강제한다.
2. `v176_chat_engine_loop.py`: 위험 신호가 있는 `NON_RESEARCH` 자막을 `prepare_nonresearch_risk_revisit`로 재발행하고, ChatGPT가 작성한 근거가 있는 응답만 `submit_context_revisit`에 추가 이벤트로 저장한다. 최초 판정은 삭제하지 않는다. `v176_chat_engine_cli.py`에는 `repair-noatom` 명령을 추가한다.
3. 회귀시험: 잘못된 출처 인용·정정 재생·원장 해시 변조·정식 금융 승인 위조·예비 필드 오염·패킷 체크포인트 불일치 차단을 합성 자막으로 테스트한다. CI PASS여도 원본 250개 의미 승인으로 취급하지 않는다.

## 실제 원본 실증의 다음 승인 조건
- 사용자 소유 원본 SRT·두 턴 판정 이벤트·SQLite 스냅샷·원장 해시 2종을 비공개로 재대조하여 단일 계보 또는 별개의 실행임을 확정한다.
- 250개 각 자막의 최초/최종 분류 및 62개 원자 후보에서 61개 네이티브 원자로 변환되는 내역, OPEN 12/22/UNRESOLVED 24 차이를 공개되지 않는 행별 리포트로 검문한다.
- 누락 경고 68건을 출처 근거와 연동하여 실질 누락을 ChatGPT가 독립 판단하며 조건·예외·화자 구조를 확정한다. 원음/화면 미확인 발화는 OPEN 유지.
- 금융 원문 바이트·효력 시점·적용 범위 원천증빙 후 V123/E4 승인 관문 검증. 모든 필수 구간 PASS 전에 E5 발행 금지.

**금지:** V176 합성 CI를 실물 의미 검토의 정밀도/재현율 또는 금융규정 승인으로 표시하지 않는다. `main`, 동결 V123/V126/V128 및 사용자의 비공개 원본은 변경하지 않는다.

## 실제 GitHub Actions 검증
- 수정 검증 HEAD `23465918bf0b34d38a834aa61101c90628ebd208` 기준, Push/PR 워크플로 각각 `completed/success`.
- Python 3.11.18: 신규 V179 15/15, 기존 V176~V178 54/54, 총 **69/69 테스트 PASS**.
- Push: https://github.com/yhappcom/pensionport/actions/runs/44519931783
- PR: https://github.com/yhappcom/pensionport/actions/runs/44519942336
- 실물 250자막 비공개 SRT/판정 DB는 CI에 투입하지 않았다. 따라서 실물 V176 재생의 독립 재실행 PASS와는 구분한다.
