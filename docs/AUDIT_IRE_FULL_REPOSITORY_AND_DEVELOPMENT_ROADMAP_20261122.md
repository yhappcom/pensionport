# 투자 연구 엔진 IRE 전 저장소 감사 및 개발 재정렬 보고서

**기준:** 2026-11-22 (KST)  
**저장소:** `yhappcom/pensionport`  
**개발 기준:** `verify/ire-v6-e1-v230-v228-source-native-handoff-20261121` @ `b6aae4a75832d2c467be262cfac79e1ae7522890`  
**비교 기준:** `main` @ `d613fd201f4bb077f1ccc74d28dee937b11bfcb2`  
**감사 스냅샷:** `audit/full-repository-snapshot-20261122` @ `1b2b64377ca97b35e40f260fdb79ce410e754b16` (감사 전용 워크플로 1개만 추가)  
**판정 원칙:** GitHub CI 합격, 실제 코드 실행, 실제 금융 의미 정확도, E3 검토, E4 승인, E5 지식 발행, 자문 적격성을 별개의 증거로 판정한다.

## I. 경영 요약

프로젝트의 목적은 791개 영상의 요약 보고서 생산이 아니라, **실제 SRT에서 투자 관련 주장을 추출하고 현행 금융 근거와 대조하며, 누적 지식과 의미 관계를 판정한 다음 ChatGPT 최종 검토 및 적법한 승인 절차를 거쳐 질문·투자 의사결정·향후 개인 포트폴리오 자문에 재사용하는 연구 시스템**이다. 별도 모델 API는 사용하지 않는다. 실제 사용자 메시지 **1턴 연구·동결 / 별도 사용자 메시지 2턴 검증**을 유지한다.

**판정:** V242에서 검증한 ETF 원본 250 cue/68 미승인 원자/13 child의 **소스 및 구조적 V6 호스트 기록**은 실증했다. 마지막 B0013은 부모 조건 45~47을 분리 보존하는 **미승인 잠정 원자 보기**로만 기록되어, 13개가 완전한 의미 원자로 승인된 것은 아니다. V123 정식 최종 승인 0/13, E4 실제 금융근거 승인/봉인 없음, E5 최종 지식 0건, 투자 자문 실제 통합 완료 아님. **전체 E1→E5 최종 GO는 HOLD**.

현재 개발이 반복되는 가장 큰 이유는 새로운 결함 하나가 아니라, **(1) 파편화된 브랜치·정책·실행 진입점, (2) 전체영상↔자식구간 문맥/원자 소유권 계약 불일치, (3) 미승인 의견을 수정·재검증해 다음 합법적인 상태로 전환하는 프로토콜 부재, (4) 실제 2턴 모델 호출은 Python에서 수행할 수 없는 호스트 경계, (5) 공식 E4→E5 긍정 실물 검증과 독립 정확도 근거 부재**가 동시에 존재하기 때문이다. 다음 단계는 새로운 V243 테스트 파일을 추가하는 것이 아니라, 작동하는 V6 커널을 중심으로 **한 개의 정식 운영 파이프라인과 릴리스 기준**을 만드는 일이다.

## II. 범위 및 완전성 증명

1. GitHub의 `main`과 E1 검증 브랜치에 대해 재귀 tree 인벤토리를 수집. GitHub 브랜치의 현재 커밋과 파일 blob SHA를 비교했다.
2. `main`은 **665개 파일 / 1,663,117바이트**, E1 검증 브랜치는 **2,351개 파일 / 21,319,224바이트**. 공통 파일 중 본문 변경은 `README.md` 1개이고 E1 개발 브랜치에 **1,686개 파일 추가**. `main`에만 있는 파일은 없음.
3. GitHub Actions에서 **E1 개발 브랜치를 기준으로 전체 추적 파일 스냅샷**을 생성해 별도 오프라인 감사 폴더에 압축 해제했다. 감사 전용 워크플로 1개가 추가된 스냅샷은 **2,352개 파일 / 21,321,282바이트**. 2,352개 파일 **모두 개별 SHA-256 재계산 일치, 누락 0, 변경 0**. 기계 판독 매니페스트 `_audit_complete_tracked_manifest.json`에는 모든 파일의 경로·바이트·해시가 있다.
4. 원문 접근 가능 유형: **Python 825개 모두 AST 구문 검증**, **JSON 757개 모두 파싱**, **Markdown 693개 모두 UTF-8로 읽고 제목·본문·상태 신호를 인덱싱**, **YAML 26개 파싱**, **JSONL 6개 총 739행 파싱**(211+116+19+230+157+6), **HTML 2개**, **텍스트 1개**. 별도 `.b64` 6개는 base64+zlib 압축임을 확인하고 해제된 JSON의 형태/개인정보 가능성만 안전하게 점검했다.
5. **36개 암호화/바이너리 아카이브**는 바이트·해시·경로를 확인했지만 개인 복호화 키/복호화 원본이 없어 **의미 내용까지 읽었다고 주장하지 않는다**. 최신 비공개 SRT·V241/V242 SQLite 실물의 주요 출처 검증은 기존 비공개 증빙을 별도로 확인한 기록에 의존하며, GitHub 저장소 자체의 추적 파일은 아니다.
6. GitHub 개발 이력: PR **74개** 중 **병합 31 / 열림 42(그중 Draft 41) / 미병합 종료 1**. 별도 열린 Issue #48·#50이 남음. 브랜치 목록의 첫 페이지에 98개 브랜치가 확인됨. 개발 브랜치의 커밋 이력은 2026-09-30~11-21 약 **2,872개**로, 저장소의 반복 실험 규모가 큼. 커밋 숫자는 품질 지표가 아니다.
7. 전체 파일 전수 목록/해시는 동봉한 `_audit_complete_tracked_manifest.json`이 정본이다. **모든 파일을 사람이 의미상 독립 심사했다는 뜻이 아니다.** 정책·실행·CI·승인 경계와 실제 원본 사고 원장에 대해서만 본 보고서가 심층 판정한다.

