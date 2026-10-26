# 박곰희TV 연구 CI 실패 알림 예방 및 안전한 배치 저장 (2026-10-26)

## 왜 GitHub 실패 메일이 반복됐는가

연구용 브랜치 `feat/subtitles-incremental-registry-20261009`의 `Subtitle evidence review gate`는 해당 경로를 수정하는 **매 push** 및 관련 PR 이벤트를 검사한다. #161~165 작업에서는 출처 등록부, 초안 근거, 승인용 정식 JSON, 집계와 검사 코드가 여러 커밋으로 순차 저장됐다. 그 사이 일부 새 V3 파일은 `MISSING_RELATIONS`, `LINKED_PILOT_EVIDENCE_GATE_BLOCKED` 같은 필수 근거 검사를 통과하지 못했다. GitHub는 각 실패 실행을 개별 메일로 통지하며, 이후 최종 CI 성공이 기존 실패 메일을 철회하지 않는다.

**목표는 실패 알림 숨기기가 아니라, 실패하기 쉬운 불완전한 중간 커밋의 원격 push를 줄이는 것이다.** 이 정책으로 모든 오류를 막을 수는 없으며, 실제 오류를 탐지하는 CI는 유지한다.

## 반드시 지킬 작성·저장 순서

1. **연구 완성:** 같은 배치의 원본 SRT 해시·큐 수·영상 ID 검증, 주장별 공식자료/발효일·정정, `source_audit`, `verification_evidence`, `relations`, `evidence_gate`, 모든 누적 원장과 보고서를 함께 준비한다. 원본 SRT/ZIP은 Google Drive 비공개 보관함에만 저장한다.
2. **검사 가능한 묶음:** 신규 `data/subtitles/pilots/<video_id>.json`은 `EVIDENCE_REVIEW_DRAFT / NOT_APPROVED`, 정식 `data/analysis_events/<video_id>.json`은 **실제 검증 후에만** `COMPLETE / APPROVED`. 신규 원본 등록부를 해시·로스터·cue·바이트 확인 규칙에 연결해야 한다. 숫자나 사적 실적의 확인 누락은 `OPEN`/조건부로 남기며 승인으로 부풀리지 않는다.
3. **업로드 전 검사:** 로컬 Git 복제본에 필요한 파일만 **명시적으로 stage**한 후 아래의 사전검사 도구를 실행한다. 오류가 있으면 push 전에 수정하고 재실행한다. `--self-test`는 도구 자체 점검일 뿐 배치 데이터 검증을 대체하지 않는다.
4. **한 번에 반영:** 동일 배치를 **가능하면 단일 원격 커밋/단일 push**로 처리한다. GitHub API 기반 작성자는 전체 JSON/문서를 메모리 또는 별도 격리 작업 브랜치에서 완성·자체검사하고, 해당 연구 브랜치로 최종 반영할 때 불완전한 중간 커밋을 남기지 않는다. 원격 API 개별 파일 쓰기는 각 커밋을 생성하므로 사용 시 중간 CI가 다시 트리거될 수 있다는 점을 보고한다.
5. **서버 검증과 재조회:** GitHub Actions 최종 실행 상태 `success`를 확인하고 JSON·원장/보고서를 다시 읽어 실제 승인 수치를 갱신한다. `queued`, `in_progress`, `failure`, `cancelled`는 성공으로 간주하지 않는다.
6. **실패 대응:** 실패 시 가장 먼저 게이트의 **실패 단계·로그·커밋 ID**를 확인한다. 원본 해시·누락 필드·정정 근거를 보완해 다시 검사한다. 테스트 건너뛰기, `continue-on-error`, 게이트 비활성화, 불완전한 승인을 위해 완화된 기준 적용은 금지한다.

### 로컬 Git에서 실행하는 사전검사

```bash
# 최초 1회: 저장소 연구 브랜치에서 작업
git switch feat/subtitles-incremental-registry-20261009

# 원본 .srt/.zip은 절대 stage하지 않는다. 파일 선택은 배치에 맞게 조정한다.
git add scripts/audit_subtitle_review_gate.py \
  data/subtitles/registry_166_170_YYYYMMDD.json \
  data/subtitles/pilots/*.json \
  data/analysis_events/*.json \
  data/subtitles/research_progress_batch_166_170_YYYYMMDD.json \
  knowledge/VIDEO166_170_*.md

python -B scripts/preflight_subtitle_batch.py
# PASS 확인 후 한 번에 커밋 및 push
git commit -m "research: approve evidence-reviewed subtitle batch"
git push origin feat/subtitles-incremental-registry-20261009
```

위 예시는 향후 배치 파일명을 표시한 **명령 패턴**일 뿐이며, 현재 #166~170 파일이 있다는 뜻이 아니다. `git add` 전에 모든 해당 파일이 존재하는지, 기존 데이터가 무단 변경되지 않았는지 확인한다. `preflight_subtitle_batch.py`는 읽기 전용이며 staged 파일의 금지 원본 확장자, index/working tree 불일치, 등록 소스, 승인 후보와 연계된 pilot의 증빙 게이트를 확인한다. 이 도구만으로 법령 링크의 실제 진위·원음·화면이 검증되는 것은 아니다.

## GitHub Actions 설정

`.github/workflows/subtitle-review-gate.yml`에 동일한 연구 브랜치의 실행을 묶는 아래 설정을 둔다.

```yaml
concurrency:
  group: subtitle-evidence-${{ github.head_ref || github.ref_name }}
  cancel-in-progress: true
```

- 새 push 또는 같은 브랜치 PR 이벤트가 발생하면 **아직 실행 중인 이전 검사**를 취소하고 최신 실행을 우선한다. 이미 종료된 실패 실행과 메일을 없애지는 못한다.
- 원본 SRT/ZIP의 공개 업로드 차단, 연구 증빙/반증·원본 해시 검사, CI 오류 시 차단은 그대로 유지한다.
- CI 트리거를 끄거나 `continue-on-error`로 실패를 성공처럼 처리하지 않는다.
- GitHub 개인 계정의 이메일 수신 설정은 저장소 워크플로 파일과 **별개**다. 전체 오류 통보를 끄는 것은 권장하지 않으며 계정 알림 변경은 소유자 확인에 따른다.

## 운영 결과의 승인 기준

- **로컬 사전검사 PASS + 원격 최종 GitHub Actions SUCCESS + 저장된 파일 재조회**를 만족해야 새 V3를 ‘정식 완료’로 보고한다.
- 중간 실패 메일은 해당 실행 당시의 실제 실패 사실을 뜻하지만, 최종 승인 상태는 **마지막 관련 커밋/CI**로 확인한다.
- 기존 `main`·기승인 근거·비공개 원본은 보존한다. 자동 병합이나 사용자 알림 설정 변경은 이 정책에 포함되지 않는다.
