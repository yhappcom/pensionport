# V166 E4 추가 개선 — 승인 전용 저장소 우회 차단과 B0001 실제 책 원전 교차검증

**기준:** 2026-11-17 KST. **공식 E4 판정: FAIL (부분 개선·재검증 완료), E5–E7 NOT_RUN, 엔진 NO-GO.**

## 1. 이전 실패의 수정 성과: 버전형 E4 저장소에서 레거시 V128 무승인 직행 차단

기존 V126 `PrivateKnowledgeStore`를 사용하는 구 E3→V128 경로는 **E4 근거가 없어도 합성 연구용 후보 3개를 SQLite에 쓸 수 있는** 것을 이전에 확인했다. 이를 무조건 PASS로 착각하면 안 된다.

- 신규 `v166_e4_guarded_knowledge_store.py`의 `E4GuardedKnowledgeStore`는 기존 V126의 하위 클래스이면서, **SQLite SQL authorizer**로 진짜 durable `knowledge`, `events`, `parent_publications`의 INSERT/UPDATE/DELETE를 기본 차단한다.
- 신규 공식 `run_e4_guarded_parent`는 **E4GuardedKnowledgeStore 외의 구 V126 저장소를 거부**한다. 각 자식이 동결 V123/E3 검문 및 E4 공식근거 검문에서 개별 PASS한 후에만 scoped 승인을 등록한다.
- 승인된 모든 자식이 충족될 때만 같은 실행 범위에서 V128 부모 원자적 저장을 수행하고, 범위 종료 후에는 별도 쓰기 권한이 자동으로 소멸한다.
- **실측 3개 추가 회귀:** (A) guarded store에서 직접 구 E3→V128 발행 시 `sqlite3.DatabaseError` 및 durable knowledge=events=parent=0, (B) 공식 E4 호출에 구 V126 일반 저장소 전달 시 거부, (C) 정식 합성 E4 부모 저장을 1회 완료한 뒤 같은 DB에 새 쓰기를 시도하면 다시 거부. 기존 E1–E3 및 E4 정상/반례도 전부 통과.
- 주의할 한계: 이 권한은 **해당 Python 보호 저장소 객체의 SQLite 연결에 적용되는 애플리케이션 정책**이다. 동일 파일을 개발자가 별도 일반 SQLite/V126 연결로 직접 여는 경우까지 방어하는 **영구적 파일 수준 승인 증명은 아직 없다**. E4 운영상 공식 저장 경로는 보호 객체로 고정하지만 이전 레거시 경로의 전역 제거·마이그레이션·승인 영수증 영구 기록은 남아 있다.

## 2. 실제 첫 원전 확보: 영상 #1 B0001의 서지 주장 2건 검문

- **실제 사용자 원본 SRT:** SHA-256 `638fefee007aa9122e68717b922194410ebbd7913a619bb9354f09af14468a0d`; 비공개 원자 ID `C00002` 원문 30–32cue, `C00006` 원문 79–81cue. 개인 소유 원문은 공개 GitHub에 기록하지 않았다.
- **출판사 1차 원전:** `https://www.wiley.com/en-us/The%2BDhandho%2BInvestor%3A%2BThe%2BLow%2BRisk%2BValue%2BMethod%2Bto%2BHigh%2BReturns-p-9780470043899`. V166 전용 라이브 TLS에서 Wiley 원본 **268,997 bytes**, SHA-256 `194091165060cf91580a62597849a35e6a7d4e72d6544f039f795e1629b811d1`; **원제 `The Dhandho Investor`, 저자 `Mohnish Pabrai`, 하드커버 ISBN `9780470043899`** 원문 확인.
- CI https://github.com/yhappcom/pensionport/actions/runs/44040578048 (Wiley 원전과 국세청 원문 실제 라이브 조회 성공).
- 한국어 번역서 교차자료(출판사 자체의 원천 파일이 아닌 **서점 서지 메타데이터**, 분리 표기): `https://www.yes24.com/product/goods/61941283` — 『투자를 어떻게 할 것인가』, 모니시 파브라이, 이레미디어 2018-07-05, 원서 `The Dhandho Investor`, ISBN 9791188279210.
- **B0001 `C00002`**: 화자가 한국어 제목과 저자를 말한다. SRT 이름은 '모니시 바브라'로 나타나지만 실제 출판사 저자 이름은 'Mohnish Pabrai'다. **오디오 미확인 자막 표기 가능 오류**를 교정 문맥으로 제시할 수 있지만, 원음 재대조 없이 음성 인증/정식 의미 PASS로 등록하지 않는다.
- **B0001 `C00006`**: 음역 표기 '단도 인베스터'와 출판사 원서 제목을 출처에 고정해 대조 가능하다.
- 사용자의 비공개 원본 2개 원자 및 cue 인용 해시·기존 V123 처분을 결합한 비공개 증빙 SHA-256 `68aae093e03a64c2112622fc00657243ef0ee6320bce9d6f95cbf5550ced1281`. **실물 C00002의 V123 기존 `OPEN` 판정 유지**, C00006 기존 `ACCEPT_FOR_RESEARCH` 유지. 의미/원전 검문을 *참고 증거*로만 추가했으며 ChatGPT 최종 기존 판정을 임의 수정하지 않음.
- Wiley가 출판한 서지 사실을 확인했다고 해서 투자 수익률, 손실제한 보장, 버핏 초기 파트너십 사실, 개인 적합성 또는 금융법 원전이 검증되는 것은 아님.

