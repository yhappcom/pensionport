# P0-0-03 — 선행 체크리스트 재감사·Actions 27개 전수 정리 (2026-11-22)

**대상:** `yhappcom/pensionport` 통합 브랜치 `audit/full-repository-snapshot-20261122`. `main` HEAD `d613fd201f4bb077f1ccc74d28dee937b11bfcb2` 불변. **실제 V3/V5/V6 전체 품질 CI 합격이나 E1~E5 실물 최종 승인 결과가 아니다.**

## 1. 이전 완료항목(P0-0-01·02)의 재검문

- [x] `P0-0-01`: 현재 실제 브랜치는 `main`+통합 2개, 기존 `main` 불변, 98/98 역사 HEAD 계보 보존. 원래 2,364개 고정 트리 경로·Git blob SHA·크기 불일치 0, 과거 삭제 96개 영수증 보존.
- [x] `P0-0-02`: 현재 14개 원천 증거 SHA 연결, 로스터 `791/703/88`와 레거시 `157/116/211` 서로 다른 분모, E1~E5 실제 최종 RELEASE=`HOLD`, ETF 실제 E3 정식 `0/13`, E5 실제 `0` 유지.
- 선행 두 항목의 정식 완료 범위 밖인 **비공개 SRT 원문·독립 금융 gold·owner 봉인·완전한 E1~E5 종단간 운영**은 이번 재감사도 수행하지 않았다. 적법한 HOLD가 있으므로 당시 코드·문서 무결성 PASS를 취소하지 않는다.

## 2. Actions 파일 전수 대상과 분류

[27개 워크플로의 개별 이름·변경 전후 Git blob SHA·트리거·권한·승계 분류 원장](IRE_P0_0_03_WORKFLOW_AUDIT_INVENTORY_20261122.json)이 기계 판독 기준이다.

| 분류 | 개수 | 현재 처리 |
|---|---:|---|
| `ACTIVE_PUSH` | **1** | `full-all-branch-history-audit-20261122.yml` — 통합 브랜치 push 시 98 HEAD·main·상태·체크리스트·워크플로 보안 검문 |
| `MANUAL_ONLY` | **1** | `full-repository-snapshot-audit-20261122.yml` — 정의상 `workflow_dispatch`만 있고 nondefault branch의 실제 수동 실행 가능성은 증명하지 않음 |
| `LEGACY_RETIRED` | **25** | V3/V5/V6/과거 실험 시험 정의 유지·인증범위 분리. 기존 push/PR 대상은 폐기된 브랜치로 한정. 현행 통합 브랜치의 필수 품질 CI에 포함되었다고 주장 금지 |
| 과다 GitHub token `contents: write` | **0** | V5 구 관리 워크플로의 쓰기권한 제거 |
| 브랜치 범위 없는 `pull_request` | **0** | 세 개 과거 PR 트리거 제한 |
| 현재 통합 브랜치에 중복된 레거시 push | **0** | 과거 버전 CI 폭증 및 오인 방지 |

**삭제된 브랜치 대상의 옛 워크플로를 모두 새 통합 브랜치 push에 연결하지 않는다.** 그렇게 하면 오래된 코드/계약을 동시에 실행하고 상충하는 PASS/FAIL을 쏟아내 재현성을 해친다. 기존 25개는 *이력 자료로 유지*하되, 다음 P0-0-04에서 **실제 공통 HEAD의 정식 단일 품질 CI**를 구성한다.

## 3. 실제 확인한 결함과 개선

