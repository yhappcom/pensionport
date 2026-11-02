# IRE V3 — 원본 금융 의미분석·누적 지식·자문 연구 엔진

**현재 사용 모드:** ChatGPT 현재 대화에서 금융 의미를 분석한다.
별도 모델 API 호출이나 API 키를 요구하지 않는다.

**목적:** 영상 5편 분석이 끝이 아니다. 새 원본 영상이 추가될 때마다
기존에 독립적으로 생성한 IRE 지식과 비교하여 새 근거·조건·예외·
시점 변경을 반영하고, 자문 질문에 사용 가능한 근거 체계를 구축한다.

## 한 턴 자동 이어달리기: 검증된 답변 묶음의 단일 명령 처리

사용자에게 반복 진행 지시를 요구하지 않도록 현재 ChatGPT가 같은 대화 내에서
원문 전용 패킷을 해석·작성하고, 소스/패킷에 연결된 답변들을 비공개로 묶는다.
`v3_one_turn.py`는 **그 준비된 답변 묶음 전체**를 원본 SHA·인용·
의미 검사 후 최대 12개 패킷씩 연속 접수하고, 완주된 경우에 한해
잠정 연구 지식을 통합한다. 남은 데이터가 있으면 다음 창을 반환하며
미제출 답변을 임의 추론하거나 빈 비주장으로 채우지 않는다.

```bash
python -m ire.v3_one_turn execute \
  --private-manifest /private/batch.json \
  --private-answers /private/cited_answers.json \
  --private-knowledge-dir /private/kb \
  --private-audit-dir /private/audit \
  --max-packets 12 --max-chars 60000
```

사용자 요청에 1~N편 전체 분석이 포함되면 ChatGPT가 원문 문맥을
가능한 한 같은 턴에서 순차 처리해야 한다. **단일 명령 실행이 곧
모델이 분석하지 않은 338개 문맥의 자동 추출을 뜻하지는 않는다.**
별도 LLM API 없이 Python이 모델을 무인 반복 호출하거나 한 턴 완주를
무조건 보장하는 기능은 없다. 모든 단계의 실패/보류가 보고서에 표시된다.

완전한 실행 규격·종료코드·잔여 P0~P2 검증 단계는
[V3_ONE_TURN_EXECUTION.md](V3_ONE_TURN_EXECUTION.md),
`contracts/research_one_turn_v3.json`을 참조한다.

## V3 P0~P2 통합 경로 (현재 개발 기준)

전체 기능 설계 및 엄격한 완료/미완료 판정: [V3_P0_P2_COMPLETION.md](V3_P0_P2_COMPLETION.md).
기계 계약: `contracts/research_system_v3_completion.json`. V2는 기존 원본·원장·
API 없는 ChatGPT 실행 호환 계층으로 보존한다.

- **P0:** `v3_orchestrator.py` (`status,next,accept,correct,audit,gate,finalize`),
  `v3_adaptive.py`, `v3_semantic_audit.py`, `v3_corrections.py`,
  `v3_evidence.py`, `v3_numeric.py`.
- **P0-D:** `v3_relation_eval.py`: 외부 신규 독립 정답이 준비될 경우
  어휘 기준선과 금융 의미 검색의 Recall@K·Precision@K 측정.
- **P1:** `v3_relation_review.py`: 새 영상 원자 주장과 기존 지식의
  관계 검토, 원본 인용, 새 후보 추가, 누적 관계 원장 rebase.
- **P2:** `v3_advisory.py`, `v3_advisory_eval.py`: 근거 시점·
  조건/예외·상충·위험·개인 적합성 평가 및 블라인드 시나리오 시험.
- **출시 판정:** `v3_release.py` 또는 `v3_orchestrator gate`는
  증거 누락과 독립 평가 미완료를 차단한다.

