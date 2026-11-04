# V5 #1 — 2026년 공식금융규정·숫자전사 29건 후속 검증 (2026-11-04)

**결론: 29/29 근거·출처별 재검토, 금융 사실 독립 승인 0, 기존 잔여 92건 OPEN 유지, 개인투자 자문 NO-GO.**

## 실제 수행 및 정량 결과
- 기존 4단계 비공개 봉인 원장을 로컬에서 복원한 뒤, 공식규정 적용성 이슈 **E 21건**과 숫자·ASR 이슈 **N 8건**을 직접 재검토.
- E 21건: 2026년 공식기관 공개 규칙 **일반 적용범위 확인·개인별 적용 미확정 15건**, 자료만으로 전체 주장 검증 불충분 **3건**, ISA 2024년 지침의 2026년 현행성 추가확인 **3건**.
- N 8건: 숫자 전사 오류 가능성을 원본 인접 문맥에서 대조했으나 독립 원음/공개 자막 동일 시점 확보 없음. 원음 없이 숫자를 추측하여 수정하지 않았음. **8건 전부 AUDIO_REQUIRED**.
- 기존 4개 체인과 #1 original SRT SHA256 `2de4b318c75c96421f446a462ecaeacef2a931fbda5bd4c7b35236dcb3fe9a0f` 변경 없이 **제5 체인** 추가. 새 제5 체인 `c755e031631a14393c1ec21ee3be614f2072d18f974a9337400bc9a995b6a92d`.
- 증거는 **ChatGPT 웹도구에 표시된 공식기관 페이지의 일부분**으로, 서버 수신 원본 HTTP bytes/원문 서명/독립 세무사의 적용판정은 아님. 기존 금융 사실 독립승인 0, 상담 승인 0. OPEN 수를 임의로 줄이지 않음.

## 재검증한 핵심 공개 근거
1. [국민연금 추납](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0047M0.do): 최대 119개월·신청 자격 유지 등 조건; 개인별 증가예상연금은 미승인.
2. [국민연금 연기연금](https://www.nps.or.kr/pnsinfo/ntpsklg/getOHAF0100M0.do): 월 0.6%·5년 36% 가산, 복리 투자수익과 다름.
3. [국세청 사적연금](https://nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7889&mi=6609): 연 1,500만원 초과 해당 사적연금소득의 국세 15% 분리과세 선택; 전체 인출액 보편 상한·일률과세 아님.
4. [2026-10-01 시행 소득세법 시행령 제40조의3](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1029964673): 과세제외금액→이연퇴직소득→기타 재원 순서의 연금계좌 인출 간주규칙.
5. [국세청 2026 연금 과세원천](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7888&mi=6435): 이연퇴직소득과 운용수익·세액공제납입 구별, 2026년 이후 실제 연금수령연차별 세율 적용 변화.
6. [국세청 ISA 만기 전환](https://d.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875&mi=6439): 전환액 10%, 300만원의 추가 세액공제 한도 일반 안내.
7. [KRX ETF 과세](https://regulation.krx.co.kr/contents/RGL/03/03060105/RGL03060105.jsp): 국내주식형 ETF와 기타 ETF 일반계좌 과세 차이, 상품 분류·연금계좌 인출세제 별도.
8. [금융투자협회 투자중개형 ISA](https://law.kofia.or.kr/service/law/detailArticlePrint.do?contentSeq=282404&historySeq=1617&seq=343): 확보 본문은 2024-02-29 개정 지침, 2026년 최신 적용 버전 별도 확인 필요.

## 실제 코드·복구·검사
- 코드: `ire/v5/rule_2026_audit.py`, `ire/v5/rule_2026_backup.py`, `ire/v5/tests/test_rule_2026_recheck.py`.
- 비공개 5단계 암호화 archive SHA256 `5fff4d0c93a4868be70ef077c77f4db584a79d52b138cce75fe59ca74b731f0e`, 154781바이트.
- 비공개 Google Drive 저장→다운로드→SHA256 동일→완전히 다른 로컬 경로에서 **원래 네 원장+신규 제5 원장 전체 재생 PASS**. 잘못된 비밀번호·변조파일은 모두 거부.
- Drive: https://drive.google.com/file/d/1lNR06GX_OwMRPFpeI87MA-6QRsf-r6fg/view?usp=drivesdk (복구 암호 별도 비공개, GitHub나 Drive에 올리지 않음).
- 관련 공개 GitHub 작업 상태: `ire/v5_app/focused_states/v5-video-001-focused-64.json` (64 위험·잔여 92·NO-GO).
- 개발 브랜치와 draft PR #13만 수정. `main`·V3·V4 승인 자료·비공개 SRT를 수정/공개하지 않음.

**후속 우선순위:** 음성/독립전사 없는 8개 수치문장은 본문 교정 금지. 2026년 ISA 지침 현행 버전·법령 시행일·개인별 실무 적격성 검증. 최종 투자 자문용 승인은 여전히 NO-GO.
