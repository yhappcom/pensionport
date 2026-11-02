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

## 2026-11-02 오후 복구 · 원본 기반 의미/수치/증거 보호 보완

- 기존 GitHub Actions에서 통과한 V3 코드를 재확보하고 별도 환경에서
  구문 검사와 전체 회귀시험을 다시 수행한다. 복구 이전의 임시 소스는
  기존 저장소에 부분 커밋하지 않는다.
- `v3_semantic_audit.py`는 주장 **자체 인용**에 없는 월 지급 주기,
  연 단위 수익률, 세제계좌 명칭 추론을 탐지한다. `개인연금`이라는
  일반 표현만으로 `연금저축`을 특정하면 중대한 출처 확대 오류로
  차단한다. 반면 앞뒤 발언의 문맥 대명사/생략, 자막 오탈자
  (`연금제축` 같은 자동 자막 표기)는 검토 경고로 남기며
  확정적 금융 사실이나 자동 승인은 하지 않는다.
- `v3_numeric.py`는 단순 부분 문자열 검사를 넘어서 전체 수치와
  인접 단위를 직접 묶어 대조한다. `1100만원`의 일부를 `100만원`으로
  인용하거나 `100만원`을 `100원`으로 해석하는 오류를 거부한다.
  회수기간 계산에서 월 지급 주기도 원문 인용에 있어야 한다.
- `v3_evidence.py`는 공식 근거 `0.3%`가 실제 `10.3%` 일부에서만
  나타나는 오인용을 거부한다. 공식 증거 원장과 V3 검토 영수증
  두 파일을 저장할 때 신규 영수증을 먼저 기록하고, 일반적인
  원장 파일 쓰기 실패 시 영수증을 되돌린다. **프로세스 전원 차단까지
  포함하는 진정한 2파일 원자 트랜잭션은 아니다.** 장기적으로는
  복구 저널/단일 커밋 마커가 필요하다.
- 실제 비공개 v002 원장을 새 코드에서 **수정 없이 다시 읽는 실험**:
  #1~#5 원본 5,129 cue, 346문맥, 제출 8, 미제출 338 확인.
  W00003 정정 전 위험 2건은 탐지되지만, 정정 후 8개 문맥의
  새 중대 오류는 0건이다. 문맥 재검토 경고 16건은 아직 열려 있으며,
  독립적 인적 블라인드 검증과 실전 금융 사실 승인은 여전히 0이다.

## 2026-11-02 복구 저널·경고 트리아지·블라인드 평가용 소스 패킷 추가

**1. V3 공식 근거 저장 WAL.** `v3_evidence_txn.py`는 두 파일 저장 전에
SHA-256 봉인된 `.pending` 사전 기록을 0600 모드로 남긴다. 전체 파일과
부모 디렉터리를 `fsync`하고 `fcntl.flock`으로 같은 폴더의 동시 쓰기를
직렬화한다. (a) 영수증만 쓰고 프로세스가 종료되면 다음 실행에서 이를
되돌리고, (b) 원장과 영수증을 모두 쓴 후 종료되면 두 SHA를 검사하고
`.done` 커밋 기록으로 이행한다. (c) 기록이 변조되거나 승인된 후 일부
파일이 사라지면 **자동 복구하지 않고 실패**한다. 기존 원장 파일 자체는
임의 변경하지 않으며, 모든 검토가 금융 사실 승인을 뜻하지 않는다.

```bash
# 크래시 이후 먼저 실행: 출력은 보안상 해시/개수 중심
python -m ire.v3_evidence recover \
  --private-evidence-dir /private/ire_evidence
```

이 방식은 로컬 POSIX 파일시스템·`fsync`의 내구성을 전제로 한
**크래시 일관성 복구 프로토콜**이다. 공유 스토리지 전원 차단,
파일시스템 구현 결함, 전체 데이터와 지문의 동시 악의적 변조를 방어하는
암호학적 서명이나 DB의 진정한 단일 원자 트랜잭션은 아니다.
V2 단독 소비자에게 파일 두 개의 동시 출현을 원자적으로 보장하지는 않는다.
V3 공식 근거 재개 시 반드시 WAL 복구를 선행해야 한다.

