# 박곰희TV #94 RIA — 이벤트 조건 제외, 제도 검증만 계속 (2026-10-15)

[영상](https://www.youtube.com/watch?v=xIygVI-t04A) · 녹화 2026-04-15 · 게시 2026-04-24 · 24:45 · 영상 ID `xIygVI-t04A`

> **원본 688큐 SRT 파일 및 공개 전사 전문 미확보 — `SOURCE_BLOCKED/NOT_APPROVED`.** 이번에 확인한 RIA 제도 12건은 *영상에서 강사가 실제 한 말의 검증 12건이 아니라* 금융사 제도 자료의 독립 검증이다. 원본 SRT 해시 `c2add25713c355c1dcfa84af1aeba57f14e2c7736d521ebd7aa5e378a527d1e4`는 과거 등록값이며 이번 바이트 재계산은 없었다. 영상 대사의 시각·문장·원음 검증 0건. **사용자 요청에 따라 10개 증권사의 이벤트 혜택·참여조건·기간 비교는 검증 목적에서 제외**했고 추가 확인하지 않는다. 과거 행사 조사기록은 데이터에서 출처 추적용으로만 별도 보존했다.

## 계속 연구할 실질 제도 내용

1. **RIA ≠ ISA.** RIA(국내시장복귀계좌)는 해외 상장주식/적격 해외자산의 기존 보유분을 국내시장 복귀시키며 양도세 혜택을 주는 별도 계좌이다. 2025-12-23에 보유했던 적격 해외주식의 수량 한도와 실제 증권사 이체 가능 여부가 중요하다. 다른 계좌에서 매도한 원화만 이체하면 동일한 혜택을 인정받는 구조가 아니다.
2. **개인 총한도 5,000만원.** 여러 증권사별 계좌를 만들더라도 전체 증권사 합산 적격 RIA 매도대금 5천만원이 한도다. 주식보유평가액·개별 RIA 한도를 무한히 합산할 수 없다.
3. **결제시점별 공제율.** 2026년 5월 말 이전 해당 해외주식 매도 **결제일** 100%, 6~7월 80%, 8~12월 50% 공제율. **공제율은 양도차익의 대상 소득공제율**이고, 계좌의 현금총액을 지급받거나 납부세금 전액을 무조건 돌려받는 보조금이 아니다. 2026년 10월 현재 100%·80% 시한은 종료됐다.
4. **최종 결제 이후 1년간 국내 재투자·유지.** 해당 RIA 내 원화예탁금, 적격 국내주식, 적격 국내주식형 ETF/펀드 등에 묶어 유지. RIA 원금 중도 인출은 혜택 무효 위험이 있고 투자이익·일부 인정된 특별사유와 구별한다. 국내상장이라고 해서 미국주식 ETF나 채권·RP 상품이 모두 RIA 적격이라는 것은 아니다.
5. **다른 계좌의 순매수와 상호작용.** 2026년에 ISA/연금저축/IRP/DC·일반위탁 등 RIA 바깥의 해외주식·해외주식형 국내 ETF/ETN·펀드를 *가중 순매수*하면 RIA 공제액이 줄어들 수 있다. 다만 매수와 매도 **순액·시점·대상자산**을 조문대로 계산해야 하며 모든 매수 1원마다 RIA 공제가 1원 자동 삭감된다고 단순화하면 안 된다.
6. **실제 절세효과.** 해외주식 간 양도손익통산, 과세연도 해외주식 기본공제(일반적으로 250만원), 해외주식 양도세율, 이미 사용한 RIA 적격매도 대금, 국내투자 운용손실, 환전비용 등을 함께 계산해야 한다. 절세제도는 **국내 주식 수익률이나 원금보장과 무관**하다.

**원자료:** [한국투자증권 RIA 제도공지](https://securities.koreainvestment.com/main/customer/notice/Notice.jsp?cmd=TF04ga000002&num=46415) · [미래에셋증권 RIA 상품설명](https://securities.miraeasset.com/hki/hki3032/n51.do) · [정부 RIA 정책소개](https://www.korea.kr/news/policyNewsView.do?newsId=148958323)

## 공식 맥락 검증 13건 — 강사 발언과 별도

| 체크 ID | 검증할 일반 제도/사실 | 근거 수준·적용조건 |
|---|---|---|
| `RIA-LAW-01` | RIA stands for Reshoring Investment Account/국내시장복귀계좌; differs from ISA | Law §91-26 and original March2026 broker instructions; portfolio from proceeds of specified existing foreign stock — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-02` | 2025-12-23 cutoff refers to eligible shares held by end of the date | Min(holdings 2025-12-23, holdings at transfer) matters; purchased only after Dec23 ineligible generally — [참고](https://securities.koreainvestment.com/main/customer/notice/Notice.jsp?cmd=TF04ga000002&num=46415) |
| `RIA-LAW-03` | RIA overseas stock sell proceeds are automatically converted to KRW on settlement | Account cannot accept arbitrary cash deposits; eligible foreign stock must be transferred into RIA then sold — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-04` | 1 person aggregate 50 million KRW RIA foreign stock settlement amount limit across all brokerages | Many accounts allowed at multiple brokers, each one account per broker, but combined sale proceeds limit still 50m. Gross transfer stock market value not itself cap — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-05` | 2026 foreign stock settlement by May31 100% income deduction rate, June-July80%, Aug-Dec50% | The qualifying percentage is based on settlement/automatic FX date, NOT opening date or order date and not a 100% cash tax rebate. Ended 100% band before Oct — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-06` | An RIA must retain 1y from LAST eligible settlement and hold KRW cash/allowed Korean equities or domestic equity funds | If foreign stocks are sold at different dates, last eligible FX funding date controls final date — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-07` | Withdrawing protected principal early (even partial) can invalidate full RIA benefit | Broker's product disclosure distinguishes early protected principal withdrawal from withdrawals of growth exceeding invested principal, and listed legal unavoidable hardship exception — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-08` | RIA allowed domestic products include KRX listed equities/qualified Korean equity ETFs or idle KRW cash | Not all domestic listed ETFs count; domestic-listed US exposure normally is overseas investment substitute and may trigger penalty if held outside RIA — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-09` | Buying foreign stocks and overseas-investing local ETFs in OTHER accounts in 2026 can reduce RIA relief | Penalty net buying in all institutions including ISA/IRP, based on deal settlement and weighted Jan-May100%, Jun-Jul80%, Aug-Dec50% — [참고](https://securities.koreainvestment.com/main/customer/notice/Notice.jsp?cmd=TF04ga000002&num=46415) |
| `RIA-LAW-10` | For 2026 investment tax, RIA relief is calculated after gains netting and a separate 2.5m KRW overseas capital gain standard deduction | Broker illustrates deduction ordering gains-losses, 2.5m KRW, RIA relief, then taxable remainder22% total. Individual actual gain is unverified — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-11` | RIA domestic stocks market losses/FX changes can exceed event rewards and tax savings | Issuer prospectus warns principal loss; foreign assets sale timing / currency FX are actual investment risks, not all investment outcomes profit — [참고](https://securities.miraeasset.com/hki/hki3032/n51.do) |
| `RIA-LAW-12` | RIA is not the same as regular ISA and moving ISA balances is not an RIA tax-relief substitute | RIA targets foreign-stock disposal tax with unique cutoff, timing and 1y lock; ISA imposes different taxable-income settlement — [참고](https://securities.koreainvestment.com/main/customer/notice/Notice.jsp?cmd=TF04ga000002&num=46415) |
| `RIA-SOURCE-01` | The YouTube video description confirms 10 brokers, chapter divisions and recording date Apr15, but full transcript was NOT accessible | YouTube page has chapter starts for 10 brokerage firms. Firecrawl full content API returned only description; translated YouTube player error and WithTranscript show No Transcript; source file 688 cues from prior chat not mounted — [참고](https://www.youtube.com/watch?v=xIygVI-t04A) |

## 실제 남은 검증

**남음:** #94 한국어 원본 `xIygVI-t04A.srt` 688큐·53,780바이트 검색/복구, 등록 SHA256 바이트 일치 확인, 전사 전문·정확 화자 문구(음성) 및 업로더 챕터 시점 대조, 영상의 계좌·세금 제도 설명에 해당하는 발언만 주장화. 필요한 경우 같은 채널 [#97 RIA 사용설명서](https://www.youtube.com/watch?v=vnPVjbRtZk4)의 공개 한국어 전사를 *주제 맥락*으로 참조할 수 있지만 **#97 자막을 #94 화자의 실제 말처럼 옮기는 것은 금지**한다.

**제외:** 증권사별 1만원/경품/최소입고액/환전우대 등 **행사 혜택·조건의 추가검증 일체**. 관련 원본 기록은 [2026-10-14 과거 조사 아카이브](VIDEO94_RIA_BROKERAGE_EVENT_SOURCE_BLOCKED_20261014.md)에만 남긴다.

**결론:** 제도 자체의 핵심 이해는 확인. #94 영상 자막 전수분석이 아니므로 `video_claim_count=0`, `NOT_APPROVED`를 유지한다. 완료된 잠정 16편·411개 주장에 산입하지 않으며 `main` 수정 금지.
