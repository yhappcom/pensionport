# V233 E1 — 실제 ETF V6 호스트에서 신규 V127.1 부모 체크포인트까지 연결 (2026-11-21)

## 범위와 성공 조건

V232까지 실물 ETF 250개 자막, 68개 미승인 원자, 178개 원본 자막 격리 근거를 가지고 실제 V6 SQLite 호스트 이벤트 30개를 성공적으로 저장했지만, **해당 실물 원본에서 V127.1 부모 체크포인트로 이어지는 운영 경로를 증명하지 못했다.** V233은 그 연결과 승인 전 안전 복구 기능을 보완한다.

실제 V176 원장이나 과거 V127 체크포인트가 V228 ZIP에 있었던 것으로 주장하지 않는다. **V228의 실제 SRT와 V230 owner inventory를 기초로 신규 V127.1 checkpoint를 생성한다.** V123/E3 의미 검토 결과를 만들어 내지 않으며 E4/E5의 권한을 부여하지 않는다.

## 적용 코드

- `validation/ire-v6-frozen/v233_e1_v228_actual_parent_checkpoint_preflight.py`
- `validation/ire-v6-frozen/test_v233_e1_v228_actual_parent_checkpoint_preflight.py`

`verify_v232_source_native_host`는 변경되지 않은 V230 원본 SHA와 V231 2턴 내부 검토 note 바이트·격리원장을 재검사한 후, **V232 실제 `TransactionStore.snapshot`의 전체 이벤트 체인을 재생**하여 외부 고정 호스트 HEAD/이벤트 건수/원본 SHA/소유자 inventory SHA/13개 모델과 증빙을 검문한다. 미승인 상태인 경우에만 다음 단계로 넘긴다.

`open_new_real_v1271_checkpoint`는 개인 디렉터리 접근 모드 `0700`을 요구하고 원자적 O_EXCL 방식으로 새 checkpoint DB를 `0600`으로 만든다. 이후 기존 V127.1의 `PrivateFullVideoCheckpoint`를 실제로 호출하여 250자막을 20개 이하 단위 13개 구간으로 분할한다. 체크포인트의 계획 SHA와 HEAD는 외부 고정값과 재생 검사한다. 이미 존재하는 checkpoint는 권한이 느슨하거나 사전 고정 HEAD와 다르면 차단한다.

참고: 기존 V127 생성기를 직접 호출하면 새 DB가 비공개 권한으로 생성되지 않을 수 있음을 확인했다. 동결 엔진 본문을 수정하지 않고 V233의 **안전 진입 경로**에서 수정했다. 운영자는 반드시 이 경로를 사용해야 한다.

## 실제 ETF 재실행 검증

| 실제 실물 검증 | 결과 |
|---|---|
| V228 원본 동결 ZIP SHA | `9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397` |
| SRT 원본 SHA | `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b` |
| V232 V6 호스트 SQLite event count | **30** |
| V232 V6 호스트 HEAD | `7dd7b5b8b30d8b7233e8fa75949e2e07d48d68cc971a0a5815dead27e1540a55` |
| V127.1 원본 parent plan SHA | `4bb9ed049b60b1f41583789b23ac88cb33f2bce17ad181f7c007db56b99e6fa7` |
| V127.1 실제 child plan | **13/13개 생성** |
| child ChatGPT 정식 의미 검토 PASS | **0/13** |
| 실제 checkpoint HEAD | `0000000000000000000000000000000000000000000000000000000000000000` |
| 신규 checkpoint DB SHA | `03e78ad4687008c2a3c7397fce0f9cab2609e9ee86cd435fd2995bd635e28551` |
| SQLite PRAGMA integrity_check | **ok** |
| 신규 checkpoint 파일 mode | **0600** |
| 동일 원본 재개봉·V127 plan HEAD 재생 | **PASS** |
| 실제 V232 SQLite 사본 이벤트 변조 | `LedgerCorrupted`로 **차단** |
| 원본 V232 SQLite 원장 유지 | **30 이벤트, 기존 HEAD 일치** |
| 최종 E3/E4/E5 승인·발행 | **모두 0 / HOLD** |

V233 실물 checkpoint는 비공개 저장 영역에만 있으며 공개 Git에 개인 원본 또는 SQLite DB를 업로드하지 않았다. 비공개 증빙 ZIP은 사용자가 보관한다.

## 테스트

V233 신규 **11개 합성 부정·긍정 회귀**: 진짜 V6 트랜잭션 후 신규 V127 checkpoint 생성, 재개봉 idempotence, 호스트 SHA 또는 이벤트 개수 오류, E3 허위 승인, 실제 V127 HEAD 재개봉 시 핀 변조, 접근권한 오류, 이벤트 내용 변조, V6 inventory 오류, 새로운 checkpoint에 0이 아닌 HEAD를 주는 경우를 모두 검증한다.

기존 V230 18건, V231 10건, V228/229/V203–205 69건, V232 4건 + V233 11건 = **총 112개 자동검사 PASS**:
https://github.com/yhappcom/pensionport/actions/runs/44899159252

CI에서는 합성 입력으로 실행했고, 실물 ETF V6→V127 경로는 개인 원본으로 따로 실행했다. 구조 검증과 의미 검증을 혼동하지 않는다.

## E1 합격 판정

| 항목 | 판정 |
|---|---|
| 실제 ETF V6 원본→13 모델/구조 증빙→SQLite 호스트 커밋 | PASS (V232) |
| 실제 ETF V232 호스트→신규 V127.1 source-pinned 13개 child 계획 | **PASS (V233)** |
| 실제 비공개 체크포인트 파일 안전 접근, 재시작·원장 변조 차단 | **PASS (V233)** |
| V203 합성 적법한 V123→V128→V126 전체 승인·저장 경로 | 합성 PASS 유지 |
| 실제 ETF 68원자의 E2 정식 의미·근거 정확도 | HOLD |
| 실제 ETF 13구간의 ChatGPT 호스트 출처가 확인된 V123 최종 검토 | HOLD (수동 2턴 참조는 암호학적 호스트 인증이 아님) |
| 실제 ETF V128/E4→V126/E5 **전체 원자적 발행** | **0건 / HOLD** |
| E1 **실제 검토→정식 승인→최종 저장까지 전체 종단간** | **HOLD** |

**결론:** V232 이후 남았던 실물 호스트→V127.1 체크포인트 연결의 구조적 결함을 개선했다. 데이터 유출·승인 우회 없이 재시작·변조 차단을 증명했다. 그러나 실물 ETF 의미 판정, 호스트 신뢰도, 공식 금융근거 및 E4/E5 적법한 발행이 없는 상태로 E1 전체 합격을 부여하지 않는다. 합성 구조 PASS와 실물 승인 PASS는 별도다.
