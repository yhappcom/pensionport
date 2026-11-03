# IRE V4 P0-R 실행 경로 확인 및 실제 증거 판정 (2026-11-03)

## 실행 주체별 확인
- 일반 Chat: 파일 접근과 유한 모델 의미 분석은 수행 가능하나 채팅 종료 후 **호스트 자체의 자율 재실행**은 이 세션에서 실증되지 않았다.
- 공식 ChatGPT Work 클라우드 실행: 공식 도움말에 대화 이탈·기기 종료 후 작업 지속이 명시되어 있음. 단, 사용자 입력·승인·로그인 상황에서는 일시정지. [Cloud Browser](https://help.openai.com/en/articles/20001280-using-cloud-browser-in-chatgpt).
- 예약 작업: 독립적으로 모델 작업을 시작할 수 있으나, 프로젝트 업로드 파일을 그대로 사용할 수 없을 수 있음. 동일 host task와 중단 시점의 source/meaning/checkpoint 및 승인 상태를 연속 승계하는 증거가 아니므로 P0-R 대체 불가. [Scheduled Tasks](https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt).
- GitHub Actions·Python: 독립 source-validator/체크포인트 복구 가능, API 없는 ChatGPT 모델 호출·호스트 자체 복귀를 대체할 수 없음.

## 이번 턴에서 실제 수행
- P0-R 최소 증거 계약에 대한 표준 라이브러리 Python fail-closed validator 작성. 소스 SHA, provider event id, host task id, 전·후 host invocation 분리, 4문맥 뒤 종료, 호스트 자체 재시작 트리거, 재개 후 8문맥, 12개 window census, 정확한 event hash chain 및 외부 telemetry 인증 플래그 검증.
- 회귀시험 9개 PASS (합성 정상 경로 1 + 거절 시험 8). 이는 **검증기 테스트일 뿐 실제 호스트 실행 성공 아님**. 메시지로 재개, scheduler 재시작으로 둔갑, telemetry 누락, source 누락, checkpoint 변조, 같은 host invocation 재사용 시 거절.
- 현재 관찰된 실제 Chat 상태에 검증기 적용: `BLOCKED`, 9개 사유 (host task id/host start/host termination/restart/telemetry/independent recovery/V3 gate/window set/final report).
- 검증기 SHA-256: `39cf577eb48cdc83665954c7a265b0ef43169e309a54fa33efb4e5e39624b70a`; 테스트 SHA-256: `cd9c866fefb2e20517b0da955941386a2659d6e6a4058ae12427aed6917c4138`.
- validator / 테스트 / 비공개 개인 데이터와 구분된 JSON 결과는 대화의 로컬 산출물에 보존됨. 공용 GitHub에 비공개 원본이나 주장 전문 업로드 없음.

## 중요한 보안 설명
테스트 입력 JSON의 `host_telemetry_independently_verified=true` 자체는 외부 인증이 아님. 해시만으로 위조된 호스트 이벤트를 진짜로 만들 수 없음. 실제 P0-R **GO**는 호스트 제공 이벤트·작업 ID를 신뢰 가능한 실행 기록과 별도로 비교하고 권한·출처 경계·12개 신규 모델 판단·사용자 추가 메시지 0개가 실제 입증된 경우에만 허용.

## 판정 및 개발 방향
**P0-C 유한 시험 통과, P0-R 실제 호스트 증거 미확보로 P0 전체 BLOCKED.** P1~P4 운영 승인 보류.

사용자가 명시적으로 현재 Chat만 사용하기로 결정한 상태이므로 강제 Work 전환·예약 태스크 생성은 실시하지 않음. 원래 요구인 '중단 이후 사용자 추가 요청 없이 자동 실행'이 필수라면 Work 등 공식 지속 호스트의 실제 12문맥 P0-R 시험이 기술적 선결 조건이다. 사용자 선호를 우회한 임의 브라우저 자동화, 비공식 Chat API, 외부 모델 API 사용 금지.
