# 박곰희TV 학습 목록 — Master Inventory v2

- 갱신일: 2026-10-02
- 기준 채널: `@gomhee`
- 현재 공개 채널 총 업로드 수(제3자 공개 통계): **793개**
- Video ID까지 식별된 롱폼 후보: **114편**
- 기존 분석과 매핑된 영상: **46편**
- 식별됐지만 미처리: **68편**
- 게시일 확보: **40편**
- 제목/게시일은 확인됐지만 Video ID 미해결: **19편**
- Shorts: 학습 본체에서 제외
- 중복 기준: Video ID

## 목록의 의미

이 파일은 앞으로 학습에 사용하는 단일 마스터 큐다.

- 식별 완료: `data/learning_queue.jsonl`
- ID 미해결 롱폼: `data/learning_queue_unresolved.jsonl`
- 분석 완료 여부: `inventory_status`
- 날짜 미확정: `chronology_status=date_unverified`

## 완전성 상태

**운영상 마스터 목록 구조는 완성했다. 다만 현재 공개 롱폼 전수 ID 확보는 아직 검증 불가 상태다.**

2026-10-01 기준 공개 채널 통계는 전체 업로드 **793개**를 표시한다. 이 숫자는 Shorts를 포함한다. 현재 접근 가능한 YouTube 웹 표면은 전체 Videos 탭을 페이지네이션해 내보내지 않으며, Tenbi 역시 영상 목록은 JavaScript가 필요하다고 표시한다.

따라서 `793 - Shorts = 롱폼 총개수`를 현재 도구만으로 정확히 산출했다고 주장하지 않는다. 대신 접근 가능한 공개 인덱스에서 확인되는 모든 롱폼을 큐에 누적하고, 새 ID가 발견되면 중복 없이 추가한다.

## 소스 통합

1. pensionport 기존 처리 데이터
2. DoLearn 보존 박곰희TV 커리큘럼
3. 공개 GitHub `chanhi2000/devlog`의 박곰희TV 영상 메타데이터
4. YouTube 원본 메타데이터
5. RankTube
6. ifvest / Socialerus / CreatorAfterWork 등 최근 공개 인덱스

## 분류 규칙

- `processed`: 이미 분석 저장 완료
- `identified_unprocessed`: Video ID 확인, 아직 분석 전
- `date_unverified`: ID/제목은 확인했지만 정확한 게시일 추가 검증 필요
- `video_id_unresolved`: 제목/날짜는 확인됐지만 ID가 아직 없음
- `video_id_unresolved_compilation`: 몰아보기/재편집형 롱폼 후보
- Shorts는 별도 보조자료로만 취급

## 학습 재개 조건

이제부터는 새 영상을 임의 검색해 처리하지 않고:
1. 마스터 큐에서 게시일이 확정된 가장 오래된 `identified_unprocessed`를 선택한다.
2. 날짜 미확정 항목은 날짜를 보강해 큐에 끼운다.
3. 새 영상이 발견되면 먼저 이 목록에 등록한다.
4. 이후 분석한다.

## 남은 완전성 검증

현재 유일한 큰 미해결은 **YouTube의 현재 공개 롱폼 전체 업로드 ID를 한 번에 얻을 수 없는 점**이다. vidIQ 같은 채널 업로드 탐색 연동이 연결되면 이 마스터 큐와 전수 대조해 누락 여부를 최종 검증할 수 있다.