## III. 저장소 구조와 운영 의미

| 위치 | 실제 파일군 | 운영상 의미·주의 |
|---|---|---|
| 루트·`docs/` | README, 791 로스터, V3 workflow, 의사결정 기준 | 상당수 역사 정책이 최신 V193 2턴 규칙보다 오래됨 |
| `data/` | legacy `videos.jsonl`, `claims.jsonl`, `canonical_events`, `analysis_events`, 큐 | 레거시 등록·후보, E3/E4/E5 신규 승인 지식과 동일시 금지 |
| `knowledge/`, `synthesis/`, `videos/` | 과거 영상별 분석·요약·합성 문서 | 데이터 계보 보존. V6 정답셋으로 자동 재사용 금지 |
| `ire/` V1·V2·V3 | 채팅-결합 오케스트레이터·증거·관계·자문 실험 | 이전 한 턴 워크플로의 역사 코드 |
| `ire/v5/`, `ire/v5_app/` | 거래 커널·1턴 원본 처리·P3/P4 교육 지식·자문 테스트 | 실제 일부 원본 실험 있음. 지속형 자동 금융 자문 완성 아님 |
| `ire/v6/` | source, atomic_exchange, TransactionStore, official candidates, blind arithmetic, 재생 검증 | 견고해진 **결정론적 커널**. 모델의 의미적 정답을 생성하지 않음 |
| `validation/ire-v6-frozen/` | V123/V126/V127/V128, E4 gates, V166~V242 브리지, 244개의 `test_*.py` 포함 | **실질 승인/저장 연결 코드가 검증 폴더에 분산**. 정식 단일 배포 인터페이스 부재 |
| `.github/workflows/` | 원래 25개 워크플로, 감사 브랜치에만 1개 추가 | 현재 E1 PR을 엄격 V5/V6 전체 검증으로 묶는 독립 통합 관문 부족 |

**중요:** 설치/배포용 `pyproject.toml`, `setup.py`, Dockerfile 등 표준 단일 배포 진입점이 현재 추적 파일에 없다. Python 소스가 존재하고 개별 모듈·시험이 통과하는 것과 동일한 환경에서 실행 가능한 운영 제품은 다르다.

## IV. 전체 개발 이력에서 확인된 논리

