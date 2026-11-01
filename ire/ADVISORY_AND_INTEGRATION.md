# IRE — 누적 투자 지식 및 자문 활용 아키텍처

2026-11-01. 현재 ChatGPT 대화가 금융 의미 해석을 직접 수행한다.
외부 언어모델 API와 기존 연구 결론·골드라벨은 사용하지 않는다.

## 최종 사용자 실행 흐름

사용자가 채팅에서 영상 1~5편 또는 신규 6~10편을 분석해 달라고 요청하면
ChatGPT가 IRE 원본 처리 도구, 의미 해석, 공식 근거 검색, 수치 검산과
원장 갱신을 조정한다. 분석 완료 때마다 다음 사항을 수행한다.

1. 원본 SRT 전체 검토 및 금융 원자 주장·조건·예외·수치 식별.
2. 새 공식기관 원문과 비교, 출처·적용 범위·효력 시점 확인.
3. 신규 주장과 **이전의 새 IRE 누적 원자 주장**을 교차 검색.
4. 같은 내용의 반복, 상호 보완, 수치 차이, 조건·관할·시점 변경,
   잠재적 반박을 구별하되 모든 자동 관계 분류를 검토 후보로 보존.
5. 상품 및 금융 사건별 통합 주제 뷰에 연결하고 원본 영상/자막의
   인용 계보 및 이전 스냅샷을 훼손하지 않음.
6. 공식 증거 및 별도 검토 없이는 검증된 사실로 자동 승격하지 않음.
7. 자문 질문에 대한 지식 검색과 충돌·날짜·이용자 적합성 확인 후
   실제 근거가 뒷받침하는 범위의 설명을 생성한다.

연구 완료 영상 수가 아니라 **누적 지식의 정확성·최신성·상충 해결·
자문 재현성**을 최종 품질 기준으로 삼는다.

## 구현된 누적 지식 엔진

파일: ire/knowledge.py

- 영상 ID + 원본 SRT SHA + 원자주장 ID로 만든 글로벌 지식 ID.
- 동일 SRT 바이트뿐 아니라 동일 자막 본문의 이중 집계 차단.
- 기존 새 IRE 연구 보고서와 새 영상 주장 간 구조화 의미 프레임 비교.
- 후보 관계: 부정 충돌, 수치 변형, 제도 적용일 변경,
  조건·예외 차이, 관할 차이, 재진술·추가 지지 가능성.
- 주제별 복수 영상·수치·날짜·조건을 묶은 통합 관점.
- 관계 후보는 독립 판정 전에는 참이라고 확정하지 않음.
- 추가형 불변 지식 스냅샷과 부모 버전 SHA, 0600 비공개 파일.
- 기존 연구 결론을 새 엔진의 골드라벨로 가져오는 경로 금지.
- API 호출, 무단 투자 사실 승인, 자동 지식 병합은 수행하지 않음.

## 채팅 분석 결과와 지식 원장 연계

처음 영상의 모든 문맥이 처리됐을 때:

    python -m ire.chat_bridge finalize \
      --original-srt /private/video001.srt \
      --video-id ABCDEFGHIJK \
      --source-sha256 ORIGINAL_SHA256 \
      --private-session-dir /private/chat_sessions \
      --private-knowledge-dir /private/new_ire_knowledge

두 번째 영상부터는 마지막 지식 원장의 경로를 추가한다.

    python -m ire.chat_bridge finalize \
      --original-srt /private/video002.srt \
      --video-id LMNOPQRSTUV \
      --source-sha256 ORIGINAL_SHA256_2 \
      --private-session-dir /private/chat_sessions \
      --private-knowledge-dir /private/new_ire_knowledge \
      --prior-knowledge-snapshot /private/new_ire_knowledge/PREVIOUS_SNAPSHOT.json

각 영상의 모든 문맥 구간 응답이 제출돼야 finalize가 작동한다.
기존 지식 저장소가 이미 존재하는데 이전 버전을 누락하면
빈 원장으로 초기화하지 않고 중단한다.

## 자문 질의

    python -m ire.knowledge advisory \
      --private-directory /private/new_ire_knowledge \
      --prior-snapshot /private/new_ire_knowledge/LATEST_SNAPSHOT.json \
      --question "ISA 만기 자금을 연금계좌로 옮길 때 고려할 조건은?" \
      --as-of 2026-11-01 \
      --jurisdiction KR

결과에는 질문 관련 원본 영상과 인용문, 잠정 통합 주제,
공식 근거가 필요한 주장, 가능한 충돌과 시간 차이가 포함된다.
이는 **자문용 근거 탐색 패킷**이며 정식 투자 실행 권고는 아니다.

실제 답변 시 ChatGPT는 패킷을 읽은 뒤 최신 공식기관 원문을 별도
검색하고, 해당 투자자의 세금 거주지, 계좌 유형, 투자기간, 손실
감내도와 유동성 수요를 확인해야 한다. 근거의 관할·효력 시점이
불분명하면 조건부 설명을 제시하고 확정 권고를 하지 않는다.

## 승인 단계 및 실전 미검증 사항

원본 분석만 통과한 주장: UNVERIFIED_REVIEW_REQUIRED.
동일 주제 클러스터: UNVERIFIED_TOPIC_CLUSTER_FOR_REVIEW.
영상 간 관계: PENDING_SEPARATE_ADJUDICATION.

현재 IRE에 독립 검토자 승인된 정답 자료나 전체 법령 시점
인증이 없기 때문에 자동 승인된 금융 사실과 투자 권고는 0건이다.
관계 검색 Recall@K, 시간/수치 충돌 검출 재현율, 실제 자문
정확도는 새 미노출 영상과 별도 평가자 자료로 검증해야 한다.
합성 회귀시험 통과만으로 금융 지식과 자문 시스템을 운영
승인하지 않는다.

이 채팅 중심 실행은 GPT 대화가 저장소 코드를 자동으로 원격
호출하는 완전 무인 프로세스는 아니며, 실행 도구·문맥 제한을
넘는 경우 기존 검증된 체크포인트를 보존한다.

과거 연구 파일은 그대로 보존. 과거 260편 결과와 차이를
비교하려면 신규 연구를 먼저 봉인한 후에 차이 탐지 자료로만
사용한다. 과거 기록의 주장을 새 엔진의 독립 정답으로 삼지 않는다.
