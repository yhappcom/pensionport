# 박곰희TV 선행 학습 Inventory Plan

## 목적
예약 분석 실행이 매번 새 영상을 찾는 데 시간을 쓰지 않도록, 학습 대상 exact Video ID를 먼저 충분히 목록화한다.

## 현재 snapshot — 2026-10-06
- exact-ID master inventory: **161편**
- canonical processed: **139편**
- exact-ID 미처리 buffer: **22편**
- source acquisition 필요: **9편**
- verification_needed: **13편**
- source-backed ready: **0편**
- Video ID unresolved: **2편**

## Reservoir 목표
- 목표 미처리 exact-ID buffer: **100편**
- 최소 안전 buffer: **60편**
- discovery batch: 최대 **40편**
- source acquisition batch: 최대 **20편**

buffer가 60편 미만인 동안은 inventory bootstrap을 선행한다. 분석 가능한 source-backed 영상이 생기면 실제 분석도 병행하지만, 다음 실행을 위해 exact-ID 목록을 계속 쌓는다.

## 새로 선등록한 exact-ID 후보
| inventory | Video ID | 제목/신호 | 상태 |
|---:|---|---|---|
| 153 | `Sk1JarcNNNs` | 남은 현금은 모두 CMA에 넣어둬야 하는 이유 ver.2025 | source_acquisition_needed |
| 154 | `PW1EuMtw18o` | ISA·건보료 관련 원본 | source_acquisition_needed |
| 155 | `UzoZbeqcctg` | ISA 사용 설명서 | source_acquisition_needed |
| 156 | `fnLgP_KCv8A` | ISA Q&A 원본 | source_acquisition_needed |
| 157 | `a6ET79jF7Xk` | 곰희스쿨 38강 - 주식 차트 보는 법 | source_acquisition_needed |
| 158 | `Dmq6Tw3Gy7Q` | IRP 안전자산 30% | source_acquisition_needed |
| 159 | `giJLCf3ed_s` | ISA를 할까? 연금저축을 할까? | source_acquisition_needed |
| 160 | `l5PUUXweyGs` | 주부도 연금저축 하는 게 좋을까? | source_acquisition_needed |
| 161 | `wI6Kd-BJqqk` | 연금저축과 IRP의 결정적인 차이 | source_acquisition_needed |

## 운영 순서
1. exact-ID inventory를 먼저 확대한다.
2. 신규 ID는 full source가 없어도 inventory에 등록한다.
3. source acquisition을 별도 배치로 수행한다.
4. 충분한 source가 확보된 영상만 `source_backed_ready`로 승격한다.
5. content lane은 ready 목록에서만 최대 40편씩 분석한다.
6. verification_needed는 retry due 또는 신규 source 신호가 있을 때만 다시 찾는다.
7. buffer가 60 미만이면 다음 실행에서도 inventory bootstrap을 우선한다.

## 전수 inventory source
- 공식 YouTube channel/playlist/공개 링크
- 공식 Shorts가 연결한 full-video ID
- 공개 강의·커리큘럼·인덱스
- exact YouTube embed/link가 있는 contemporaneous 리뷰·요약
- 검색엔진 exact watch/youtu.be 링크

## 완료 기준
전체 채널 롱폼의 exact-ID 전수확정이 최종 목표다. 단기적으로는 미처리 buffer 100편을 먼저 확보해 분석이 discovery 때문에 멈추지 않도록 한다.