1. **2026-09~10 초:** 영상 등록부·과거 교육 주장·기본 주제별 지식 구축. 791 고유 영상(703 롱폼·88 Shorts)의 로스터. 초기 '등록/분석'은 현행 금융 지식 E4 인증과 구분해야 함.
2. **10월 말 V2/V3/V4:** 단일 영상 파일 기록 중심을 벗어나 원본 전체 cue·조건/숫자·공식 근거·신구 지식 관계·질문 자문으로 전환. 그러나 한 턴 반복 실행과 실제 ChatGPT 호출을 Python이 자동으로 할 수 없다는 근본 한계가 드러남.
3. **11월 초 V5:** 원본 SRT 기반 거래/중단 재개·근거/관계·P3/P4 교육용 자문 경로 시연. 일부 원본 창에서 실험했으나 전체 #1~#5/700편의 정확도, 공식 금융 승인, 한 턴 무인 완주는 미검증. 원장/영수증에서 거짓 PASS를 차단하는 개선이 반복됨.
4. **11월 8일 이후 V6:** V5의 인메모리/JSON 트랜잭션 부작용을 해결하려고 ACID SQLite, 단일 writer, revision/HEAD, 재개봉 해시, source/owner attest, 기존 116·P4 후보·법령 후보·gold arithmetic를 분리. **V6 기본 설계는 의미 모델이 아니라 검증·저장 커널**.
5. **V123/V127/V128:** ChatGPT 최종 의미 검토, 13 child 부모 체크포인트, 모든 자식 승인 시 원자적 부모 발행 경로를 연결. 일부 합성 입력에서 저장 성공, 실물 원본에서 공식 금융 검증·정식 최종 PASS는 부재.
6. **V166:** E1~E7 순차 정책으로 소스·채팅·승인·저장·자문 경계를 독립 검증. E1/E2/E3의 과거 제한된 PASS 표기와 E4 실제 HOLD/FAIL을 구분해야 함.
7. **V167~V193:** 실제 금융근거·화자·반박·조건·인용의 교착을 확인하고, 실제 사용자 **서로 다른 메시지 두 개: 1턴 동결 → 2턴 최종 검증**을 상위 운영 계약으로 고정. V179의 1~125+126~250 연속 분석은 2턴 최종 검증 증명이 아님.
8. **V202~V203:** E1 이전 합격 판정 독립 재검문으로 부족한 경로를 발견, 합성 V176→V6→V123/V127/V128/V126 유효 입력의 실제 저장 및 차단 성공. **합성 E1 구조만 PASS**.
9. **V228~V242:** 실제 ETF 250 cue/68 후보에서 2턴 내부 검토 영수증과 비공개 원본 해시를 연결. V232 전체 영상 V6 호스트 30 이벤트, V233 V127 13-child 계획, V234/235 외부 문맥 21원자/49 edge 및 HOLD, V236 원인 규명, V237~V239 13 child 검토 입력, V240 E4 sealed 전용 게이트, V241 자식 12개 72 이벤트, V242 B0013 부모 조건 잠정 표현 6 이벤트 → **총 13개 구조 호스트 78 이벤트**. E3 최종 0/13, E5 발행 0.

## V. 실물 검증 현황

**대표 영상** `LVE7XN_esTc`: 250 SRT cues, V228 원자 후보 68개, 13 child, 21개 cross-scope 원자/49개 외부 cue edge. V231 2턴 내부 원자 의견: **48개 수정 필요 + 20개 HOLD**. 68개 원자 stance는 현재 원본에서 전부 `UNRESOLVED`로 남아 있다. 47개는 child-local 구조 후보, 나머지 21개는 부모 외부 문맥을 요구한다. 178개 의심/미해결 원문 자막은 별도 출처 기반 격리 원장으로 추적.

| 검증 경로 | 지금 확인된 것 | 승인 여부 |
|---|---|---|
| 원본 SRT→V6 전체영상 | 250 cues/68 atoms, SQLite 30 이벤트, 해시·재개봉 확인 | 구조 PASS, E2/E3 미승인 |
| 전체영상→V127 부모 | 13 child manifest 및 안전 재개봉 | 계획 PASS, 실제 13개 자식 최종 승인 0 |
| 외부 문맥 | 21 원자·49 인용/조건/숫자 edge 원본 SHA 추적 | 보존 PASS, 의미 미확정 |
| V241/V242 자식 native V6 | 12개 정상 child-local 호스트 + B0013 미승인 부모-조건 부분 보기, 78 이벤트 | **구조 기록 PASS, 전체 의미 보존된 승인 원자 13/13 PASS 아님** |
| V123/E3 | 형식과 hash 차단, 실제 검토 미제출 HOLD | 0/13 승인 |
| E4 guarded/sealed | sealed store 전용 경로, 부적합 입력 차단 | 공식 금융실물 양성 미검증 |
| E5 knowledge | 13 child 최종 전체 승인 시 한 부모 발행 설계 및 합성 회귀 | 실제 ETF 0건 |
| 자문 | V5/6 기존 소스·지식 조회 교육용 시연 | 실제 승인 지식 기반 개인 자문 GO 아님 |

**B0013 구체적 사실:** C00057 원문 244~247은 부모 cue 45~47의 '인덱스 ETF에 적용되는 6개 기준' 제한을 참조한다. frozen child input은 외부 cue를 직접 받아들이지 않으므로 V241은 원자 0개 오류. V242는 원본 C00057 전체/45~47을 sidecar에 SHA 고정하고, B0013 로컬 244~247 부분 보기를 `UNRESOLVED`로 V6 구조 호스트에 기록. **이것은 의미 완결된 C00057로 승인한 것이 아니다**.

## VI. 식별된 결함의 근본 원인과 현재 상태

