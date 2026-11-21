# V232 E1 — ETF 실원본 V6 SQLite host 커밋 PASS · 최종 승인·발행 HOLD (2026-11-21)

## E1의 실제 진전

**V230/V231의 실물 실행 미입증 결함을 해결했다.** V228 동결 ETF 원본과 V231 별도 사용자 요청 이후 작성한 비블라인드 내부 2턴 검토 영수증을 로컬 비공개 실행 환경으로 가져와, **GitHub 커밋에서 그대로 추출한 실제 V6 코드를 실행**하였다. 이번에는 합성 fixture나 영수증 형태검사만으로 성공을 선언하지 않는다.

- 실제 영상: `LVE7XN_esTc` ETF 원문 250개 자막, 미승인 V6 원자 68개, 13개 구간
- 동결 소스 ZIP SHA-256: `9f5a281191502bb30cb78ff17d2b08f6887f55b836cee67e00d7309770efa397`
- SRT SHA-256: `e4aef32c007bc5e9f1ac6c3e18764ddc1b766e430893127cf98abe632c70301b`
- V228 1턴 freeze head: `c7edf0a2ffffcdb2654c6f6006efe16254ee06afa5cd16b5481b8d2edee620d2`
- V231 별도 2턴 내부 검토 기록 head: `b489535a74f7600a050f8daa92c21871230b455edfc8dc35e5696f0070eef102`
- 출처 기반 V145 격리 원장: **178** 미해결·의심 원문 자막, 실제 bytes SHA `07ef6ef2cbba6a1ebb3262086c2c7cda6f89e59cf5c79280bd79bbd0bf500f0f`. V231 엔진 함수가 검토 노트와 전 행을 실제 원본 기준으로 연결 검증해 통과함.

## 보호된 prior 145개 실물 읽기

본래 Git에 존재하는 다음 3개 본문을 각각 **Git blob SHA-1 재계산 후 일치 검증**했다.

| 지식 원본 | 고정 Git blob SHA-1 |
|---|---|
| `data/claims.jsonl` (116개) | `ab5af7eea02e65d5e36174546a2a94f4cc642d92` |
| `ire/v5/advisory_knowledge/p4_integrated_scoped_education22_20261106.json` (22개) | `bfb446ffb1dd40caa1ed03088d088c9a1ba7490f` |
| `ire/v5/advisory_knowledge/p4_p3_incremental_education29_20261106.json` (추가 7개) | `b92573dbefb0f22d3a3a266685415c538b4f7a72` |

원자 68개 전체에 실제 기존 지식의 검증된 content SHA를 가진 **OPEN pending relation**을 부착했다. 이는 기계적 검색 후보이며 동치·충돌·확장·신규성 판정이 아님. 전 항목 `independent_semantic_review_verified=false`, `personalized_action_approved=false`. 검토 중 단어 겹침이 없는 원자 4개가 무관한 연금 지식에 연결되는 예비 결과를 확인해 그 장부를 별도로 보관하고, 넓은 상품구조 일반 원칙으로 바꾼 후 새로운 **최종 로컬 호스트 원장**을 별도로 실행해 성공했다. 더 이상의 의미 확정은 E2에서 필요하다.

- 최종 비공개 pending 원장 SHA-256: `530db35aeff0a6f9d7eaa3de99d0f7657846ba4eb0541f1b0be3063eec5e54ab`

## 실제 V6 호스트 트랜잭션 (합성이 아님)

로컬 access-controlled private SQLite(`0600`, 부모 폴더 `0700`)에서 다음 실제 프로덕션 호출을 연결했다.

`read_v228_source_native → verify_real_turn2_private_custody → audit_prior_candidates → audit_host_quarantine_preflight → TransactionStore.create_scope → attest_source → attest_owner_inventory → submit_host_atomic_batch`

- 실제 SQLite: **스코프 1, 이벤트 30**, 구간 모델 13/13 및 구조 증빙 13/13 기록
- 새로 연 별도 `TransactionStore`의 verified snapshot에서 **이벤트 체인 head 일치**
- V6 최종 이벤트 head: `7dd7b5b8b30d8b7233e8fa75949e2e07d48d68cc971a0a5815dead27e1540a55`
- 최종 SQLite 파일 SHA-256: `bf94bbea7f032dd75472c65f7b531bddee853c00875d3a75b10d809a0033ccd1`
- 안전한 공개용 구조 영수증 SHA-256: `babcf3a29096f38475159c7670e18dd3971ebd6290061d733dbb0a83c9511034`
- `PRAGMA integrity_check=ok`; SQLite 사본의 event_json 변조 시 `LedgerCorrupted`로 차단. 원본 이벤트 체인은 유지.
- `knowledge`와 `parent_publications` 발행 테이블 없음. 지식 합병·개인 투자권고·최종 승인은 **0**.

**한계:** V6 snapshot의 `source_attestation_recorded=true`지만 `source_original_bytes_verified=false`이며, `verified_proofs=0`, `research_report_closed=false`, `engine_quality_certified=false`, `p0_go=false`다. 이는 source custody + native structural host staging이 실물 성공했음을 뜻하지, 최종 연구 의미 인증이나 전체 V123/126/128 저장 검증을 뜻하지 않는다. V231은 호스트의 USER 메시지 ID를 암호학적으로 증명할 수 없고 E2 정답셋도 미확정이다.

## 회귀 · 저장 경계

GitHub [V232 신규 테스트 포함 CI](https://github.com/yhappcom/pensionport/actions/runs/44872445663) **101/101 PASS**:
- V230 합성 source-native 경계 18건
- V231 합성 검토 note/격리 SHA 경계 10건
- V228/229 및 V203–205 합성 회귀 69건
- V232 합성 2턴 검문 이후 실제 V6 SQLite 긍정경로 + prior 누락·승인 위조·보호 blob 변경 부정시험 4건

CI는 합성 데이터 사용이므로 **실제 ETF 실증은 별도 오프라인 비공개 SQLite 실행**이 근거다. 안전을 위해 원본 비공개 ZIP, 검토 메모, pending relation 원문, SQLite 모두 **GitHub 업로드하지 않았다.** `main`, frozen V6 및 V123–V128, 기존 V228 ZIP 불변.

## 합격 경계

| 인증 층 | 최종 판정 |
|---|---|
| V203 합성 구조 연결 | PASS |
| V228 실물 source·250 cues·68 atoms custody | PASS |
| V231 실물 source-note·178 격리 증빙 연계 | PASS (비블라인드·수동 2턴) |
| **V232 실제 ETF V6 source-native host SQLite commit** | **PASS — 최초 실증** |
| 실제 E2 전수 의미·화자·조건·중복·독립 정답 정확도 | HOLD |
| E3 호스트 인증 ChatGPT 최종 승인 | HOLD |
| E4 승인 권한, E5 원자적 지식 발행 | HOLD |
| **E1 전체 입력→검토→적법 승인→지식 최종 저장** | **HOLD** |

**결론:** 이전에 실물 호스트 실행 단계에서 막혔던 E1 장애는 해소했다. 그러나 E1 전체 합격은 실제 승인된 13구간으로 V123/E4/E5를 통과하고 완전한 부모 저장이 증명될 때까지 보류한다. 이는 E2/E3 검증을 생략하거나 가상 검토로 우회하라는 뜻이 아니다.
