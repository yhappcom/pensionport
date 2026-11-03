# V5 #1 전체 원본 범위 실연구 검증 — 2026-11-04

**단계:** ORIGINAL_SOURCE_SCOPE_SEALED / OFFICIAL_FACT_AUDIT_OPEN / INVESTMENT_ADVICE_NO_GO

## 실제 수행
- 연구 원본: #1 `sz5N9WJS310`, 원본 SRT 1195 cues, 원본 SHA256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f`.
- 전체 V5 계획: **67/67 문맥 원본 범위 접수** (3 이전 승인 전 접수 문맥 + 현재 채팅에서 실제 원문 64개 문맥 직접 읽음). 이전 V5 81문맥 계획과 서로 다른 source plan이므로 이 둘의 진행률을 합산하지 않음.
- **81개 잠정 주장** (이전 4개+이번 77개), **81개 증거 조사 판정**, **81개 기존 지식 관계 심사**. 기존 #1 연구원장 23개 주장에 대하여 후보 연결 완료. 기존 연구를 자동 수정·승인하지 않음.
- V5 BATCH_ACCEPT 해시 체인 이벤트 **11건**, 최종 헤드 `d05ef6c38c9bda57e00bf10997cbb8c1cc93b0cf3f5f50fa75d0f825b8a80660`. V5 report sealed = **원본 범위 분석 기록이 폐쇄됨**, 금융 사실의 독립 진실 승인 아님.
- **공식 금융 사실 승인 0건, 자문 승인 0건.** 모든 증거 판정은 적용성 검토 및 OPEN 항목으로 남음. 현재 source manifest에는 `STRICT_P0C_V1`이 지정되지 않았으므로 해시 고정 공식 원문·독립 시행일 판정 조건을 실제로 통과했다고 주장할 수 없음.

## 검토 및 정정 후보 (검증원문 사본·현행규칙 적용성은 재심사)
- 국민연금 추납 구독자 월 25만원 증가 예상액은 개인 이력 없이는 일반화 불가. 국민연금공단의 최대 추납 가능기간 119개월과 구별.
- 국민연금 연기연금 공식 설명은 월 0.6%, 5년 최대 36% 가산; 투자수익률의 복리 36%가 아님.
- 월 30만원·연 실효 7%·월말 적립 가정의 7년 후 약 3,214만원, 10년 후 약 5,132만원. 영상의 '7년 후 약 5,100만원'은 기간 혼동.
- 사적연금 연 1,500만원은 과세방식 판정 기준이지 보편적인 법률상 인출 금액 상한이 아니다. 세액공제 미수령 원금의 과세제외성, 인출순서는 법령·계좌장부 대조 필요.
- 8억원 × 연 6% / 12 = 월 400만원은 가정상 세전 분배 산술이며 지속적 세후 비과세 현금흐름 보장 아님.
- 국내주식형 ETF 일반계좌 매매차익과 연금계좌 인출과세는 별개. ISA 계좌 손실 무기한 자동 세액상계는 승인하지 않음.
- 공식 원문 후보: `nps.or.kr` (연금 추납/연기), `nts.go.kr` (사적연금), `law.go.kr` (소득세법 시행령 인출순서), `regulation.krx.co.kr` (ETF), `law.kofia.or.kr` (ISA). **이는 금융 기관이 원장을 독립적으로 확인했다는 의미가 아님.**

## 독립 품질 위험 — GO 차단 조건
1. 67 source windows 중 강제 문장분리 위험 **48개**. 인접 문맥은 검토했지만 미노출 blind 재현율 시험은 수행하지 않음.
2. 신규 source 문맥에서 독립 원자주장으로 인용되지 않은 원본 자막 **732개**; 그 중 숫자가 등장하는 **99개**는 다른 인용을 완성하는 문장·대화인지 혹은 독립 금융조건 누락인지 재판정 필요. 숫자 포함만으로 누락이 확정되는 것은 아님. ASR 오류/미확인 개인예시 존재.
3. 사례별 제도 적용일·개인 가입이력·원문 네트워크 출처 인증 및 독립 금융 심사자 승인은 미완료.
4. GitHub Actions에 비공개 SRT·원장·키를 두지 않았으므로 GitHub의 완료 카운터만으로 진위를 승인할 수 없음.
5. 무외부모델API 채팅의 장시간 4~5편 연속 완주는 아직 미입증.

## 저장·운영 검증
- 최신 암호화 원본/영수증 백업 SHA256 `de2f5ec71d0c375094be0010cb1b01946be118d89e2fe22b7d0cf553790611ca`, 88,968 bytes.
- 개인 Google Drive 업로드→인증된 재다운로드→바이트 동일 SHA→별도 실행 저장소 AES-GCM 복호화→V5 해시 체인 11개 재생 **PASS**.
- [비공개 암호화 백업](https://drive.google.com/file/d/1GyrpilULElZcobOHe8MkePu2gQ7yHuz8/view?usp=drivesdk) — 복구 비밀번호는 별도 로컬 비공개 보관, GitHub/Drive에 올리지 않음.
- 로컬 V5 코어 시험: **53회 실행, 50 PASS, 3 기존 private-only fixture SKIP**; 앱 시험 **26 PASS**.
- 기존 GitHub 단일 작업 관리자가 묶음 영수증에 대해 `events>=windows`를 요구하던 결함 수정 후 67문맥/11영수증 보고 정상 접수. 별도 앱 작업 `v5-video-001-full67-20261104`, [Actions 봇 생성 상태](https://github.com/yhappcom/pensionport/blob/feat/ire-v5-vertical-slice-20261103/ire/v5_app/states/v5-video-001-full67-20261104.json): `remaining_windows_reported=0`, `PRIVATE_REPLAY_AND_RESEARCH_CLOSURE_AUDIT_REQUIRED`, `full_video_completed_and_verified=false`, `financial_advice_approved=false`.
- PR-triggered GitHub 클린룸 CI run `41681521580` conclusion **success** on human update `b808fc6...`. Subsequent `github-actions[bot]` status-only commit PR workflow reports `action_required`, which is not a reason to declare new financial research verified.
- Original `main`, historical V3/V4 records unchanged; PR #13 draft/unmerged.

**최종 판정:** 사용자 한 턴에 #1 원본 전수 67문맥을 기록하고 재생하는 기술 경로는 성공했으나, 미노출 검증·공식 근거 독립승인·99개 숫자 비주장 재심사 없이 **정식 투자자문 지식 L3/L4 출시 승인 금지**. 다음에는 기존 기록을 재분석하지 않고 48 강제 경계/99 숫자 비주장/공식 원문 적용일 심사를 대상으로 추가 검증해야 함.