| 결함 ID | 실제 근본 원인 | 현행 수선·잔존 위험 | 판정 |
|---|---|---|---|
| R01 | 합성 구조시험과 실물 금융 의미 검증의 판정 혼동 | V203+ 보고서에서 구분; `README`/status JSON은 시점에 따라 다른 PASS | **부분 해결** — 단일 현재 상태 부재 |
| R02 | 원본/검토 증빙 신뢰 경계 부족 | source SHA·cues·사본 변조 차단 구현 | **부분 해결** — 소유자 서명/원본 음성 검증 아님 |
| R03 | V5 in-memory·다중 파일 거래 오류·재시작 실패 | V6 SQLite ACID/HEAD/idempotence·체인 검증 | **시험 범위 PASS** — 운영 환경 성능/복구 미측정 |
| R04 | 전체 영상 atom에 child 바깥 조건·예외·숫자 포함 | V234/237 부모 sidecar 무손실·검토 입력 전달 | **입력 보존 PASS**, E2 원자화 미완료 |
| R05 | 전체영상 1개 V6 scope와 13개 자식 formal host packet 계약 불일치 | V238/241/242 개별 구조 호스트 기록 | **구조 PASS**, B0013 잠정/나머지 20개 cross 미확정 |
| R06 | `cross_count>0`이면 어떤 의미 검토도 실행 못하는 운영 교착 | V237~V239에서 검토 준비 가능 | **일부 해결**; V240은 여전히 V238의 미해결 21개를 즉시 HOLD |
| R07 | 기존 2턴 검토 note는 V123의 최종 `chat_review` schema가 아님 | V239에 미승인 의견 라우팅 | **미완료** — 정정 overlay→정식 child case 빌더 부재 |
| R08 | 별도 채팅 턴에 대한 신뢰할 호스트 메시지 서명 없음 | V193 수동 영수증은 `host_verified=false` | **플랫폼 한계** — 암호학 인증 주장 불가 |
| R09 | V235 일반 V126 경로가 E4 primary/sealed 관문 생략 | V240 별도 E4 전용 경로 구현 | **부분 해결** — 연구 후보 긍정 E4→E5 통합 실제 시험 부족 |
| R10 | E4 용어의 `승인`과 금융사실/자문 신뢰 등급 혼동 | 결과에 `financial_fact_formally_approved=false`, `p0_go=false` 명시 | **정책 보호 PASS**, 릴리스 등급 분리 필요 |
| R11 | source-only/원자 후보/legacy116을 독립 gold와 혼동 | prior relation OPEN, 별도 V123 review, 위험 격리 | **정량 정확도 미측정** |
| R12 | 2,351파일·다수 Draft PR, 버전별 상충 문서와 복제 실행 진입점 | 최신 보고서의 HOLD 보존 | **미해결** — 단일 버전 관리/정식 패키지·CI 필요 |
| R13 | 공개 repo와 비공개 원본 지속 보관·복원 체계의 부재 | owner SRT/SQLite는 로컬 비공개 ZIP; Git에는 해시 | **미해결** — 지속가능한 비공개 원본 보관 필요 |
| R14 | 유효 법령의 현행 시점·관할·조건·본문 인증 및 독립 평가 부족 | E4 official bytes 검사 일부 구현 | **미완료** — 실제 정확도·공식 본문 재조회 필요 |
| R15 | 791편 확장 전 처리량/재현성/자문 품질 측정 미완료 | 좁은 실물 1편, 합성 테스트 증가 | **미완료** — 독립 신규 다편 벤치마크 필요 |

### 가장 위험한 두 가지 구체적인 운영 결함

1. **원자 정정 결과의 실제 승인 상태 전이 없음:** V238의 `cross_atoms_waiting_for_semantics=21`과 V240의 `if native['cross_atoms_waiting_for_semantics']: HOLD`는 현재 동결 자료에서 계산된다. 모델이 이후 21개를 검토했다는 별도 의견만 붙여도 이 값이 자동 변경되지 않는다. **검증된 정정 overlay를 새 canonical 원자/자식 source/host packet으로 컴파일하고, 그 정정본의 자체 버전·hash/승인 상태를 재검증하는 경로**가 필수다. 원본 sidecar의 ref를 삭제하여 0으로 만드는 것은 금지.
2. **릴리스의 강제 경로가 단일하지 않음:** V235의 옛 일반 V126/V128 경로와 V240의 E4 sealed 경로가 별도다. `E4SealedKnowledgeStore`가 research candidate parent를 발행할 때도 최종 소유자 외부 신뢰 pin을 별도로 고정·확인해야 하며, 이것은 개인 자문 승인과 다르다. 기존 `v173_e4_only_parent`는 `e5_authorized=false`가 정상. **하위 모듈을 공개 승인 API에서 직접 호출하지 못하게 정식 E1→E5 관문을 한 개로 제한**해야 한다.

## VII. 정확성·검증·테스트 해석

