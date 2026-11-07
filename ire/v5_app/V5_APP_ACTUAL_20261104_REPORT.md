# V5 GitHub 앱 + ChatGPT 연구 엔진 실제 연결 검증 (2026-11-04)

**판정:** APPLICATION CONTROL PLANE PASS / PRIVATE CHAT RESEARCH LOOP PASS (W00004) / FULL P0 NO-GO.

## 핵심 구현
- `ire/v5_app/worker.py`: GitHub Actions가 GitHub의 새 numbered request를 읽어 안전한 공개 상태(작업 번호, 진행 개수, 다음 해야 할 일)를 계산하여 커밋한다.
- `ire/v5_app/server.py`: 127.0.0.1 private V5 연구 앱 API. `/v1/next`에서 실제 원본 인용 자막을 요구하고 `/v1/receipt`은 예상 task SHA와 이전 이벤트 해시 일치 시에만 답변을 받는다.
- `.github/workflows/ire-v5-app-control.yml`: request push → 실제 단위시험 → worker 실행 → GitHub Actions bot 상태 커밋. 영구 상주 프로세스가 아니라 GitHub event-triggered runner다.
- 원본과 개인 자료, 비공개 금융 주장, 복구 비밀번호를 public repository에 넣지 않는다.

## GitHub app 실제 작동 증거
1. 공개 작업 `ire/v5_app/requests/v5-video-001-research/000001.json` 등록: source `sz5N9WJS310`, 1195 cues, adaptive 81 windows.
2. 실제 보존된 private V5 3/81 체크포인트의 SHA·영수증을 `000002.json`으로 접수.
3. **GitHub Actions bot 자동 커밋 `b138fb4339e0202e8340b7a3267160b40bf2642f`**, 상태는 다음 문맥 `W00004`라고 계산.
4. 별도 private V5 엔진 복원 → ChatGPT 현재 대화에서 **W00004 자막 35~48번 직접 읽기·4개 금융 명제 분해** → 국민연금공단 추납 신청한도 119개월/가입자격 제한 공식 출처 검색 → 기존 #1 분석 claim `sz5N9WJS310-01` 버전과 관계 보류 → 로컬 V5 API에 1개 의미 결과, 4개 증거 검토, 4개 기존 지식 관계 사건 접수.
5. 신규 private V5 총 **4/81 문맥, 9 provisional claims, 9 evidence reviews, 9 relation reviews, 22 immutable events**, 77개 문맥 미처리, 다음 `W00005`.
6. 새로운 원본+영수증 AES-GCM 암호화 백업을 개인 Google Drive에 업로드: `https://drive.google.com/file/d/1xIXSMDHmUI42JIbdrysTy3IKbEyQvUBA/view?usp=drivesdk`. **별도 다운로드 후 SHA-256 `0655d3254d99910dd2dc2bf71fd4f258477d67f6a05482cb8c886e708eea2aa3` 일치**, V5 독립 저장소 복원/22건 이벤트 재실행 성공.
7. 공개 작업 `000003.json`에 검증 완료된 private 암호화 백업 해시 및 이벤트 체인 해시 `180c633876f0c7e2887e0126e7064a76298e5a0d9bb706116ddf1c4ac08d177c`를 접수.
8. **GitHub Actions bot 자동 커밋 `427a606d7b386db0da016d50d0ba0bb7fcd22a26`**, repository 상태 파일 `ire/v5_app/states/v5-video-001-research.json`은 **4/81, 다음 W00005**를 반환한다.
9. 로컬 앱 테스트 **18/18 PASS**. V5 핵심 테스트 35건 중 **32 PASS, 3 SKIP**. GitHub 클린룸 보호 검사는 수동 개발 커밋 기준 성공하였으나, 일부 봇 PR 이벤트에는 `action_required`가 표시되므로 모든 CI가 통과했다는 주장을 하지 않는다.

## 판정의 경계
- **실제로 작동**: (A) GitHub push-triggered 애플리케이션 task/state loop, (B) ChatGPT 실제 원본 해석 및 공식 검색/사례 분리, (C) private local API의 source/event CAS와 안전한 인수, (D) private cloud encrypted backup→readback→replay.
- **아직 입증 안 됨**: (A) GitHub 자체 24/7 resident server; GitHub Actions는 단기 job (B) ChatGPT가 종료된 상태에서 GitHub가 독자적으로 AI 의미 분석을 호출하는 기능 (추가 LLM API 금지), (C) 81/81 원본 완주, (D) 외부 심사자가 승인한 금융 사실, (E) 개인 투자 자문 승인.
- 특히 공개 GitHub status의 progress는 **ChatGPT가 비공개 실험으로 재검사한 결과를 보고한 메타데이터**다. GitHub Actions에 원본과 복구키가 없으므로 공개 상태 자체가 비공개 금융 사실을 독립적으로 검증했다는 뜻은 아니다.

## 실제 운영 모델
GitHub repo = 버전관리된 연구 앱 / GitHub Actions = push 시 임시 실행되는 안전한 task runner / local host 또는 사용자 승인된 클라우드 컴퓨터 = source-only private V5 REST engine / ChatGPT = 모델 의미 분석+공식 web search+기존 지식 비교 / Google Drive = 유출 방지 암호화 영속 저장. 상주 서비스가 정말 필요하다면 사용자 소유 상시 서버 또는 self-hosted runner 등 **별도 실행 호스트**가 반드시 필요하다.

**다음 실제 연구 작업: W00005. GO 승인 금지. main 불변.**
