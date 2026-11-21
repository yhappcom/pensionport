# V230 E1 보완 — V228 실원본 → 신규 V6 입력 이관, E3/E4/E5 분리 HOLD (2026-11-21)

## 요약

V229는 V228 원본을 V203의 V176 형식으로 강제로 바꾸지 않았으나, **실제로 사용할 대체 이관 경로가 없었다**. V230은 동결 V228 원본과 68개 미승인 V6 원자를 **새로운 출처 보존형 V6 입력**으로 취급하는 경로를 추가한다. 기존 V176 원장을 복원했다고 주장하지 않는다.

- 원본: ETF \`LVE7XN_esTc\` 개인 동결 ZIP, 원본 250자막, 68 미승인 원자, 2,278 lexical 쌍. 소유자 자료는 공개 저장소에 배포하지 않음.
- 동결 ZIP SHA256: \`9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397\`
- 원본 SRT SHA256: \`e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b\`
- V228 freeze head: \`c7edf0a2ffffcdb2654c6f6006efe16254ee06afa5cd16b5481b8d2edee620d2\`
- **동결 ZIP 내용은 변경하지 않는다.** 실제 V176 SQLite와 V127 checkpoint는 해당 ZIP 안에 존재하지 않는다.

## 새로운 E1 seam

\`v230_e1_v228_source_native_handoff.py\`

1. **원본이 실제 입력:** V228 원문 ZIP·manifest·첫 턴 head·SRT SHA를 외부 pin과 비교하여 모두 재검사. 기존 \`verify_turn1_frozen\` 및 frozen V6 atomic exchange 재검사 재사용.
2. **새로운 V6 inventory, V176 위조 없음:** 검증된 원본의 video/source/manifest/cue census만으로 새로운 V6 운영 목록을 구성. 별도 SHA를 요구. \`owner_identity_verified=False\`를 유지하며 이는 역사적 V176 review가 아님을 명확히 한다.
3. **V6 host-only writer:** 작업자가 source inventory pin·보호된 prior knowledge 116+29 본문과 원자별 관계 OPEN 기록·미해결 자막별 출처기반 ChatGPT 격리 검토 원장·새 private \`TransactionStore\`·명시적 실행 동의를 입력한 경우에 한해 \`create_scope → attest_source → attest_owner_inventory → submit_host_atomic_batch\` 호출. 모델·원자·원문 확인용 영수증만 생성하며 V123/V126/V128 승인·저장 함수는 호출하지 않는다. 실제 작성 전 \`audit_prior_candidates\`를 요구하므로 관계 입력 없는 임의 통과 불가.
4. **V229와 V228 영수증 형식 충돌 수정:** V228 2턴 영수증은 \`first_frozen_head_sha256\`, \`e4_authorized\`와 **개행을 포함한 V228 canonical hash**를 쓴다. V230은 실제 필드명·원문 250행·원자 68행·서로 다른 수동 메시지 참조·review hash를 검문한다. 수동 메시지 ID를 ChatGPT 호스트가 암호학적으로 보증한 것으로 취급하지 않는다.
5. **엄격한 상태 분리:** V6 host-only 등록은 E1 운영 승인/저장 종단간의 증거가 아니다. E2 독립 정확도·E3 호스트 최종 검증·E4 적법 승인·E5 전체 지식 저장은 계속 HOLD.

## 검증 기준과 현재 한계

- 공개 합성 fixture를 사용하는 V230 18개 회귀 검사를 추가했다. V228·V229·V203/204/205 기존 회귀도 함께 실행하는 별도 GitHub Actions 워크플로를 추가했다. 기존 15개 초기 CI에서는 PASS였으며, 실제 V6 host 긍정 합성 경로를 추가했을 때 V6 잔여 원문 격리 검문에서 1회 RED가 발생했다. 보호장치를 완화하지 않고 필수 `source_prequarantine` 입력을 추가하여 해당 정상 합성 경로를 재검증했다. 내용이 바뀐 동수 원자의 거짓 이관을 차단하는 회귀시험도 포함한다.
- 사용자 ETF 실물은 기존 private V228 ZIP SHA와 8개 멤버의 byte integrity가 확인되었으나, V230의 새로운 V6 host-only SQLite writer를 **개인 실물로 성공 실행했다는 증거는 별도**다. 원본 ZIP과 native 외에, 사전 확정 inventory pin 및 보호된 legacy 원문과 68개 원자 전체의 pending relation ledger가 필요하다.
- 실제 독립된 TURN2 사용자 명령에 의한 250 자막·68 원자 원문 판정 및 E3 최종 서명은 아직 없다. 이 검토 없이 E1 전체 real owner PASS, E2 PASS, E3 승인, E4 승인, E5 지식 발행을 주장하지 않는다.
- 작업 브랜치만 수정; \`main\`, 원래 frozen V6/V123/V126/V127/V128 구현, V228 private ZIP 비변경.

## 최종 상태표

| 항목 | 상태 |
|---|---|
| 기존 V203 합성 구조 종단간 | PASS 유지 |
| V228 실원본 SHA·자막·원자 재확인 | 1턴 내용 무결성 PASS |
| V228 → 새로운 V6 **source-native 입력 계약** | V230 구현 / 합성 테스트 별도 |
| V228 → 새로운 V6 **실물 host SQLite 이벤트** | NOT_YET_PROVEN |
| V228 → ChatGPT 실제 2턴 → V123 승인 → V126/128 저장 | HOLD |
| E2 금융 의미 정확성 | HOLD |
| E3/E4/E5 최종 승인·발행 | 0 |

소스 기반 입력 모델 전환으로 V176 역사적 원장 파일을 복원해야만 V228 원문을 V6가 읽을 수 있다는 **불필요한 결합을 제거**했다. 그러나 완전한 E1 운영 PASS를 인증하려면 실제 호스트 commit과 2턴 승인·저장 경로의 추가 증거가 필요하다.
