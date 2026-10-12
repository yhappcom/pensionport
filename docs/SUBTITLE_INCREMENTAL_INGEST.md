# 박곰희TV 자막 ZIP 증분 등록 — 2026-10-09

## 현재 확정 사실

- 기준 목록: `VIDEO_INVENTORY_2026-10-07.md`, 영상 791편 (롱폼 703, Shorts 88).
- 2026-10-09 최초 ZIP에서 실제 SRT 70개, 고유 영상 **69편** 확인(같은 영상 `5NvtBlmt93Y`의 동일 파일 사본 1개 중복). 이후 #60 단독 SRT 추가로 **총 고유 70편** 확보.
- 최초 1~70번 중 누락한 60번 `oMs4-3ZOevE`은 추가 등록 완료; 현재 **1~70번 누락 0편**.
- `data/subtitles/registry.json`은 **원본 전체 텍스트가 아닌** SHA-256/구간 수/시간/검수 상태 메타데이터만 보존.
- 71번 `4vNF2fui5jc`: 2026-10-09 사용자 확인 기준 무료 자막 페이지에 자막 없음. `data/subtitles/acquisition_issues.json`에서 `NO_TRANSCRIPT_ON_SITE_REPORTED_BY_USER`로 관리하며 70편 수집 완료 통계에 포함하지 않는다. YouTube 원본 자막 부재까지 확인된 것은 아니다.
- 현재 70편은 `SRT_STRUCTURE_CHECKED` 및 `CONTENT_INDEXED`(기계적 주제/시간코드 색인), `NOT_VERIFIED` 상태다. 심층 금융 분석 및 사실 검증 완료와 혼동하지 않는다.
- 2019년 영상 2편의 기존 V4/V3 분석 상태는 이 수집 관리대장과 별도; 데이터베이스 이전 분석을 임의로 완료 처리하지 않는다.

## 2026-10-12 원본 SRT 재확보·백업 검증

- **복구 완료:** 사용자 제공 `1-70.zip` 1,558,752바이트를 확보했다. ZIP에는 유효 원본 SRT 71개(중복 영상 ID `5NvtBlmt93Y`의 동일 SRT 2개), **고유 70편**이 들어 있다. 이전에 따로 취급했던 #60 `oMs4-3ZOevE`도 이번 ZIP에 포함돼 있다.
- **원본 ZIP SHA-256:** `00024d54bbca57c8c9f528d3c6c2f4766052ad2dc37bf4f132280dbd223dd8fd`.
- **70/70 등록 원본 일치:** 모든 영상에서 개별 SRT 바이트 SHA-256·구간 수·종료 시각이 `data/subtitles/registry.json`의 기존 등록값과 일치한다. 구조 검사 오류와 누락 없음.
- **두 비공개 백업 업로드 및 읽기 재검증:** 사용자 소유 비공개 Google Drive `박곰희TV_SRT_원본보관함/1-70.zip` 및 ChatGPT 개인 Library `박곰희TV_원본확보/1-70.zip`에 보관. 저장된 두 ZIP을 각각 재조회해 원본과 SHA-256 및 바이트 일치를 검증했다. 공개 GitHub에 전체 SRT 원문·ZIP을 저장하지 않는다.
- **13번 검증 완료:** `keu5SvpD7KE` SRT 등록 해시가 일치하고 27개 구간(마지막 60.879초)의 전체 텍스트가 2026-10-12 독립 조회 공개 한국어 자동전사 27개 줄 / 506자와 정확히 일치한다. 9개 주장 시작 구간도 SRT 시각으로 갱신했다.
- **남은 한계:** 독립 YouTube **오디오 및 화면**과 실제 발화를 대조한 것은 아니다. 원본 SRT와 공개 ASR이 같은 잘못된 인식을 공유할 수 있다. `07%`, `연의 월배당` 등은 음성·화면 검증 전 미확정이다. 나머지 69편의 공개 전사와의 문장별 대조도 별개로 미완료다.
- **향후 신규 자료 보호:** `scripts/recover_subtitle_sources.py`는 기존 등록 해시·구간 수·종료시각을 검사해 두 독립 보관 위치의 파일을 검증한다. `ingest_subtitle_zip.py --apply`도 두 사본의 검증을 요구한다. 다만 도구의 개인 로컬 2사본 검사와 이 회차 비공개 Drive·Library 백업 읽기 검사는 **서로 다른 검증 절차**이므로 구분한다.

