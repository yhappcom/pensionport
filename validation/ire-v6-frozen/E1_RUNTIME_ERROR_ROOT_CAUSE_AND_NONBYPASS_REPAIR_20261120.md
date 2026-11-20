# E1 반복 런타임 실패 분석 및 재발 방지 — 2026-11-20

**범위:** GitHub PR #74, V176→native V6→V123/V128/V126 E1 구조 연결. 보호 `main`, 기존 V166 E1 PASS, 비공개 자막·원장 불변. E2~E5 의미·금융 승인 개선 미착수.

## 확인한 실제 실패 및 수정

| 실행 | 실제 원인 | 분류 | 대응 |
|---|---|---|---|
| PR #73 V201 최초 신규 시험 | `TransactionStore`가 요구하는 `.db` 확장자 대신 `.sqlite` 사용 | 테스트 초기화 오류 | `.db`로 수정 |
| PR #73 V201 신규 시험 재실행 | genesis `0` 해시를 가짜 head라고 사용, native `create_scope`는 같은 명령에 멱등적으로 반응 | 잘못된 부정 테스트 / 재시작 경계 | 존재하지 않는 `f` 해시로 부정 시험 교정, 신규 scope 기존 재사용 거부 |
| PR #74 E1 positive transport 최초 테스트 작성 | `unittest.TestCase.run`을 helper로 덮어쓸 위험 | 테스트 런타임 API 충돌 | helper를 `_execute()`로 수정 |
| V204 독립 E1 RED test #04 | native batch가 `HOST_BATCH_UNRESOLVED_SOURCE_RESIDUALS`로 먼저 안전 차단하는데 테스트는 후단 `EMPTY_WINDOW_NOT_EXPLICITLY_NO_ATOM`만 요구 | 단일 오류 메시지를 잘못 가정한 assertion | 두 선행·후행 차단을 모두 인정하고 **모델·구조 proof 기록 0**을 검사. 위험 입력 승인 없음 |
| 기존 `Independent Research Engine - clean-room foundation` | 과거 고정 정책: `GITHUB_HEAD_REF`가 지정된 2026-11-09 V6 브랜치가 아니면 `validation/ire-v6-frozen/` 변경 차단. PR #74 E1 검증 문서·시험 수정까지 제한 | **의도된 보호 정책 BLOCK (Python runtime crash 아님)** | 정책 우회/변경 금지, 클린룸 job의 실패를 정책 충돌로 명시 보고. 해당 legacy job의 PASS를 허위 주장하지 않음 |

## 수정 뒤 실제 결과

- **V201 E1 compatibility:** <https://github.com/yhappcom/pensionport/actions/runs/44718816951> — SUCCESS, 431/431 unit tests.
- **Isolated E1 positive/negative:** <https://github.com/yhappcom/pensionport/actions/runs/44718816274> — SUCCESS, 58/58 unit tests.
- **기존 legacy clean-room:** <https://github.com/yhappcom/pensionport/actions/runs/44718816357> — FAILURE at `HISTORICAL_OR_OTHER_FILE_MODIFIED` policy. No assertion this workflow is green.
- 수정 커밋: `d517f6d8455ff5bfa526b036b9d5ebd086899c94`.

## 재발 방지 운영 규칙

1. 실제 CI traceback을 보고 **코드 예외 / 합성 fixture 오류 / 안전한 fail-closed 결과 / 보호 정책 차단**을 분리한다. 새 버전만 추가하면서 이전 실패를 숨기지 않는다.
2. 검증 시험은 오류 문구의 호출 순서가 아니라 **안전 불변식(원장 이벤트 증가 0, 미검토 승인 0, 재개 체크포인트 불변)**을 우선 검증한다.
3. 테스트 helper는 `setUp`, `run` 등 `unittest.TestCase` 생명주기 메서드를 덮어쓰지 않는다.
4. `TransactionStore`용 신규 데이터베이스 파일은 `.db` 확장자, 비공개 권한·폴더 요건을 만족한다.
5. 동시 개발 변경이 섞이지 않도록 정확한 검증 SHA를 별도 브랜치에 고정하고, 기존 V166·V201 결론을 바꾸지 않는다.
6. 오래된 클린룸 게이트를 변경해 CI 녹색으로 위장하지 않는다. 정책이 실제 현행 검증 경로와 불일치하면 해당 보호 정책의 **별도 정당한 변경 승인·테스트**가 필요하다.

**판정:** 재현된 반복 Python/테스트 실패는 수정돼 두 E1 CI가 통과. 그러나 legacy clean-room은 정책상 BLOCK이며, 사용자 앱 또는 ChatGPT 플랫폼의 모든 런타임 오류가 사라졌다는 의미가 아니다. 전체 E1 구조 합격 판정은 별도 단계 관문에서 결정한다. E2~E5 작업 금지.
