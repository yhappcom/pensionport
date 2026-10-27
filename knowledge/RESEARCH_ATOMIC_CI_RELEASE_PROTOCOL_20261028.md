# 박곰희TV 연구 GitHub Actions 실패 재발 방지: 원자적 배포 규칙 (2026-10-28)

## 원인
2026-10-27 GitHub Actions 로그에서 `Reject promotion of new incomplete canonical analyses` 실패를 확인: `data/analysis_events/1Hzf1eiM-t8.json`의 `LINKED_PILOT_EVIDENCE_GATE_BLOCKED`. 이는 미승인 원본등록부보다 정식 분석 JSON을 **먼저 브랜치에 커밋**해 발생했고, 잦은 커밋은 CI 취소도 발생시켰다. 최종 등록부 승격 시 Push/PR 모두 성공.

## 앞으로 강제할 순서
1. 비공개 Google Drive 원본 SRT의 SHA-256·bytes·cue 수 확인; `main` 수정 금지, ZIP/SRT 전문 업로드 금지.
2. 현재 roster ID 확인, 각 비공개 원본 SRT의 정확한 시간코드·주장·공식자료를 먼저 검토한다.
3. 승인용 registry, 각 video pilot, 각 canonical analysis, 심사보고서, 기존 검사코드의 새 배치 검증 블록을 **모두 완성**한다.
4. pilot은 `EVIDENCE_REVIEW_DRAFT / NOT_APPROVED`, canonical은 `COMPLETE / APPROVED`로 유지하되 1:1 고유 주장 ID·timecode·cue 인덱스 일치, official URL 및 `verification_evidence` 필수 필드 확인. Registry 배치 `v3_approval_count` 및 5개 승인 상태 **동시에** 승격.
5. 공개 브랜치에 기록하지 않고 GitHub Git Database `create_blob`을 이용해 파일을 먼저 staging, blob SHA를 확보. Git objects 생성 자체로 Actions가 실행되지 않는다.
6. 5편 canonical ↔ pilot claim set, registry ↔ roster ↔ pinned SHA, `source_audit`, 문서 요약 카운트를 교차 확인한다. 하나라도 불일치 시 **브랜치 커밋을 만들지 말고 수정된 새 blob만 재준비**.
7. 수정한 모든 blob SHA를 base tree 위에 `create_tree`로 묶고, `create_commit` 하나를 만든 뒤 `update_ref` 한 번만 실행한다(lease `expected_sha` 필수). 승인 후보만 공개 브랜치에 올라가도록 한다.
8. 동일 SHA의 Push CI/PR CI의 `completed success` 결과를 모두 확인한다. 실패 시 해당 run의 실패 job 로그로 원인을 밝히고 다시 *완성된 단일 추가 커밋*만 제출한다. 검사를 건너뛰거나 실패를 숨기지 않는다.

**절대 금지**: source intake만 먼저 커밋하고 나중에 approval 승격, pilot+canonical만 먼저 커밋, 등록부 등록 이전 V3 승인 커밋, 단순 테스트 용도로 실패할 것을 알면서 커밋, 빠른 연속 커밋으로 CI 취소 누적.

이 규칙은 새 채팅에서도 적용하는 지속 운영 지침이다.