**2. 경고 16건을 원문 위치에 연결한 보강 대기열.**
`v3_warning_triage.py`는 유효한 체크포인트를 다시 읽어, 재검토 경고의
claim ordinal/문맥 ID/원본 cue 번호/인용 SHA를 비공개 JSON에 저장한다.
실제 #1~#5 v002에서는 경고 16건 중 7건의 원문 보강 후보가 **동일한
primary window**에 존재했고, 9건은 **앞 문맥의 별도 source**에 있었다.
두 부류는 자동으로 해결되거나 해당 주장의 citation 범위를 확장하지 않는다.
원본을 검토하는 사람이 인용의 연결 타당성을 확인하고 필요한 경우
기존 캐시를 수정하지 않는 `correct` 이력을 별도로 작성해야 한다.

```bash
python -m ire.v3_warning_triage inspect \
 --private-manifest /private/batch.json \
 --private-report-dir /private/ire_warning_triage
```

**3. 실제 독립 평가자를 위한 소스 전용 홀드아웃.**
`v3_blind_protocol.py`는 저장된 잠정 모델 답변이 **없는** 원본 창만
선택하고, 실제 SRT primary cue와 참고용 주변 cue만 포함한다.
영상별 3개씩 **총 15개 원본 홀드아웃 패킷**을 비공개로 생성했다.
모델 주장·기존 연구 지식·관계 검색 순위는 패킷에 넣지 않는다.
두 명의 실제 독립 검토자는 모델 예측을 보지 않고 별도로 답해야 하며
제3 조정자의 독립 결과가 확보돼야 골드 품질을 평가할 수 있다.
패킷 생성 자체가 독립 사람의 검토·골드·Recall/Precision을 인증하지 않는다.

```bash
python -m ire.v3_blind_protocol prepare \
 --private-manifest /private/batch.json \
 --sample-per-video 3 \
 --private-dir /private/ire_blind_source_only
```

코드·합성/적대적 테스트만 GitHub에 반영한다. 실제 SRT와 블라인드
패킷·원자 주장 텍스트는 비공개 보관한다. `main`은 수정하지 않는다.

## 2026-11-02 금융 의미의 인과관계·단위 정확도 재판정

- **구조 PASS와 의미/금융진위 PASS는 서로 다르다.** 영상 #1의 비공개
  유효 체크포인트 8개 창/31개 잠정 주장은 원문 인용/저장 검사에 통과했지만
  8개 종전 문맥 경고와 3개 신규 중대한 검토 위험은 미해결이다.
- 신규 원자 주장 사이 교차 문맥 감사를 `v3_claim_quality.py`에 추가한다.
  W00005 주장 3, W00008 주장 4는 앞 W00003의 7년 추가 납부 가정에서
  나온 증가액을 추납만의 효과와 동일시할 가능성이 있어
  `PENSION_INCREMENT_CAUSAL_BASIS_UNSEPARATED`로 검토 대기시킨다.
  이것은 원본 경제적 원인 관계에 대한 **미검증 경고**이지
  모델이 금융 진위를 판정한 결과가 아니다.
- W00007 주장 2의 5.5/4.4는 원본 단위 명시가 없어
  `REGULATORY_NUMERIC_UNIT_UNESTABLISHED`로 검토 대기시킨다.
  소득세·지방소득세 포함 여부/효력 날짜/개인 조건 등 별도 공식 대조가 필요하다.
- 세 위험과 종전 8개 문맥 경고를 주장 ID 기준으로 중복 제거하면
  **31건 중 9개 고유 주장**이 우선 검토 대상이다. 나머지 22건 역시
  독립 골드나 금융 사실로 인증된 것이 아니다.
- `v3_orchestrator audit/gate/finalize` 및 `v3_release.py`에 교차 문맥
  검증을 연결했다. 중요한 위험이 남아 있으면 `finalize`는 새
  지식 스냅샷을 만들지 않고 막는다. 원본 또는 v003 원장은 변경하지 않았다.
- 공식세법 확인·보험료 및 수급액 원인 분리·독립 전문가 판정이
  끝나기 전에는 실제 자문 승인 금지. 외부 LLM API 0회.
- **255개 합성/적대적 GitHub CI 테스트 PASS.**
  상세 규칙: `V3_CLAIM_QUALITY_POLICY.md`.
  비공개 31건 판정·인용: 개인 Google Drive에 저장.