공식 HTML/텍스트형 PDF 지원은 데이터 추출·출처 대조에 관한
소프트웨어 기능이다. 스캔본 OCR, 현재 법적 효력,
실제 금융 사실·자문 적합성의 독립 승인까지 자동화한 것은 아니다.
2026-11-02 실전 #1~#5 입력은 346문맥 중 8개가 제출됐고 338개가
남아 있다. 실제 전체 자막 분석이 완료됐다고 표시하지 않는다.

## V2 우선 문서와 개발 계약

- ARCHITECTURE_V2.md: 최종 사용자 경험, 전체 단계, 데이터 모델, 검증·마이그레이션 정책
- contracts/research_system_v2.json: 현재 활성화된 기계 판독 가능 설계 계약
- v2_run.py: 1~30편 원본과 ChatGPT 문맥 응답을 일괄 감사하고 누적 지식에 통합
- chat_bridge.py: 채팅의 원본 문맥·원자 주장 추출·인용 검증·비공개 체크포인트
- knowledge.py: 이전 신규 IRE 결과와 추가 영상 간 관계 후보, 통합 주제, 불변 지식 스냅샷
- v2_evidence.py: 새 공식 원문에 대한 ChatGPT 평가, 기관·원문 해시·인용·기간 확인
- research.py: Decimal 수치 검산과 근거 조사 의무
- blind_eval.py: 독립 검토자 원본 우선 평가가 확보된 경우에만 품질 지표 계산

기존 API 중심 one_shot.py/semantics.py/primary.py/evidence_audit.py의
인터페이스는 과거 실험·회귀시험을 위한 레거시 호환 코드다.
현재 실행 플로는 외부 모델 API를 호출하지 않는다.
기존 모듈을 수정할 때는 출처 검증 기능을 훼손하지 않아야 한다.

## 사용자 작업 흐름: 한 번의 ChatGPT 메시지

1. 사용자가 “영상 1~5편 전체 분석하고 기존 지식에 통합”이라고 지시한다.
2. ChatGPT가 원본을 확보해 채팅 내부에서 모든 문맥을 분석하고
   서술된 주장·조건·수치·예외·적용 시점을 추출한다.
3. 필요한 공식 기관 원본을 현재 채팅 웹 도구와 IRE 문서 검증기로 확인한다.
4. 새 연구를 이전 신규-IRE 지식과 비교해 중복·보완·시간 변경·
   잠재적 충돌 및 새로운 근거를 표시한다.
5. V2 일괄 감사 완료 시 한 버전의 지식 원장으로 갱신하고
   연구 결과와 변경 이력, 미완료 항목을 함께 보고한다.
6. 자문 질문은 관련 통합 주제와 현재 법령 근거, 위험·비용,
   이용자 적합성을 재확인한 후 필요한 범위에서 답한다.

사용자가 내부 문맥 패킷이나 JSON을 일일이 제출할 필요는 없다.
ChatGPT가 관련 도구 호출을 조정한다. 다만 채팅 도구/시간/문맥
제한을 초과한 상황에는 부분적인 완료 상태만 보고하고
새 지식을 승인하지 않는다. 무인 백그라운드 완료를 약속하지 않는다.

## 비공개 입력 매니페스트

원본 영상 1~30편을 하나의 실행 입력으로 지정한다.
다음 JSON은 형식 예시이며 실제 SHA와 경로는 내부 도구가 확인한다.

    {
      "schema":"IRE_V2_CHAT_BATCH_V1",
      "research_as_of":"2026-11-01",
      "videos":[
        {
          "video_id":"ABCDEFGHIJK",
          "original_srt_path":"/private/001.srt",
          "source_sha256":"ACTUAL_64_CHAR_SHA256",
          "private_chat_sessions_path":"/private/ire_sessions"
        }
      ]
    }

원본 입력·연구 전문·개인 자문 자료는 GitHub에 업로드하지 않는다.

## 배치 원문 검사 및 지식 통합

