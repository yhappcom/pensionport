# IRE V3 P0–P2 연구·통합·자문 엔진 — 구현 완료 조건 및 실행 절차

기준: 2026-11-02. 이 문서는 **구현된 소프트웨어 기능**과 **실제 금융 연구·자문 검증 상태**를 엄격하게 구분한다. 엔진은 공개 GitHub의 원본 SRT/개인재무자료를 읽지 않는다. 원본과 산출물은 사용자 비공개 공간에서만 처리한다.

## 1. 원래 목표 및 구현 결함 보완

사용자는 "#1~#5 영상 분석", "다음 영상 추가 및 누적 통합", "개인 금융 질문"과 같은 **하나의 자연어 요청**을 입력한다. 현재 ChatGPT가 실제 금융 발언을 해석하며, Python은 인증·근거·문맥·관계·계산·누적 원장·검증의 결정적 처리를 담당한다. **별도 LLM API 없음**. 이 구조는 ChatGPT의 무제한 호출, 사용자 응답 뒤 자동 백그라운드 완료, 346개 문맥의 한 턴 무조건 완주를 지원하지 않는다. 완료되지 않은 연구를 자동 승인하지 않는다.

| 작업 | 구현 모듈 | 자동화 가능한 부분 | 실제 증명이 필요한 부분 |
|---|---|---|---|
| P0-A 원본→채팅 문맥→체크포인트 | `v3_orchestrator.py`, `chat_bridge.py` | 원본 SHA, 윈도 전수 추적, 응답 스키마/인용, 중단 재개 | 대화모델이 실제로 모든 문맥의 금융 의미를 완전히 해석했는지 |
| P0-B 적응형 금융 의미 | `v3_adaptive.py`, `v3_semantic_audit.py`, `v3_corrections.py` | cue 유일 배정, 문맥 경계 경고, 비주장 오분류 일부 탐지, 불변 정정 | 실제 주장 단위 재현율·다의성·문맥 누락 |
| P0-C 공식자료·수치 | `evidence.py`, `v3_evidence.py`, `v3_numeric.py`, `v2_evidence.py` | 허용 후보 도메인 실원문 재취득, 텍스트형 PDF 추출, 인용·숫자·날짜 링크, Decimal 검산 | 법령 효력·스캔형 PDF·현재 유효성·금융 사실 독립 판정 |
| P0-D 관계 검색 | `v3_semantic_candidates.py`, `v3_relation_eval.py` | 한국어 금융 용어 확장, 소스 우선 골드 형식, 실제 랭킹 Recall@K·Precision@K | 실제 외부 평가자 2인 + 독립 조정자 정답 및 검증된 판정 절차 |
| P1 누적 지식 | `knowledge.py`, `v3_relation_review.py` | 새 IRE 주장 원본별 불변 보존, 관계 판정 이력, 누락 후보의 근거 있는 추가, 새 영상 추가 시 rebase | 관계의 의미적 참·거짓 및 조건·시점 충돌 독립 확정 |
| P2 자문 근거 | `v3_advisory.py`, `v3_advisory_eval.py` | 질문별 실제 캡처일·효력기간·범위·상충·계좌/기간/위험 확인, 안전성 시나리오 계산 | 개인 적합성 전문 검토·현행 규정·거래 판단 독립 승인 |
| 최종 게이트 | `v3_release.py`, `v3_orchestrator.py gate` | 누락 창·미해결 cue·사실 미승인·증거 부재·개인자문 승인 미충족 보고 | 외부 사람이 실험적 금융 진위/자문 성능을 실제 검증했는지 |

## 2. 실제 수행 명령 — 사용자에게 내부 JSON 반복 요구 금지

원본 ZIP은 사용자 비공개 공간에 두고 연구 요청이 들어오면 ChatGPT가 필요한 연결 도구를 사용해 원본 해시 및 대기 문맥을 가져온다. 아래 명령은 **채팅이 내부적으로 오케스트레이션할 때의 실행 절차**다.

```bash
# 원본 cue·지문·완료 수 / 다음 문맥 표시
python -m ire.v3_orchestrator status --private-manifest /private/batch.json

# 실제 현재 채팅이 해석할 원본 전용 문맥 가져오기
python -m ire.v3_orchestrator next --private-manifest /private/batch.json \
  --max-packets 4 --max-chars 18000

# 채팅이 작성하고 인용 검증한 원자 주장 일괄 접수
python -m ire.v3_orchestrator accept --private-manifest /private/batch.json \
  --private-submission /private/next_answers.json

# 기존 명제의 의미적 오류 수정: 원래 답변 파일 불변
python -m ire.v3_orchestrator correct --private-manifest /private/batch.json \
  --private-correction /private/window_correction.json

# 공통 연구 전 단계 안전 확인
python -m ire.v3_orchestrator gate --private-manifest /private/batch.json

# 전체 영상의 실제 금융 의미 검토가 끝났을 때만 통합 (V2 불변 원장)
python -m ire.v3_orchestrator finalize --private-manifest /private/batch.json \
  --private-knowledge-dir /private/ire_kb --private-audit-dir /private/audits
```

새 영상이 추가되고 기존 지식이 존재하면 `finalize`에 `--prior-knowledge-snapshot` 및 해당 증거 원장 인자를 넣어야 한다. 원본이 하나라도 미해석이거나 잘못되면 누적 지식은 쓰지 않는다. 연구 대상이 30편을 넘으면 원본을 1~30편 배치로 나누고 모든 배치를 검증한 뒤 누적 저장한다.

