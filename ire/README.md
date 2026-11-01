# IRE: 독립 금융 지식 연구 엔진

**2026-11-01 착수 · 신규 설계 및 실행 가능한 기반 · 운영 BLOCKED**

과거 연구는 실패 유형을 파악하는 설계 참고사항으로만 사용한다. 과거의 분석 주장, 결론,
평가 정답, 통계, 코드, 기존 검색 코퍼스를 새 엔진의 사실 입력으로 사용하거나 인용하지 않는다.
새 엔진의 연구 결론은 반드시 원본과 독립 근거에서만 생성하도록 설계한다.

## 첫 구현 아키텍처

| 신규 모듈 | 구현 내용 | 검증 경계 |
|---|---|---|
| ire/source.py | 원본 SHA-256 검증, 전 자막 cue 검사, 문맥 단위 복원 및 좌우 문맥 | 문맥 묶음은 원자 주장 아님 |
| ire/claims.py | 완결된 의미 주장 제안 및 금융 프레임 형식/원문 인용 검증 | 주석은 외부 분석기/사람 입력. 독립 금융 사실 승인 아님 |
| ire/retrieval.py | 이번 원본의 신규 명제만 어휘·문자 조각·명시 의미 필드로 후보 관계 검색 | 이전 연구 원장/정답 연결 없음 |
| ire/research.py | 주장별 공식/수치/실증 근거 의무, 문서 바이트 인용 및 정확한 산술 | 문구 존재는 발행기관/적용 범위/사실 인증 아님 |
| ire/semantics.py | 실제 OpenAI Responses API 금융 의미 해석 요청, 원본 10-cue 문맥/앞뒤 인용 문맥 전달, 원본 인용 검증 | 코드·합성 통합검사 완료. 실제 API 추론 미실행(인증 정보 없음) |
| ire/checkpoint.py | 모델·프롬프트·원본·문맥 SHA 결속, 실패 후 0600 비공개 재개 | 합성 단절·재시도 검증만 통과 |
| ire/cli.py | SRT부터 독립 의미 해석(설정 시)·관계 후보·차단 연구 작업표 연결 | 비공개 원본과 출력은 저장소 밖에만 보관 |
| ire/tests | 신규 합성 발언의 누락·변조·허위 승인·출처/보안 반례 시험 | 실제 금융/미노출 영상 성능 결과가 아님 |

## 근본적인 처리 변화

1. 원본 음성·영상/SRT의 출처를 확인한다. 첫 구현에서는 SRT 바이트만 검증하며 음성 대조는 미구현이다.
2. 자막의 단편을 직접 주장으로 간주하지 않고, 여러 cue의 연속 발언과 인접 문맥을 보존한다.
3. 별도 문맥 해석기가 완결된 금융 명제를 제안한다. 명제마다 원래 cue 인용, 주체·상품·금융 사건·행위·관할·유효일·조건·예외·수치·부정/가정 정보를 구성한다.
4. 구조 검증기가 모든 cue 분류 상태와 인용문의 원본 일치, 수치 출처를 검사한다. 검증 통과도 의미적 완전성/정확성을 보장하지 않는다.
5. 별도 공식 원문/정량/실증 조사 의무를 실행해 승인 대기열로 보낸다.
6. 관계 후보는 독립 생성된 주장끼리 검색하되 참/거짓 판정을 내리지 않는다.
7. 별도 인간 검토 및 미노출 정확도 입증 전까지 지식 승인 및 병합을 차단한다.

### 새 주장 형식

새로운 원본에만 묶인 주장에는 원본 SRT SHA, 단일 주장 ID, 정규화된 명제,
복수 cue 인용문, 주장 분류, 금융 의미 프레임(주체/상품/사건/행위/대상),
관할·발효일·조건·예외·측정값과 양태가 필요하다. 정보가 없으면 null로
남겨야 한다. 외부 모델/프롬프트 SHA는 입력 변경 추적용이며, 실제 모델 호출 여부는
해당 실행의 API 응답 및 권한 설정으로만 구별한다. 실행되더라도 자동 금융 사실
승인이나 사람의 독립 심사를 증명하지 못한다. 주장 승인은 절대 자동 부여하지 않는다.