1. `ire-cleanroom-gate.yml`: 과거 `pull_request`에 base branch 필터가 없던 범위 과다 → 퇴역한 cleanroom base만 대상으로 한정.
2. `ire-v5-p3-p4-one-turn.yml`: 역시 `pull_request`에 base branch 필터가 없음 → 퇴역한 V5 base만으로 한정. 구 one-turn 구현은 현재의 *실제 별도 사용자 2턴* E3를 대신하지 않는다.
3. `ire-v169-chat-resume.yml`: 첫 자동 27개 검문에서 **세 번째 무제한 PR 트리거 검출**, 실제 CI RED [44981905814](https://github.com/yhappcom/pensionport/actions/runs/44981905814) → 퇴역 V168 base만으로 한정하고 전용 회귀시험 추가.
4. `ire-v5-app-control.yml`: 구 자동 상태 쓰기 함수에 부여된 `permissions: contents: write` 제거 → `contents: read`. 퇴역 경로의 이전 `git push` 코드는 활성화되더라도 이 권한으로는 성공해서는 안 되며 기능을 되살릴 때는 별도 승인·보안 설계가 선행되어야 한다.
5. [정적 범위 검사](../scripts/ire_workflow_audit_gate.py) 및 [19개 양성·음성 시험](../scripts/test_ire_workflow_audit_gate.py)을 기존 브랜치 관리 CI에 연결. 실제 27개 파일과 전체 목록/고정 blob SHA(가변인 현재 관리 워크플로 자기 자신 제외), push·PR 활성 대상, job/top-level 읽기권한, 분류 개수를 **실제 현재 checkout에서 검증**.

재검증: [Actions 44981957332](https://github.com/yhappcom/pensionport/actions/runs/44981957332) — Python 3.11.18; 원래 17개 체크리스트 정책 + 23개 단일 상태 원장 + 19개 워크플로 보안, **59개 정책 회귀시험 PASS**. `WORKFLOW_AUDIT_GATE_PASS total=27 active_push=1 manual_nondefault=1 historic_dormant=25 contents_write=0 broad_pr=0 full_engine_ci=NOT_YET`.

## 4. P0-0-04 인수인계: 현행 통합 CI 구성·실행 (별도 항목)

1. 기존 25개 역사 워크플로의 **검증 목적/명령/테스트 범위만** 재사용하고, 폐기한 브랜치별 YAML을 통째로 재활성화하지 않는다. checkout과 작업 헤드는 **현재 통합 브랜치 정확한 SHA**로 고정한다.
2. Python **3.11.18**에서 단위/통합/엄격 사전검사/보안/동결 V6/V123/E4/E5/V5 앱 및 E1 최신 브리지 전 범위를 실제 독립 스텝으로 실행한다. 실패가 나면 그 항목을 HOLD/FAIL로 보고하고 P0-0-05로 넘어가지 않는다.
3. 공식 외부 금융 원문 및 개인 원본을 공개 CI에 올리지 않는다. 실제 원본 의미·별도 사용자 두 턴·금융 원전 승인·E5 발행은 코드 CI와 분리한다.
4. **새 브랜치 만들기 금지**. 워크플로 등록·해제/실패 시 GitHub Actions 영수증을 체크리스트에 연결하며, 신규 관리용 `contents:write` 부여 금지.
5. 통합 브랜치의 workflow_dispatch 기능과 GitHub default-branch 제약, 사전 branch Ruleset 부재를 정확히 명시하고, 관리자의 Ruleset 설정은 별도 관리/권한 작업으로 추적한다. 자동검사의 성공은 이미 push된 악성 커밋을 사전에 차단한 사실을 의미하지 않는다.

## 5. 완료판정 및 사용자 보고

**P0-0-03의 합격 기준:** 27개 모두 개별 분류, 과거 경로·base 필터 확정, read-only token, 0 무제한 PR, 0 통합 브랜치 레거시 push, 정확한 Git HEAD에서 양·음성 CI PASS, 사용자 시작·종료 보고. 위 27개 검사에 실패하면 `P0-0-03`에서 계속 수정, **P0-0-04 차단**. 현재 27개 소프트웨어 정책 검사는 성공했지만 `P0-0-04`의 전체 엔진 CI는 *NOT_RUN*.

**위험·한계:** 비공개 원본 실증 및 Ruleset 생성 사전 통제는 이 항목 범위에 포함되지 않는다. 구 PR 분기를 같은 이름으로 재생성하는 위험을 고려하여 브랜치 수/원본 HEAD 사후검증과 관리자 Ruleset 필요성을 계속 명기한다.