```bash
# 누적 지식 관계 후보에 대한 원문 연결 판정 (소스 우선, 사실 인증 아님)
python -m ire.v3_relation_review init \
 --private-knowledge-snapshot /private/ire_kb/snapshot.json \
 --private-dir /private/ire_relation
python -m ire.v3_relation_review assess \
 --private-knowledge-snapshot /private/ire_kb/snapshot.json \
 --private-ledger /private/ire_relation/current.json \
 --private-review /private/claim_pair_review.json \
 --private-dir /private/ire_relation

# 후보 순위 밖에 있는 관계를 원문 인용으로 추가. 기존 지식 덮어쓰기 금지.
python -m ire.v3_relation_review discover \
 --private-knowledge-snapshot /private/ire_kb/snapshot.json \
 --private-ledger /private/ire_relation/current.json \
 --private-review /private/missed_pair.json \
 --private-dir /private/ire_relation

# 독립적으로 작성·봉인한 관계 골드가 있을 때만 통계 측정
python -m ire.v3_relation_eval evaluate \
 --private-knowledge-snapshot /private/ire_kb/snapshot.json \
 --private-gold /private/relation_blind_gold.json \
 --private-report-dir /private/ire_relation_eval

# 최신 공식 원문과 투자자 조건을 확인한 자문 연구 맥락 (거래 지시 아님)
python -m ire.v3_advisory dossier \
 --private-knowledge-snapshot /private/ire_kb/snapshot.json \
 --private-evidence-ledger /private/ire_evidence/current.json \
 --question "연금 인출 시 위험과 세금을 확인해 주세요" \
 --as-of 2026-11-02 --jurisdiction KR \
 --private-report-dir /private/ire_advisory

# 독립적으로 제시된 자문 시나리오와 실제 품질/누락 통계 계산
python -m ire.v3_advisory_eval evaluate \
 --private-knowledge-snapshot /private/ire_kb/snapshot.json \
 --private-evidence-ledger /private/ire_evidence/current.json \
 --private-gold-cases /private/advisory_blind_scenarios.json \
 --private-report-dir /private/ire_advisory_eval

# 최종 단계 종합 판정 (자문 자동승인 금지)
python -m ire.v3_release audit \
 --private-manifest /private/batch.json \
 --private-report-dir /private/ire_release_audit
```

## 3. 평가 및 승인 조건

**연구 출처 관리·시스템 기능**과 **금융 사실/개인 자문 품질 인증**은 별개다. 모델이 스스로 작성한 가상 리뷰어 ID나 합성 테스트는 독립 인간 검증을 증명하지 않는다.

- 전체 원본 SRT 해시가 일치하고 모든 primary cue가 정확히 한 창에 소속돼야 한다.
- 원본 창별 인용·측정값·부정/조건/시점/수치 구조가 대조되고 모든 창이 완료돼야 한다. `UNRESOLVED` cue 또는 핵심 누락 경고가 있으면 연구 출시 차단.
- 새 지식 스냅샷에 해당 배치의 실제 영상 ID·SHA가 모두 포함돼야 하며, 기존 스냅샷/관계/증거를 삭제하거나 재활용할 수 없다.
- 금융 사실은 별도의 공식기관 문서 실원문(문서 바이트 SHA 포함), 적용기간·관할·세제·예외에 대한 독립 검토가 필요하다. 도메인 화이트리스트는 발행자·법령 효력 인증이 아니다.
- 원자 주장/관계 골드에는 원본 우선 2인 독립 평가와 별도 조정자 판정이 실제로 존재해야 한다. 코드의 역할·해시 필드 검사는 이 조건을 자동 인증하지 못한다.
- 질문별 최신 법규·비용·위험·유동성·계좌·개인 적합성 검토 및 독립 자문 시나리오 검사를 통과해야 한다. 현재 코드는 개인 매매 지시·자동 자문 승인을 허용하지 않는다.
- 출처·체크포인트 무결성에 쓰는 SHA-256은 인증된 외부 저장값과 함께 사용해야 변조 탐지 근거가 된다. 악의적인 주체가 원본과 모든 해시를 함께 다시 쓴 경우 단독 서명이 아니다.

## 4. 실제 #1~#5 실증 상태 (2026-11-02)

개인 Drive의 `1-100.zip` 원본에서 #1~#5 5,129개 cue·원본 SHA를 재확인했고 V3 planner B로 346문맥으로 분할했다. 기존 V2 기준은 517문맥이다. #1 W00001~W00008의 **8개 문맥/31개 잠정 주장**만 비공개 v002 원장에 저장됐다. W00003의 원본 미지지 월 단위 및 특정 상품명 확대 2건은 불변 정정 기록으로 보존됐다. **나머지 338문맥은 아직 실제 해석되지 않았다.** 그 상태에서 실전 누적 지식, 실제 골드, 금융 사실/개인 자문 출시를 주장할 수 없다.

새 V3 P0-D/P1/P2 모듈은 원본·지식·증거가 생겼을 때 자동 검증을 수행하는 **구현된 도구**다. 실전 정확도 인증은 별도로 남아 있다. GitHub `main`, 기존 V2, 과거 260편 연구·원본은 보존한다.