전체 cue는 LINKED / NONCLAIM_CANDIDATE / UNRESOLVED 중 하나로 분류하고
역방향 claim ID를 확인한다. AI/분석기의 비금융 발언 제외는 독립 심사 없이는
최종 제외 승인으로 간주하지 않는다.

## 평가·격리 원칙

과거 연구는 별도 보관하며 새로운 연구를 작성하거나 새 엔진의 점수를 계산할
때 읽지 않는다. 신규 연구 결과가 봉인된 뒤에만 과거 연구와 차이를 비교할 수
있으며, 과거 연구는 골드라벨이 아니다. 새 평가 자료는 새 개발 자료와
중복되지 않는 원본만 사용하고, 별도 검토자 두 명의 독립 판정 후
주장/의미구조/관계 검색/출처 확인의 평가 항목을 분리한다.
실제 미노출 recall/precision과 신뢰구간은 아직 측정되지 않았다.

## 첫 실행

원본과 결과를 저장소 밖의 비공개 경로에 둔다. 원본 SHA를 사전 계산한다.

~~~bash
python -m ire.cli --original-srt /private/new_source.srt \
  --source-sha256 ACTUAL_64_HEX_DIGEST \
  --video-id ABCDEFGHIJK \
  --private-report /private/new_engine_report.json
python -m unittest discover -s ire/tests -v
~~~

외부 분석기가 **해당 신규 원본만을 해석해 만든** 주석 원장을 별도로 확보한
경우에만 다음 옵션을 추가한다.

~~~text
--private-annotations /private/new_source_proposals.json
~~~

주석이 없으면 문맥 윈도만 생성하며 원자 명제 자동 추출을 수행했다고
주장하지 않는다. 실제 모델 추론은 API 인증을 갖춘 개인 실행 환경에서만
아래 형태로 가능하다. 비공개 원본은 외부 모델 제공업체로 전송되므로 이용
권한·비용·개인정보 처리 정책을 확인한 뒤 실행한다.

~~~bash
export OPENAI_API_KEY="YOUR_PRIVATE_API_KEY"
python -m ire.cli --original-srt /private/new_source.srt   --source-sha256 ACTUAL_64_HEX_DIGEST   --video-id=ABCDEFGHIJK   --semantic-model YOUR_VERIFIED_MODEL_NAME   --private-semantic-checkpoints /private/ire_resume   --private-report /private/new_financial_claim_proposals.json
~~~

사용자 영상 ID가 하이픈으로 시작하면 --video-id=-lX...처럼 등호 방식으로
넣어야 한다. API 키는 명령 인수나 저장소/보고서에 기록하지 않는다.

**실제 모델 요청 코드와 재개 기능은 구현됐지만 현 실행 환경에 API 키가 없어
실제 금융 모델 호출을 한 번도 검증하지 못했다.** 음성 대조/공식자료 자동 취득/
인간 이중 심사/독립 미노출 평가/정식 지식 통합 승인 기능도 미구현이다.

현재 개발 산출물은 연구용 기반이며 투자 자동화 엔진이나 운영 가능
연구 인증 시스템이 아니다.

## 5단계 순차 연구 시험 현황

[원본 중복 검사 및 5단계 게이트 선언](validation/ire_5_stage_execution_20261101_v1.json)을
참조한다. **최종 개발용 원본 #266·267·269·270·271** 5편에서 3,600개
SRT cue → 364개 독립 문맥 윈도 생성과 출처 보존이 확인됐다. 원본
지문 중복을 발견해 초기 선정 #265·268은 신규 개발용 집합에서 제외했다.

별도 금융 사실 검증 10편은 원본 후보만 선정했으며 연구 결과를 작성하지
않았다. 비공개 원본의 재사용·중복과 노출 문제를 적용하면 블라인드 후보는
현재 잠정 6편만 남아 20~30편 목표를 충족하지 못한다. 독립 검토자의
블라인드 판정자료도 미확보다. 따라서 단계 3~5는 실행/승인하지 않는다.


## IRE 단일 실행 연구 오케스트레이터

새 진입점: python -m ire.one_shot. 사용자는 추가 진행 명령 없이 하나의
원본 또는 최대 30개 원본의 처리·검증·연구 차단 보고서를 받을 수 있다.

