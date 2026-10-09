# 박곰희TV 자막 ZIP 증분 등록 — 2026-10-09

## 현재 확정 사실

- 기준 목록: `VIDEO_INVENTORY_2026-10-07.md`, 영상 791편 (롱폼 703, Shorts 88).
- 2026-10-09 최초 ZIP에서 실제 SRT 70개, 고유 영상 **69편** 확인(같은 영상 `5NvtBlmt93Y`의 동일 파일 사본 1개 중복). 이후 #60 단독 SRT 추가로 **총 고유 70편** 확보.
- 최초 1~70번 중 누락한 60번 `oMs4-3ZOevE`은 추가 등록 완료; 현재 **1~70번 누락 0편**.
- `data/subtitles/registry.json`은 **원본 전체 텍스트가 아닌** SHA-256/구간 수/시간/검수 상태 메타데이터만 보존.
- 71번 `4vNF2fui5jc`: 2026-10-09 사용자 확인 기준 무료 자막 페이지에 자막 없음. `data/subtitles/acquisition_issues.json`에서 `NO_TRANSCRIPT_ON_SITE_REPORTED_BY_USER`로 관리하며 70편 수집 완료 통계에 포함하지 않는다. YouTube 원본 자막 부재까지 확인된 것은 아니다.
- 현재 70편은 `SRT_STRUCTURE_CHECKED` 및 `CONTENT_INDEXED`(기계적 주제/시간코드 색인), `NOT_VERIFIED` 상태다. 심층 금융 분석 및 사실 검증 완료와 혼동하지 않는다.
- 2019년 영상 2편의 기존 V4/V3 분석 상태는 이 수집 관리대장과 별도; 데이터베이스 이전 분석을 임의로 완료 처리하지 않는다.

## 다음 ZIP 처리

사용자는 새로운 SRT들을 기존 파일과 중복돼도 그대로 ZIP으로 올릴 수 있다. 다운로드 이름에 YouTube 영상 ID가 있어야 한다. 프로그램은 ZIP의 SRT를 읽고, ID와 SHA-256을 기존 70편 상태에 비교한다.

```bash
python scripts/ingest_subtitle_zip.py \
  --archive /path/to/new_subtitles.zip \
  --roster data/subtitles/roster_20261007.csv \
  --registry data/subtitles/registry.json \
  --out-dir /tmp/subtitle_audit
```

기본값은 **미반영(dry run)**이다. 결과 `batch_audit.csv`, `intake_report.json`, `registry_preview.json`을 검토한다. 확인 후에만 같은 명령에 `--apply`를 붙여 **NEW로 판정된** 영상만 등록한다.

| 판정 | 의미 | 처리 |
|---|---|---|
| `NEW` | 기준 목록에 있고 처음 확보한 정상 SRT | 반영 후보 |
| `UNCHANGED` | 기존 영상과 SHA-256 동일 | 건너뜀 |
| `REVISED_REVIEW` | 같은 영상 ID, 자막 파일 내용 변경 | 원본·신본 비교 전까지 덮어쓰지 않음 |
| `CONFLICT_IN_BATCH` | 한 ZIP 안에 같은 ID의 서로 다른 자막 | 검수 대기 |
| `INVALID_SRT` | 시간코드/구조 오류 | 보류 |
| `OUTSIDE_ROSTER` | 영상 ID가 2026-10-07 목록 외 | 사용자 확인 후 로스터 갱신 |
| `UNRECOGNIZED_FILENAME` | 파일명에서 ID를 식별할 수 없음 | 파일명 확인 |

**한계:** 유효한 시간코드/형식 여부만 확인한다. 자동자막의 원음 일치·금융정보의 진위·영상 화면은 전혀 자동 승인하지 않는다. 영상 게시일과 촬영일을 혼동하지 않는다.

## 학습 연결 규칙

수집과 학습을 분리한다.

1. `SRT_STRUCTURE_CHECKED`: 파일명/ID/해시/타임코드 구조를 검사했다.
2. `CONTENT_INDEXED`: 실제 자막을 읽고 시간코드별 주요 주제를 추출했다.
3. `ANALYZED`: 주장의 전제·예외·수치·투자위험을 구분한 영상 분석이 존재한다.
4. `EVIDENCE_VERIFIED`: 필요한 금융상품·규정·세법 등의 공식자료를 독립 검증했다.
5. `APPROVED`: 검증 범위/한계를 포함한 리뷰가 완료되어 지식베이스에 연결 가능하다.

앞 단계 완료 없이 뒤 단계를 자동 승인하지 않는다. 영상 분석의 정식 기록은 기존 V3 워크플로의 `data/analysis_events/<video_id>.json` 또는 별도 심사가 필요한 V4 구조에 따라 **근거를 포함해 개별 저장**한다. 이 메타데이터 레지스트리는 기존의 완료 숫자·학습 기록을 재계산하거나 덮어쓰지 않는다.

## 보안·저작권·데이터보존

- 타인의 **전체 SRT 원문을 공개 저장소에 커밋하지 않는다**. 개인 비공개 보관함에 원본 ZIP을 유지한다.
- ZIP 내부 경로를 디스크에 풀지 않고 각 SRT를 메모리에서 검사한다.
- 재처리의 핵심 키는 `video_id + SHA-256`이다. 같은 ID 다른 해시는 무음 덮어쓰기 금지.
- 채팅에만 업로드한 파일은 만료될 수 있다. GitHub에는 수집 상태만 남고 원문 ZIP은 남지 않으므로 원본을 별도 보존해야 한다.
- `main`에는 검토 후 병합하며, 다른 V4 검토용 브랜치/PR에는 영향이 없다.

## 다음 검증 단계

1~70번의 **자동 주제·시간코드 색인**은 `data/subtitles/content_index_001_070.json`과 `docs/SUBTITLE_CONTENT_INDEX_001_070.md`에 기록했다. 다음에는 2번·28번·36번의 주장을 원문 전체·공식자료와 교차 검증한다. **내용 색인과 심층 분석/공식 검증 상태를 분리**하고, 학습 승인은 증거가 있을 때만 한다.
