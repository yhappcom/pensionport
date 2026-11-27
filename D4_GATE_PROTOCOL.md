# D4 P0-3~P0-5 — GateEngine 후보 통합 경로 (2026-11-27)

## 범위와 판정
- 기존 `engine.py`와 `d4_quality.py`는 변경하지 않는다. `d4_gate.py`의 `GateEngine`이 신규 DB에 대한 **정식 후보 실행 경로**이다. 기존 DB는 변경하지 않고 새 경로에서 사용하려면 사본을 명시적으로 이관한다.
- 기술 시험 PASS와 신규 원본의 2턴 운영 PASS를 분리한다. #261/#280/#263 HOLD는 유지한다. 신규 모듈은 의미 추론, 원자 분해의 완전성, 금융 사실 검증, 자연어 검색을 자동 인증하지 않는다. ChatGPT가 직접 검토하고 기록한다. 독립 인증 미측정.

## DB 및 실행 방법 (직접 Python 호출, 단일 스레드)
1. `GateEngine.migrate(source_path, target_path, expected_sha)`로 원본 DB의 SHA를 검증하고 읽기 전용으로 복제한다. `target_path`는 존재하지 않는 새 경로여야 한다. 기존 영상/판정 및 지식 head를 보존하고 모드 표식을 `D4_GATE_1:research`로 변경하여 일반 Engine으로 열 수 없게 한다. 새 빈 DB는 `GateEngine.create(path, mode)`로 생성한다. SQL/임의 코드 수정까지 차단하는 보안 경계는 아니다.
2. 신규 후보 DB는 registry 검토 전 PENDING 상태이다. 기존 활성 지식의 전체 목록, 조건·예외·보완 관계를 ChatGPT가 실제 검토한 뒤 `bootstrap_registry(specs, reviewed_ids, review_note)` 실행. 기술 시험의 진단용 registry를 운영용으로 재사용하지 않는다. 각 edge는 `from`, `to`, `kind`(REQUIRED_CONTEXT/CONDITION/EXCEPTION), `reason`을 갖는다. 양단은 활성 qualified_id이다. 전체 검토 선언은 수동이며 완전성을 코드가 보장하지 않는다.
3. 1턴 `prepare(raw, terms)` → 원문 연구 및 공식 근거 검색 → `save_draft(packet)`; `context_query`에는 기존 직접 검색과 필수 문맥이 함께 반환된다. 원본 전용 파일과 초안 저장본을 분리한다. 외부 파일의 초안 열람은 프로그램이 강제로 차단할 수 없으므로 운영 규칙으로 금지한다.
4. 2턴 `source_only(sid)`로 원문 확인 → 원자 참조 및 비주장 자막, 질문 기준을 독립 작성 → `freeze_reference(sid, reference, queries, review_note)` → `resume(sid, terms)`. 참조는 `source_id`, `unit=ATOM`, `atomization_reviewed=True`, `atoms`, `nonclaim_cues`를 갖는다. 모든 자막은 참조 원자 또는 비주장으로 분류한다. 원자 구조는 기존 `d4_quality.FIELDS` 및 id/cues/risk. 사전 고정 기록은 DB에 별도 저장; 초안 반환 API는 freeze 전 차단. 시간·실행 순서를 실제 작업 로그로 추가 기록한다.
5. 최종 패킷은 기존 Engine 형식을 유지하되 `atomization_reviewed=True`와 각 claim에 `source_atom`을 추가한다. `source_atom`은 `subject`, `speaker_stance`(speaker와 kind 명시), `polarity`, `conditions`, `exceptions`, `numbers_units`, `risk`를 갖는다. 원문 주장인 `statement`, `time_scope`, `cues`, `id`는 실제 claim에서 직접 파생한다. `knowledge` 및 기존 conditions/exceptions/numbers는 금융 검증 결과로 유지할 수 있다. 한 claim에 하나의 원자 명제. 참조 및 출력의 조건이 없으면 NONE, 불명확하면 UNKNOWN으로 구분하며 수동 평가한다. 모든 claim(보류·문맥 포함)이 출력 분모에 들어가며 비주장 자막은 별도로 확인한다.
6. 리뷰 행에는 `output`, `reference`(추가 명제는 null), `output_sha`, `reference_sha`(null 가능), 8개 `fields`의 bool, `reason`을 기록한다. `output_from(packet)`으로 실제 최종 패킷에서 평가 원자를 얻고 각 행의 canonical digest를 연결한다. 원자별 수동 대조를 수행하고 정밀도95%/재현율98%/고위험 누락0을 적용한다. 승인·교정·동치 항목은 모두 정확 매칭되어야 하고 `financial` 사전에 claim id별 `claim_sha`, `reason`, `checks`(evidence/scope/date/conditions/exceptions/numbers/dependencies 각 True)를 기록한다. 이는 ChatGPT의 사실·근거 판정 기록이지 공식 자료 원본의 자동 인증이 아니다.
7. 질문은 freeze 시 `id`, `terms`, `required_refs`, `required_prior`, `forbidden_refs`, `forbidden_prior`, `no_match`로 사전 등록한다. 적어도 한 긍정/부정 질의 필요. 필수 신규 지식 포함 및 명시된 금지 지식 제외/빈 결과를 시험한다. 신규 활성 지식이 있으면 적어도 하나의 신규 지식 긍정 질의를 요구한다. 모든 관련성 낮은 후보의 자동 판별이나 자연어 전체 답변 평가를 수행하지 않으므로 그 한계는 기록한다.
8. `registry_plan`은 `prior_sha`, `review_note`, `reviewed_ids`(갱신 후 활성 qualified_id 전체), `add`, `remove`를 갖는다. 기존 edge는 보존하며 삭제하려면 from/to 및 이유가 필요하다. 양단이 비활성화된 edge를 조용히 제거하지 않고 명시적 재검토/대체 또는 삭제를 요구한다. 새 edge의 실제 양단 digest는 저장 후 엔진이 산출한다. 매 연구 후 registry head 갱신; 구 버전 registry 주입은 차단한다. 전체 활성 목록의 확인 비용 및 관계 완전성은 신규 영상 및 규모 확대에서 평가한다.
9. `finalize(packet, reviews, financial, registry_plan)` 실행. 동일 SQLite 트랜잭션에서 원자 평가 및 금융 검토 → 기존 Engine.finalize → registry 갱신 → 사전 확정 query 시험 → 감사기록 삽입을 수행한다. 실패 시 영상 final/items/head/registry/audit 모두 롤백한다(초안과 사전 고정 자료는 보존). 동일 입력 재시도는 동일 영수증, 변경 요청은 차단한다. `query(terms)`는 저장된 registry만 이용하고 `audit(sid)`로 승인 감사 기록 조회. 실제 운영 승격 전 별도 복제 DB에서 재현 및 기존 운영 보존 확인. 2턴 실패 후 같은 영상의 소급 PASS 금지.