### 과거 13번 원본 복구·검사

```bash
# 원본을 개인 로컬 보관 경로 2곳에도 별도로 복원/검증하려는 경우에만 실행.
python scripts/recover_subtitle_sources.py \
  --archive /private/original.zip \
  --registry data/subtitles/registry.json \
  --video-id keu5SvpD7KE \
  --vault-dir /private/srt-primary \
  --backup-dir /another-private-backup/srt \
  --apply

# 다시 원본을 열어 두 사본의 해시·구간·끝시각을 검증한다.
python scripts/recover_subtitle_sources.py \
  --registry data/subtitles/registry.json \
  --video-id keu5SvpD7KE \
  --vault-dir /private/srt-primary \
  --backup-dir /another-private-backup/srt \
  --verify-only
```

`--archive`는 반복 지정 가능하며 ZIP 또는 `youtube-transcript-<video_id>.srt`를 받는다. 전체 70편 검증 시 `--video-id` 생략, 현재 복구한 `1-70.zip` 단일 파일을 제공하면 된다. 상태가 `TWO_COPIES_VERIFIED`가 아니면 SHA가 다르거나 바이트가 없어 복구 완료로 처리하지 않는다. 이 검증은 **원본 확보와 저장 무결성**만 확인하며 공개 전사와의 문장별 비교는 다음 별도 단계다.

### 앞으로 새 ZIP을 등록하는 안전한 순서

1. 아래 `ingest_subtitle_zip.py`를 **`--apply` 없이** 실행해 `registry_preview.json` 생성.
2. `recover_subtitle_sources.py --archive <new.zip> --registry /tmp/subtitle_audit/registry_preview.json --vault-dir <private> --backup-dir <independent_private> --apply`로 신규 해시를 포함한 미리보기 레지스트리에 대해 비공개 원본 두 사본 복구/검증.
3. 원본 ZIP 자체를 비공개 Google Drive 보관함에 장기 보관했는지 별도 확인.
4. `ingest_subtitle_zip.py --apply --vault-dir <private> --backup-dir <independent_private>`로 **두 사본 재검증에 성공한 신규 SRT만** 레지스트리에 반영.
5. 전체 전사·공개 전사·원음의 타임코드·숫자를 대조한 뒤, 검증한 내용만 별도 연구 파일에 반영. 비교 불가능한 항목은 계속 OPEN.

**보존 상태:** 2026-10-12 실제 ZIP 복구 및 Google Drive·개인 Library 2개 사본 다운로드 재검증을 마쳤다. 13번 원본과 공개 자동전사 전체 텍스트 대조는 완료했으며, 원음/화면 검증 및 다른 영상의 독립 공개전사와의 비교는 계속 별도로 수행한다.

## 다음 ZIP 처리

사용자는 새로운 SRT들을 기존 파일과 중복돼도 그대로 ZIP으로 올릴 수 있다. 다운로드 이름에 YouTube 영상 ID가 있어야 한다. 프로그램은 ZIP의 SRT를 읽고, ID와 SHA-256을 기존 70편 상태에 비교한다.

```bash
python scripts/ingest_subtitle_zip.py \
  --archive /path/to/new_subtitles.zip \
  --roster data/subtitles/roster_20261007.csv \
  --registry data/subtitles/registry.json \
  --out-dir /tmp/subtitle_audit
```

기본값은 **미반영(dry run)**이다. 결과 `batch_audit.csv`, `intake_report.json`, `registry_preview.json`을 검토한다. 신규 등록 시에는 위의 비공개 원본 2사본 검증 절차를 먼저 거치고, 동일 명령에 `--apply --vault-dir <private> --backup-dir <independent_private>`를 붙여 **NEW로 판정되고 원본 바이트가 두 곳에 검증된** 영상만 등록한다.

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