현재 채팅에서는 assistant가 내부적으로 다음 실행을 담당한다.
원문 분석 내용은 ire.chat_bridge 검증된 세션으로 보존한다.

    python -m ire.v2_run plan \
      --private-manifest /private/current_batch.json

    python -m ire.v2_run finalize \
      --private-manifest /private/current_batch.json \
      --private-knowledge-dir /private/new_ire_kb \
      --private-audit-dir /private/ire_batch_audits

누적 지식 원장이 이미 있는 경우 반드시 다음 인수를 추가한다.

    --prior-knowledge-snapshot /private/new_ire_kb/LATEST.json

근거 평가가 이미 있는 경우 추가한다.

    --prior-evidence-snapshot /private/ire_evidence/LATEST.json \
    --private-evidence-dir /private/ire_evidence

**모든 분석 문맥이 제출되고 unresolved cue가 0일 때만**
새 버전 지식을 반영한다. 중단되면 비공개 감사 보고서를
생성하고 기존 지식 원장은 그대로 유지한다.

지식 원장은 영상 ID·원본 해시·claim ID를 지닌 모든 주장을
보존한다. 신규 주장이 기존 주장과 달라도 오래된 주장을
삭제하거나 검색 유사도만으로 참·거짓을 승인하지 않는다.

## 공식자료 실원문 검사 및 자문 맥락

새 공식 원문이 확보되고 채팅에서 claim별 JSON 판정이
생성된 경우 다음 명령으로 문서를 **독립적으로 다시 다운로드**
하여 정확 인용문, URL, 원문 해시, 날짜·조건 등을 대조한다.

    python -m ire.v2_evidence init \
      --private-knowledge-snapshot /private/new_ire_kb/LATEST.json \
      --private-evidence-dir /private/ire_evidence

    python -m ire.v2_evidence review \
      --private-knowledge-snapshot /private/new_ire_kb/LATEST.json \
      --private-ledger /private/ire_evidence/LATEST.json \
      --private-chat-review /private/official_claim_review.json \
      --private-evidence-dir /private/ire_evidence \
      --private-original-document-dir /private/official_bytes

새 지식 버전으로 넘어갈 때는 v2_evidence rebase를 사용해
기존 근거 사건을 원자 주장 ID에 연결한 채 이관한다.

자문 근거 질의:

    python -m ire.v2_evidence advisory \
      --private-knowledge-snapshot /private/new_ire_kb/LATEST.json \
      --private-ledger /private/ire_evidence/LATEST.json \
      --question "ISA 만기 시 세금 및 연금계좌 이전은?" \
      --as-of 2026-11-01 \
      --jurisdiction KR

출력은 검증 대기와 가능한 모순·만료 자료를 구분한 연구 맥락이다.
사용자별 자동 매매 지시나 독립적 금융 사실 승인 기능이 아니다.
ChatGPT는 최신 공식 원문과 사용자 조건을 확인하여 설명해야 한다.

## 실행 및 연구 검증 수준

- 원본 cue·문맥·인용·수치·패킷 해시 검사: 구조적으로 시험 가능.
- 금융 주장 추출의 완전성·정확성: 독립 신규 정답 없이는 인증 불가.
- URL만 검색한 공식자료: 아직 사실 검증이 아니다.
- 공식 원문 인용 일치: 직접 확인된 텍스트, 법적 효력·범위는 별도.
- ChatGPT 스스로 한 주장의 지지를 판단: 독립 인간 심사 아님.
- 신규 주장과 기존 주장 간 자동 관계: PENDING, 정답 아님.
- 자문용 자료: 기준일·관할·비용·위험·상품 적합성을 다시 확인.
- 금지 상태: 미검증 주장을 확정적 투자 권고나 자동 지식 승인으로 변경.

엔진의 CI 유닛 PASS는 실제 금융 연구·자문 품질 PASS를 뜻하지 않는다.
과거 260편의 연구 결론은 새 엔진의 독립 정답으로 사용하지 않는다.
main·기존 원본 파일은 보존한다.