## 3. 최신 코드 검증·운영 주의

- CI [전체 E1–E4 회귀](https://github.com/yhappcom/pensionport/actions/runs/44040577989): 9 jobs success, 그중 E4 정책/저장소 단위테스트 **57 + 4개 책 서지 테스트 + 기존 통합시험** 성공. 초기 기존 우회 진단 `test_v166_e4_legacy_ungated_path_diagnostic`도 계속 녹색이며 이는 **위험 존재를 확인**하는 테스트이다.
- CI [실제 국세청·Wiley](https://github.com/yhappcom/pensionport/actions/runs/44040578048) 라이브 TLS 검증 성공.
- `main`·동결 V123·기존 V126/V127/V128 원본 코드는 그대로 보존했으며, 모든 신규 기능은 V166 별도 코드/테스트/검증 워크플로에만 추가했다.

## 4. E4 판정이 아직 FAIL인 이유

1. **실제 소유자 영상의 정상 E4 양성 통과 없음.** B0001에서 C00002 등 역사·서지 관련 OPEN을 임의 해제하지 않았다. 출판사 원문은 확보했지만 실제 ChatGPT 최종 보류 → 승인으로 변경하려면 나머지 원전/자막/조건·예외·이견을 개별 검문하고 정식 V123을 재실행해야 한다.
2. **법령 의역·적용범위 의미 승인 보완 필요.** 현재 E4는 정확한 원문 인용 + 일치 시행일을 요구하는 보수적인 계약이어서 통상적인 말하기식 요약 금융 발언의 의미 동등성을 통과시킬 수 없다. ChatGPT의 근거-주장 대응 검토 계약을 엄격히 확장해야 한다.
3. **전역/영구적 우회 방지 미완료.** 보호 객체에 한해서 과거 직접 호출이 막혔으나 일반 V126/SQLite 인스턴스가 같은 파일을 별도로 열어 신규 연구용 후보를 추가하는 경로에 영구적인 E4 감사 영수증 검문이 없다. 이 경로가 실제 운영 지식으로 취급되지 않도록 명확한 격리와 파일별 승인 영수증 관리가 필요하다.

**공식 결론: E1/E2/E3 PASS, E4 FAIL(상당한 개선이 있으나 정식 전수 운영 합격 아님), E5/E6/E7 NOT_RUN.**  
다음 턴에도 E4 남은 3가지 원인 해결부터 시작하고, 실제 단일 원본에 대한 정식 승인/불승인 과정을 재현하여 E4를 합격시킨 뒤에만 E5로 넘어간다.


## 5. 추가 실측 — 같은 SQLite 파일의 레거시 재개방 가능성

`test_v166_e4_primary_approval_gate.V166E4E3V128RealSQLiteIntegration.test_23_same_file_plain_legacy_reopen_still_bypasses_object_only_guard`로 다음을 실제 실행했다.

- E4 보호 객체 `E4GuardedKnowledgeStore`가 생성한 **동일 SQLite 파일**을 일반 V126 `PrivateKnowledgeStore` 객체로 다시 열고, E4 원전 검문 없이 구 E3→V128 호출.
- 합성 연구후보 3개·부모발행 1개를 쓸 수 있음을 재현. **그 결과를 E4 PASS라고 표기하지 않음**. 금융 사실 정식 승인도 False.
- 최신 종합 CI https://github.com/yhappcom/pensionport/actions/runs/44041183772 **9/9 jobs success**. 우회 진단의 성공은 **지속적 승인 강제성이 아직 없다는 실패 증명**이다.
- 그러므로 E4는 진입점 수준의 안전성은 향상됐으나 **저장소 수준의 지속적 E4 승인 영수증 결합 및 레거시 무권한 파일 접근 차단이 미완료**다. E5 착수 금지.