- 전 파일에서 Python 825개 AST 구문 오류 0, JSON 757개 파싱 오류 0, Markdown 상대 파일 링크 128개 중 깨진 링크 0. 이는 정적 상태 검사다.
- 2026-11-22 오프라인 Python 3.13.5 환경에서 선택된 테스트: 기본 IRE **310 PASS**, V5 앱 **59 PASS**, V6 core **647 PASS**, E1 V203~V242 **187 PASS**; **합계 1,203 PASS**. V5 전체 core의 장시간 로컬 실행은 해당 감사 실행에서 완료하지 못했고, 현지 Python 3.13.5는 GitHub 고정 CPython 3.11.18과 다르다.
- 현재 GitHub [PR #76 E1 187건 CI](https://github.com/yhappcom/pensionport/actions/runs/44957548898)는 PASS. **그러나 기존 V6 전체 엄격 CI는 현재 E1 브랜치를 대상으로 자동 실행하지 않는다.** 현재 E1 브랜치 전용 워크플로의 187개 회귀 통과를 5,000여 개 전체 테스트 전수 합격이나 실제 금융 의미 골드셋 PASS로 확장하지 않는다.
- 코드 AST에는 약 415개 테스트 파일, 5,411개 `test*` 함수가 보이지만 전부 동일 환경/커밋에서 PASS했다는 증빙은 없다. 양성 E4/E5, 부정 격리, 성능, 오디오 정합성, 복구 후 상태 변조 시험을 분리해야 한다.
- 연구 정확도 목표는 과거 E1~E7 문서에 명시된 **정밀도 95% 이상, 재현율 98% 이상, 고위험 누락 0**. 원본 250개 ETF에 대해 독립 사전 고정 gold와 실제 TP/FP/FN이 없으므로 **미측정**. 같은 ChatGPT가 작성·평가한 참조셋은 별도 인간 독립성으로 인증하지 않는다.

## VIII. 레거시 연구 자산과 로스터의 정확한 해석

- 확정 로스터는 2026-10-07 기준 **791 영상 / 롱폼 703 / Shorts 88**. 로스터 등록은 SRT 확보나 의미 연구 완료가 아니다. roster의 게시일 미확인 155건도 있다.
- 레거시 `data/videos.jsonl` **157건**, `data/claims.jsonl` **116건**(`core` 9 / `supported` 107), `data/learning_queue.jsonl` **211건**, `data/canonical_events/*.json` **168건**, `data/analysis_events/*.json` **74건**. 이 숫자의 서로 다른 분모를 합산해 “분석 완료 편수”라고 제시하면 안 된다. 출처 수준/편집상태/독립성 재판정 필요.
- V5 P4 교육 지식 **22+7=29** 별도 과거 노드와 master116은 V6 기존 지식 **145개 관계 조회 후보**. 레거시 `core/supported`는 현재 ETF에서 E4 승인 지식 145개가 검증됐다는 증거가 아니다.
- `state/progress.json`은 2026-10-08 역사 스냅샷이며 현재 운영 완료 수의 단일 진실값이 아니다.
- 오래된 원본이나 현재 791편의 SRT 전문은 공개 추적 repo에 없다. 비공개 출처 보존이 끊기면 현재 SHA·요약만으로 실제 분석을 재현할 수 없다.

## IX. 보안·저작권·운영 위험

1. GitHub 저장소는 공개 repo이다. 원본 SRT, 상세 의미판정, 개인 포트폴리오, 키, 로컬 SQLite·WAL은 절대 공개 커밋하지 않는다. 비공개 **별도 접근제어/암호화/백업 영역**에 원본·2턴 영수증을 보관하며 정책에 맞게 회수 가능해야 한다.
2. 검증 폴더가 아닌 `ire/v5/validation/private_source_derived_20261107/`에 `.json.zlib.b64` 6개가 이미 공개 Git에 존재한다. 이들은 **암호화가 아니라 base64+zlib 복호화 가능한 JSON**이다. 후보 주장 `proposition_ko`, 소스 SHA, 메타데이터 등이 포함되므로 원본 전문이 없다는 기존 플래그만 믿지 말고 **공개 적합성·저작권·민감성**을 다시 판정해야 한다. 확인 없이 파일을 단순 지우는 것으로 Git 히스토리 노출이 사라지지 않는다.
3. 36개 `.ppc1`/`.v5enc`/`.v5archive` 등은 바이트 검문했지만 암호화 원문 내용은 미검증. 복원키의 존재·안전성을 확인할 때까지 승인 지식으로 취급 금지.
4. SQLite event chain은 일반적 무결성 손상을 검출하지만 전체 DB를 다시 쓰고 SHA를 일치시키는 공격까지 단독 방어하는 것은 아니다. 외부 핀과 owner의 실제 권한이 필요하다.
5. 오디오/비디오 전체 진위는 SRT SHA만으로 인증할 수 없다. 공식 금융 법령은 조회일·시행일·관할·적용대상을 실물 바이트로 검사해야 한다.

## X. 단일 목표 아키텍처(제안)

```
USER / CHAT TURN 1 (연구·원본 동결)
    |
    v
Private ORIGINAL / 791 roster / SHA + cue + transcript-vs-audio limitations
    |
    v
V6 Canonical Parent Source + All cue dispositions + Atom Graph
    |       \-- parent_context: cross-child condition/exception/numeric/source roles
    v
13 Child Review Packages (source- and parent-hash bound; no lost references)
    |
    v
USER / CHAT TURN 2 (별도 실제 사용자 메시지; ChatGPT 의미 재판정)
    |
    v
APPEND-ONLY Correction/Quarantine Decisions + new canonical atom revision
    |
    v
Independent stage E2 quality / V123 ChatGPT E3 formal review
    |
    v
E4 official primary source/date/jurisdiction/owner seal gate
    |
    v
E5 exactly-once single parent SQLite transaction (13/13 approved-or-explicitly-quarantined)
    |
    v
Verified Knowledge Graph, novelty/conflict/correction lineage + Advisory Retrieval
    |
    v
Answer-date official source refresh + suitability/risk checks (+ portfolio only after GO)
```

**실제 계약의 핵심:** parent 원본 불변/sidecar와 child-local 검토 표현을 분리할 수는 있지만, E3의 최종 입력에서는 **부모 조건이 실제 의미로 붙은 canonical 원자 또는 명시적인 출처 검증 격리**가 필수다. 미승인 부분 표현은 정식 원자 승인과 구조적으로 다른 타입으로 유지. 두 번째 사용자 턴을 Python 자체에서 생성하거나 호스트 서명인 척하지 않는다.

## XI. 실행 우선순위 및 단계별 완료 정의

### P0-0. 기준 버전·CI·문서 정렬 (먼저 시행)

- **작업:** V242 `b6aae4a`를 불변 진단 기준으로 고정하고 V166/E1~E7 문서, V193 2턴 규칙, V202 status, V203 합성 PASS, V242 실물 HOLD의 판정 스코프를 하나의 **머신리더블 STATUS**로 통합. 역사 파일 삭제/덮어쓰기 금지. 41개 열린 Draft PR 중 현행 의존 체인을 목록화하고, 승인 통합 대상/보류/역사 보존으로 분류. GitHub `main` 건드리지 않음. Python 3.11.18, 의존성, source manifest/hash pin, V5 core+V6+E1~E5 현행 테스트를 **동일 PR HEAD**에 수행하는 하나의 필수 CI를 만든다.
- **종료 기준:** 상태 문서·테스트 commit SHA가 동일, 현행 E1/E2/... 별도 PASS/HOLD 표준, 기존 frozen 코드 drift=0, CI 완료/실패 원인 재현. **문서 PASS의 실물 승인 과장 0**.

### P0-1. 교차 문맥의 정식 의미 해소·원자 정정 전이 (가장 중요한 코드 작업)

- **작업:** V237 13 child task와 V234 21 cross/49 edge를 immutable source graph로 유지한 채, correction overlay의 `parent_claim_sha`, `source_quote_sha`, `owner_child`, `role`, `qualifier_link`, `decision`(KEEP/REATOMIZE/EXCLUDE/OPEN), `review_turn2_sha`, revision/head를 정의. 21개 cross 원자에 대해 **조건·예외·숫자·멀리 떨어진 source cue**의 source-anchored 의미 판정 결과를 받아 새 **정식 V6 canonical 원자/자식 패킷** 또는 정확한 격리로 편입한다. 정정 전 C00057을 그대로 승인하지 않는다. V240의 **동결된 초기 21개 pending 계산**을 검증된 최신 revision의 unresolved 수로 대체한다. 초기 원본을 덮어쓰지 않고 재생 가능한 lineage 남김.
- **종료 기준:** 68개 원자 중 누락/중복/조건 상실 0, 21개 cross 전부 원문 기준 ACCEPT/REATOMIZE/QUARANTINE/OPEN 명시, 검증되지 않은 OPEN>0이면 승인 HOLD. 진짜 2턴 증빙 없이는 형식상 변환도 PASS 금지. B0013 부모 조건은 '인덱스 ETF에 한정' 내용이 빠지면 RED.

### P0-2. 2턴→V123 형식 및 실제 E3 경계 완결

- **작업:** 사용자 메시지 TURN1에서 원본/13 packet/수정대상/공식자료 후보 동결하고 실제 별도 TURN2에서 ChatGPT가 250 cue와 68 원자, 구간 경계와 부모 의미를 검토. 각 원자 source/stance/role/numeric/exception/contradiction, V123 필수 `source_cues`, `atom_verdicts`, official evidence bytes/as-of, quarantine, reviewed/OPEN를 채운다. `review_or_load_child`, `review_seams`, `review_parent`에 상태 변화·판정 이유 및 출처를 전달한다. 별도의 호스트 메시지 인증이 제공되지 않으면 `host_separate_turns_verified=false`를 유지한다.
- **종료 기준:** 13/13 **실제 V123 child case** 제출 및 결과 재조회(일부 HOLD 가능), 인용/조건/숫자 누락 0, 변조·위조 사용자 턴·수동 ID를 host-signed로 바꾼 입력 차단. ChatGPT 자체 작성/검토 정답은 인간 독립 블라인드 정답으로 간주하지 않음.

### P0-3. E4 typed 공식금융근거와 E5 원자적 긍정 저장 단일 경로

- **작업:** V235의 일반 V126 직접 저장 경로를 정식 출판 API에서 폐기/격리하고 V240 E4 sealed parent를 유일한 경로로 고정. E4 `official body SHA / 기관·HTTPS / 시행일 / 관할·대상 / 주장의 entailment / E3 최종결론 / 외부 owner seal`을 전수 확인하고 E5에 별도 **명시적인 승인권한**을 넘긴다. 연구 후보 E4 통과는 공식 금융 사실의 독립적 참 인증이나 개인 자문 GO와 구분. `v173 e5_authorized=false`를 임의 true로 바꾸지 않는다.
- **종료 기준:** **정상 합성 원본 13개 구간**의 V123→E4→E5 긍정 1건 이상에서 SQLite `parent_publications=1`, 정확한 지식/이벤트 delta, 재실행 중복 0; **12/13**, 근거 시점 누락, SHA 변조, 부적합 금융 상품, E4 seal 없는 경우 0/0/0. 실물 ETF는 실제 판정/공식근거 전에는 계속 발행 0.

### P0-4. E1 경로를 E2~E5의 정답 품질과 분리해 재합격

- **작업:** E1 합격 문구 **‘입력·검토·승인·저장 경로가 하나로 연결’**을 변경하지 않고, (a) 합성 적법 완전 긍정 및 부정 전 범위, (b) 실제 ETF 원본 입력·미승인 HOLD 재생, (c) V5·V6 전체 회귀·재개봉·동시성으로 재검문. 실제 정식 의미 결론의 정확도는 E2, 실제 ChatGPT 결정전달은 E3, E4 합법 승인/차단, E5 13구간 원자적 저장으로 각각 판정.
- **종료 기준:** E1 **소프트웨어 구조 PASS를 독립 선언할 수 있을 만큼의 긍정·부정 경로**. 실제 연구의 승인 13/13이 없으면 `E1_REAL_OWNER_FULL_APPROVAL=HOLD`를 그대로 표시. E1만 불가능한 목표로 정의해 E2 진행을 영구 봉쇄하는 순환 제거.

### P1-1. 금융 의미 정확도 및 측정 체계

- **작업:** V228 ETF 원본 및 새 미노출 영상으로 사전 고정 원자 정답 후보(원문 blind-pass, 반례, 정정 append-only)를 작성. 현재 ChatGPT가 작성하는 기준셋은 내부 재검문 기준이며 외부 독립 gold라고 부르지 않는다. TP/FP/FN 전체, 위험, 화자·조건·예외, 기간/세율, 인용 범위 및 법령 최신성 분모를 보고. 공식 자료를 해당 시점에 웹 원문으로 재조회.
- **종료 기준:** 독립 검토 자격을 충족하는 평가자료가 확보되면 precision≥95%, recall≥98%, high-risk FN=0을 적용. 그렇지 않으면 `UNMEASURABLE`이고 기능 동작 PASS와 품질 인증을 분리한다.

### P1-2. 동결 커널 운영 안정성·장편 처리량

- **작업:** 250 cue / 약 1,000~1,500 cue / 복수 5편 / 10편에서 단계별 CPU·ChatGPT 의미 검토·공식자료 검색·SQLite 재생시간/토큰/도구콜/중단·재개 비용을 별도로 측정. V6 전체 이벤트 체인 O(n) 재생의 장편 성능 계측. 공개 GitHub code, 비공개 원본 보관 분리. 체크포인트 복구 실패와 중복 실행을 구분.
- **종료 기준:** 다른 원본 5편에서 출처 유실 0, 원자 누락·반례/조건 검문 PASS, 중단→재개→동일 영수증, 부분 발행 0, 병목 예산을 실측. 이를 통과하기 전 703 롱폼 전체 배치 계획 단정 금지.

### P1-3. 승인 지식 누적과 자문 근거 재사용

- **작업:** 새 승인 원자를 기존 116·P4 29와 조회 단계에서 분리한 뒤 SAME/SUPPORTS/EXTENDS/CONFLICTS/SUPERSEDED/DISTINCT/OPEN를 원문·시점·전제에 근거해 채택. 신규 영상의 승인 지식만 통합, 기존 사항의 원본/버전 보존. 원자 ID→영상 cue→공식 원문→지식 주제→답변 인용 역추적. 고정 ISA/IRP/ETF/연금 질문 및 최신 법령 재검증.
- **종료 기준:** 승인 1편에서 신규·동치·충돌·유효기간 의도대로 통합되고, 2번째 미노출 영상에서 중복/시점 충돌을 제대로 처리, 자문 질문에 근거/반례/불확정 표시, 지식 재조회 결과 동일. 개인 포트폴리오는 연구 엔진 완료 후 별도 단계.

## XII. 개발 운영의 무조건적 원칙

- **새 구현 전 계획 문서에 실패 재현·입출력 계약·수용기준을 먼저 명시.** 같은 문제로 V243, V244… 랩퍼/수치만 증가시키지 않는다.
- **실제 두 사용자 메시지 필수:** 하나의 응답·프로세스에서 turn2를 가짜 생성하지 않는다. ChatGPT를 GitHub Actions나 Python이 자체 API 없이 무인 호출할 수 없다는 제약을 사용자 경험/스케줄에 반영한다.
- **원본 보호:** 역사 원본·기존 event/head·main/동결 코어 불변. 정정은 append-only 새 revision. 비공개 SRT/금융 개인정보의 공용 repo 업로드 금지. 임시 sandbox ZIP만을 장기 복구 수단으로 간주 금지.
- **상태 용어 분리:** SOURCE_VERIFIED / STRUCTURAL_HOST_STAGED / MEANING_REVIEWED / E3_REVIEW_DECISION / E4_RESEARCH_CERTIFIED / E5_PARENT_COMMITTED / FINANCIAL_FACT_VERIFIED / ADVISORY_ELIGIBLE. 하나라도 자동으로 다른 단계를 부여하지 않는다.
- **운영 지표:** 완료로 인정한 영상의 source/atom/official/knowledge/answer 각 층의 분모, 검토 주체, Git HEAD, owner PIN, SHA, 실제 사용된 ChatGPT USER 턴 1·2, CI ID, 미완료 원인을 단일 status 원장에 기록.

## XIII. 우선 착수 순서와 확정 권고

**즉시:** P0-0(정식 기준/CI/브랜치/운영 상태 통일) → P0-1(검토 의견을 정식 원자 revision으로 반영하는 정정 상태전이) → P0-2(13구간 실제 ChatGPT TURN2→V123 형식) → P0-3(E4/E5 명시 권한/긍정 경로) → P0-4(E1 구조 최종 합격). 그 다음 P1-1(정확도)·P1-2(장편/다편 파일럿)·P1-3(통합지식·자문). 

**핵심 결론:** V6 기반의 해시·SQLite 커널은 재사용한다. E1~E5로 가는 경로가 218개의 실험용 실행 브리지와 여러 오래된 PASS 보고서에 분산된 부분을 하나의 정식 상태전이·증빙 컴파일러·승인 관문으로 정리해야 한다. 현재 V242 소스 구조 13/13 성공은 **출발점**, 금융 지식/자문 완성이 아니다. **초기 1편의 정식 2턴 검토·공식 근거·E4/E5 전체 성공을 한 번 실제로 증명한 뒤에만 영상 확장을 시작한다.**

## XIV. 주요 감사 근거

- [루트 README (구 V203 E1 합성 PASS 문구)](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/README.md)
- [마스터 연구·자문 설계 계약](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/ire/RESEARCH_ADVISORY_MASTER_CONTRACT_20261104.md)
- [V6 결정론적 커널 아키텍처](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/ire/v6/contracts/ARCHITECTURE_DECISION_V6_000.md)
- [V166 E1~E7 동결 합격 기준](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/validation/ire-v6-frozen/V166_E1_E7_SEQUENTIAL_ENGINE_VERIFICATION_PLAN.md)
- [V193 실제 사용자 2턴 필수 정책](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/validation/ire-v6-frozen/V193_E3_TWO_ACTUAL_USER_TURNS_MANDATORY_PROTOCOL_20261120.md)
- [V202 E1 독립 실패 보고](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/validation/ire-v6-frozen/V202_E1_INDEPENDENT_REAUDIT_FAIL_20261120.md)
- [V203 합성 E1 긍정 연결](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/validation/ire-v6-frozen/V203_E1_REAL_V176_ORIGIN_TO_NATIVE_V128_STRUCTURAL_PASS_20261120.md)
- [V236 E1 근본 원인](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/validation/ire-v6-frozen/V236_E1_INDEPENDENT_ROOT_CAUSE_DIAGNOSIS_ONLY_20261121.md)
- [V241 12개 실물 자식 호스트](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/validation/ire-v6-frozen/V241_E1_REAL_ETF250_EXECUTION_RESULTS_12_CHILD_HOSTS_1_HOLD_20261121.md)
- [V242 B0013 마지막 구조 호스트](https://github.com/yhappcom/pensionport/blob/verify/ire-v6-e1-v230-v228-source-native-handoff-20261121/validation/ire-v6-frozen/V242_E1_REAL_ETF250_B0013_CONDITION_LINKED_NATIVE_HOST_PASS_E3_E5_HOLD_20261122.md)
- [검증 브랜치 Draft PR #76](https://github.com/yhappcom/pensionport/pull/76)
- [최신 E1 전용 CI](https://github.com/yhappcom/pensionport/actions/runs/44957548898)
- [전수 추적파일 감사 스냅샷 CI](https://github.com/yhappcom/pensionport/actions/runs/44958700308)

**변경 관리:** 본 보고서는 원본 코드를 수정하지 않는 진단 산출물이다. 특정 구현을 완료했다고 표기하지 않았으며 향후 사용자 승인된 이력·합격 기준에 따라 진척이 확인될 때만 STATUS/보고서를 갱신한다.