단일 명령은 원본 무결성 검사 → 발언 문맥 구성 → 모델 의미 해석 →
금융 원자주장 출처 검사 → 독립 공식 사이트 후보 검색 →
정량 검증 작업표 → 관계 후보 검색 → 독립 심사 게이트 →
비공개 최종 보고서 저장을 순차 실행한다. 완료되지 않은 단계는
결과 보고서에 SKIPPED_UPSTREAM_BLOCKED로 남긴다.

실제 모델 호출은 개인 OPENAI_API_KEY와 사용 가능한 모델 및 외부
API 전송 권한이 있는 환경에서만 이루어진다. 원본과 원자 주장은
외부 API 제공자에게 전송될 수 있으며 호출 및 검색 비용이 발생한다.

### 개별 원본 단일 실행

~~~bash
python -m ire.one_shot \
  --original-srt /private/new_original.srt \
  --video-id ABCDEFGHIJK \
  --source-sha256 ACTUAL_64_DIGIT_SHA256 \
  --semantic-model YOUR_MODEL \
  --research-model YOUR_WEB_SEARCH_MODEL \
  --private-semantic-checkpoints /private/ire_checkpoints \
  --private-output-dir /private/ire_reports
~~~

### 다섯 편 이상 일괄 실행

기존 연구 자료가 아니라 새 원본의 파일 경로, 영상 ID 및 실제 SRT
해시만을 포함한 비공개 JSON 매니페스트를 만든다.

~~~json
{
  "schema": "IRE_NEW_ORIGINAL_BATCH_V1",
  "videos": [
    {
      "video_id": "ABCDEFGHIJK",
      "original_srt_path": "/private/A.srt",
      "source_sha256": "ACTUAL_64_CHAR_SHA256_A"
    },
    {
      "video_id": "LMNOPQRSTUV",
      "original_srt_path": "/private/B.srt",
      "source_sha256": "ACTUAL_64_CHAR_SHA256_B"
    }
  ]
}
~~~

~~~bash
python -m ire.one_shot \
  --batch-manifest /private/new_sources.json \
  --semantic-model YOUR_MODEL \
  --private-semantic-checkpoints /private/ire_checkpoints \
  --private-output-dir /private/ire_reports
~~~

### 자동 실패 복구와 한계

- 모델 일시 장애는 제한 횟수만 재시도한다. 출처에 연결되어 검증된
  문맥 결과는 원본·모델·프롬프트 해시에 결속해 비공개로 재사용한다.
- 원본을 조작한 흔적이나 원문에 없는 인용은 중단 사유로 기록한다.
  모델 응답은 원문 검사를 통과해야 체크포인트에 기록된다.
- 원본 파일이 없거나 해시가 다르면 영상별 실패 보고서를 만들고
  나머지 영상은 계속 처리한다.
- 결과는 개인 디렉터리에 0600 권한으로 저장하고 기존 보고서를
  덮어쓰지 않는다. 외부 API는 원본 전송 동의를 전제로 한다.
- 실제 공식 기관 웹 검색으로 발견한 URL은 후보일 뿐이다.
  공식 자료의 진위, 적용 시점, 예외와 주장의 사실성을 자동 승인하지 않는다.
- 사람 2인의 독립 블라인드 판정이 확보되지 않은 현재, 전주제
  투자 사실 검증과 지식 통합 승인은 반드시 BLOCKED로 유지한다.

정상적으로 차단 보고서를 작성한 경우 종료 코드 2다. 파일 접근/
입력 스키마 등으로 실행 자체가 실패한 경우 종료 코드 3이다.
연구가 승인됐다는 성공 코드 0은 현재 제공하지 않는다.

### 재실행 검증

개발용 신규 원본 #266·267·269·270·271 총 3,600 SRT cue를 한
명령으로 다시 실행해 5개 원본 검증과 5개 비공개 실행 보고서 작성에
성공했다. 금융 모델 호출이 없는 환경에서는 5개 모두
SEMANTIC_MODEL_NOT_CONFIGURED로 명확하게 차단됐다.
모델 명칭만 부여하고 키가 없는 추가 시험도
SEMANTIC_API_KEY_UNAVAILABLE로 차단됐다.

CI 합성·적대적 시험 38건에 통과했으며, 이 결과는 실제 금융
의미추출 정밀도·재현율 또는 독립 금융 사실 검증 성능을 의미하지 않는다.


## 원본 의미 분석 → 실제 공식자료 원문 대조 통합 (IRE evidence v1)