## 실측 및 제한
- `python -m unittest -v test_d4_gate test_d4_quality`: 29/29 (신규 18, 기존 11). 합성 시험이며 실제 금융 의미를 인증하지 않음.
- `python replay_gate.py <diagnostic_root>`: 원본 운영 DB 4편/37활성/61판정 사본 이관 시 rows 및 head 보존, baseline review 전 조회 차단, 불완전 등록 차단. #263 기존 시험 DB 두 개의 임시 진단 사본에서 기존 수동 12개 질의 12/12 재현. I21→I20 수동 관계를 포함한 기지 사례이며 baseline semantic review나 신규 금융 승인으로 해석 금지. 이관 사본은 임시 디렉터리에서 폐기. 원본 DB 세 개 SHA-256 불변.
- 실제 운영 DB의 37개 지식에 대한 baseline 관계 검토 미완료; 새 게이트 운영 원장 미승격. 기존 Engine CLI를 사용하는 기존 DB 자체는 유지되므로 그것을 신규 승인 경로로 사용하면 안 된다. 새 DB 모드 표식은 정상 API의 우회를 차단하지만 임의 Python/SQL은 신뢰 경계 바깥이다.
- 단일 스레드 직접 호출용; 동일 객체의 다중 스레드 호출은 미지원. 실제 2턴 성공 여부, 참조의 완전성, 자동 관계 발견, 자연어 답변, 전체 연구시간 미입증. 외부 파일/채팅 노출은 독립 블라인드가 아니다.

## 다음 과제
1. 운영 37개 활성 지식 및 필수 문맥 관계의 실제 전수 baseline review, 승인 가능한 이관 사본 생성 및 해시 보존.
2. P0-6 신규 장편 영상 미사용 원본 선정 및 참조 원자/사전 확정 질의 기반 2턴 end-to-end 실증. 기존 HOLD 자료는 신규 운영 입력으로 사용하지 않는다.
3. 신규 게이트로 합격 영상 3편 추가 필요. D4-2~4 TODO, 17/32, 운영 4편/37활성/61판정 유지.


## Baseline 이관 결과 (2026-11-27)
활성37개 수동 문맥 전수 검토 및 39개 관계 등록 완료. D4_GATE_BASELINE_RESULT.json 및 Library 보존본 참조. 두 후보 DB 해시 및 기존 rows/head 일치. 신규 후보 DB SHA 7ad9091c27b6b909cbec451e7241b7824e4e47aa25b1f1068c85cd67e7ca7a34. 기존 원장은 그대로 유지. 신규 P0-6 연구는 후보 DB 복제본에서만 진행. 원본을 처음부터 연구하고 2턴 freeze/원자 평가/금융 리뷰/registry/질의/감사 기록을 GateEngine으로 완결한다. 기존 HOLD 소급 합격 금지. 후보 baseline PASS는 신규 원본 운영 합격이 아니다.


## #270 실패 후 작성 절차 변경
[D4_AUTHORING_PROTOCOL.md](D4_AUTHORING_PROTOCOL.md)를 신규 원본 1턴 연구에 적용한다. 이 변경은 ChatGPT 작성 절차이며 GateEngine 코드/승인 관문은 변경하지 않는다. #270 사후 진단을 운영 합격으로 사용하지 않는다. 신규 #292 준비 완료, 연구 미착수.
