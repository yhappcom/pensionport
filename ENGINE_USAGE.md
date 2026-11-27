# D1 최소 엔진 사용법

Python 3.10+ 표준 라이브러리만 사용한다. D1 실행 검증은 Python 3.13.5 / SQLite에서 수행했다. `engine.py`는 저장·조회·구조 검사만 한다. SRT UTF-8(BOM 허용), 연속 번호, 정상 시간 및 본문을 읽으며 겹치는 자막은 허용한다. 다른 인코딩/비표준 SRT는 오류로 보고하며 임의 교정하지 않는다. 영상 ID가 확인되지 않은 경우 원문 SHA-256을 식별자로 사용한다.

## 두 턴의 연결

```sh
# 1턴: 원문과 현재 신규 지식 후보를 JSON으로 출력하고 원문 바이트를 저장
python engine.py --db research.db prepare source.srt ETF 순자산 > prepared.json
# ChatGPT가 prepared.json 전체를 읽고 공식 자료를 새로 검색해 draft.json 작성
python engine.py --db research.db draft draft.json
# 2턴: 준비된 원문, 저장 초안, 초안 해시, 최신 지식 head를 복구
python engine.py --db research.db resume SOURCE_SHA ETF 순자산 > resumed.json
# ChatGPT가 원문 재대조·새 근거·기존 지식 비교 후 final.json 작성
python engine.py --db research.db finalize final.json
python engine.py --db research.db query ETF 순자산
python engine.py --db research.db status
```

`prepare`와 `resume`의 `cues`는 자막 번호·시작/종료 ms·본문을 모두 제공한다. `candidates`는 현재 승인된 신규 지식의 키워드 후보이며, 의미 관련성과 충분성은 ChatGPT가 판단한다. 관련 검색어를 복수로 사용하고 필요하면 추가 `query`를 실행한다. `head`가 변하면 최신 자료를 다시 검토한 후 판정 입력을 작성해야 한다. 동일 초안·최종 요청의 재시도는 중복 저장하지 않는다. 최종 결과는 한 번 저장되고, 동일 영상의 결과를 직접 수정하지 않는다. 후속 영상은 이전 지식에 보완·교정·충돌 관계를 연결할 수 있다. 동일 원본에 대한 후속 재판정 경로는 D1 범위 밖이며 필요 시 실제 실패 사례에 기반해 설계한다.

## 최소 입력 계약

`draft.json` 및 `final.json`의 최상위 필드:

- `mode`: `research` (실제 연구) 또는 `test` (기술 검증 전용, DB 생성 시 고정)
- `source_id`: prepare의 원본 SHA-256
- `head`: prepare/resume의 지식 head
- `review_note`: ChatGPT의 검토 범위, 미해결 사유 및 최종 변경 근거; 의미 판정 인증이 아니라 작성자의 기록
- `claims`: 아래 연구 항목 목록
- `nonclaim`: `[{"cues":[번호,...],"reason":"비연구/반복 등 제외 근거"}]` (근거 없는 일괄 제외 금지)
- `draft_sha`: finalize에서만 필요, resume의 값 그대로 사용

항목 필드:

| 필드 | 내용 |
|---|---|
| id | 영상 내부 고유 ID (영문·숫자·하이픈·밑줄) |
| cues | 실제 원문 자막 번호 목록 (원문 본문·시간은 엔진이 직접 첨부) |
| topic, statement, speaker | 주제·원래 발언의 의미·화자 (불확실하면 명시) |
| kind | FACT, OPINION, ASSUMPTION, QUESTION, OTHER |
| conditions, exceptions, numbers | 조건·예외·수치/단위/맥락 문자열 목록, 없으면 빈 배열 |
| time_scope | 적용 시점 및 불확실성 |
| verdict | APPROVE, CORRECT, DUPLICATE, CONTEXT, HOLD, EXCLUDE |
| reason | ChatGPT 최종 판정의 실질적인 이유 |
| knowledge | 승인/교정/동치의 검증된 범위만 작성, 나머지는 빈 문자열 |
| evidence | 근거 목록 (아래 필드) |
| depends_on | 성립에 필요한 항목 ID. 같은 영상의 로컬 ID 또는 `SOURCE_SHA:ID` |
| relations | `[{"type":"SAME/EXTENDS/CORRECTS/CONFLICTS/DISTINCT","target":"SOURCE_SHA:ID","reason":"관계의 의미·범위 근거"}]`; 신규 독립 지식은 빈 배열 |

근거 한 건의 필드: `issuer`, `title`, `url`(HTTPS), `checked_on`(YYYY-MM-DD), `applies_on`(시행일 또는 적용일 불확실성), `scope`, `excerpt`(짧은 인용/요약과 문서 위치), `access`(`WEB`/`BYTES`; `TEST`는 시험 DB만). 실제 원문 바이트를 직접 확보한 경우에만 `BYTES` 및 `sha256`을 기록한다. 엔진은 근거 메타데이터 형식만 검사하며 웹/바이트의 진위 또는 금융 의미를 인증하지 않는다. ChatGPT가 실제 근거를 확인하고 적용 범위를 판단해야 한다.

예시: `APPROVE`와 `CORRECT`는 FACT만 허용하고 근거를 요구한다. `DUPLICATE`는 기존 활성 지식에 SAME을 정확히 하나 연결하며 기존 지식과 동일한 의미·조건인지는 ChatGPT가 판정한다. `CONTEXT`, `HOLD`, `EXCLUDE`는 일반 사실 조회에서 제외한다. `CORRECTS`는 검증된 새 교정으로 이전 활성 지식을 대체하고, `CONFLICTS`는 미해결 충돌로 이전 지식의 일반 조회를 차단한다. 원문과 모든 판정은 보존된다. 차단 지식에 의존하는 후속 지식도 조회에서 제외된다. 승인된 항목 조회에는 명시된 의존 지식 및 동치 출처가 함께 반환된다.

최종 입력에서 전체 자막은 주장 출처 또는 근거를 명시한 비연구 항목으로 연결되어야 한다. 이 검사는 구조적 누락 검사일 뿐 원문 의미를 모두 읽거나 올바르게 검증했다는 증거가 아니다. 2턴 최종 검증은 ChatGPT가 직접 수행한다. `status.finalized`는 영상 저장 트랜잭션 완료 수이며 금융 사실의 전수 승인 또는 연구 품질 합격 수가 아니다. 연구 완료 여부와 2턴 준수는 개발 일지에서 별도 판단한다.

## 시험

```sh
python -m unittest -v test_engine
# 개인 보관 SRT가 있는 경우: 원본을 공개 저장소로 복사하지 않는다.
SRT_DIR=/path/to/srt python -m unittest -v test_engine
```

시험 DB의 `test` 모드는 실제 연구 DB로 열 수 없다. 시험의 근거·주장·전체 커버리지는 기술적 가상 입력이며 금융 지식이 아니다. 원문 세 편의 로딩 및 저장·재개 경로 검증만 수행한다. 실제 연구는 D2에서 처음 수행한다. D1은 외부 API를 호출하거나 다음 턴을 자동 실행하지 않는다. 연구 DB와 초안은 다음 턴에 복구 가능한 비공개 보관 위치에 저장해야 한다. GitHub에는 코드·공개 문서만 반영한다. 포트폴리오 연계는 하지 않는다.