실제 금융 주장을 얻는 단계와 독립 근거를 얻는 단계를 서로 다른 모델
요청으로 실행한다. 이 엔진에는 **기존 연구의 금융 주장·판정·정답
자료를 참조하는 코드가 없다.**

단일 명령의 연구 수행 상태는 다음 9단계로 기록한다.

1. 원본 SRT SHA-256 및 누락 구간 검사
2. 문맥별 실제 금융 의미 분석(Responses API, Structured Outputs strict)
3. 원자 주장 원문 인용·수치·조건·음성 미검증 상태 검사
4. 새 주장만 이용한 공식 자료 검색(web_search)
5. 공식 기관 도메인 제한 → 문서 HTTPS 직접 다운로드 →
   원본 응답 SHA → HTML/텍스트 추출 → 개별 금융 주장과 적용
   조건·시점·예외·단위를 별도 모델로 비교 → 정확한 인용문 역검증
6. 독립 수치 검산 의무와 누락 항목 기록
7. 이번 신규 원본 주장끼리만 관계 후보 검색
8. 독립 심사 차단(미검증 금융 사실 자동 승인 불가)
9. 변경 불가능한 비공개 실행 보고서 보존

### 새 실제 근거 검증 옵션

~~~bash
python -m ire.one_shot \
  --batch-manifest /private/ire_new_sources.json \
  --semantic-model YOUR_RESPONSES_MODEL \
  --research-model YOUR_SEPARATE_RESEARCH_MODEL \
  --private-semantic-checkpoints /private/ire_semantic_checkpoints \
  --private-evidence-dir /private/ire_original_official_bytes \
  --max-evidence-documents 8 \
  --private-output-dir /private/ire_reports
~~~

OPENAI_API_KEY는 사용자 소유의 비공개 실행 환경에서만 설정한다.
실제 모델과 web_search 호출은 비용이 발생하고, SRT 원문 및 새 주장의
일부가 API 제공업체로 전송될 수 있다. API 키를 GitHub에
커밋하거나 대화창으로 전송하지 않는다.

**지원:** 공식기관으로 허용한 HTTPS 도메인 아래 HTML 및 순수 텍스트.
실제 바이트의 SHA-256, 응답 시각, 문서 URL, 원문 대조 인용문,
모델 및 프롬프트 해시, 판단 범위가 개인 보고서에 남는다.
원본 응답 바이트는 private-evidence-dir 설정 시 0600 경로에 저장되며
변조된 기존 복사본은 재사용하지 않는다. 제한된 동일 기관 HTTPS
리디렉션은 허용하되 다른 기관으로의 이동, 개인 네트워크 주소,
과대한 문서 및 비인증 도메인은 차단한다.

**실제 근거 원문과 사실 승인 구별:** 기관 도메인을 검색했다고 발행기관
신원을 법적으로 입증한 것은 아니다. 기재된 법률의 효력일·적용
대상·상품 조건·예외·계산 전제는 별도 검토가 필요하다.
문서에 특정 구절이 존재하거나 LLM이 SUPPORTS라고 응답하더라도
심사자가 승인한 금융 사실로 승격하지 않는다.
모델이 INSUFFICIENT / CONTRADICTS / CONDITIONALLY_SUPPORTS를
판정하면 그 상태와 원문 인용 증거를 검토 대기열에 남긴다.

**현재 미지원 또는 미완성:** PDF 문서 본문 파싱, 웹사이트의
JavaScript 전용 자료, 모든 발언 의미의 독립 인간 누락 심사,
공식 문서의 법적 효력 인증, 복합 금융 공식 자동 검산,
독립 미노출 평가, 자동 최종 승인.

### 연동 시험 기준

GitHub Actions의 외부 공개 페이지 시험에서 국제결제은행(BIS)
공식 기관 페이지를 **실제로 HTTP 다운로드**해 텍스트와 원본
SHA-256을 추출하는 경로가 작동함을 확인했다.
이는 공개 기관 문서 **취득 성능만** 검증한 것이며
특정 투자 주장을 사실로 인증한 것은 아니다.

실제 원본에 대한 금융 의미 분석 API 호출은 현재 실행 환경에
OPENAI_API_KEY가 없어 아직 수행하지 않았다. 추출 재현율,
의미 정확도 및 공식 사실 승인은 현재 미측정이다.
