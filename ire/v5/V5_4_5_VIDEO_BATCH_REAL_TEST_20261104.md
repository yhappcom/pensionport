# IRE V5 — 4–5편 단일 요청 연구처리 성능 전환 (2026-11-04)

**결론:** V5 5편 통합 source admission, round-robin source packets, per-video hash-chained batch receipts, private 5-video encrypted archive, GitHub Actions 5-video job reducer **실제 통과**. **5편 전체 금융연구를 사용자 1턴에 완료하는 성능은 아직 미입증·NO-GO.**

## 실제 원본 확인
비공개 `1-100.zip`에서 #1–#5를 영상 번호와 SHA256으로 대조함. 전체 5,129 cues, 원본 394,221 bytes. V5 새 planner는 **288** 문맥 (#1 67, #2 76, #3 44, #4 43, #5 58). 과거 V3 적응형 346창과 별도 분할이므로 동일 품질이라고 주장할 수 없음.

## 실제 단일 사용자 요청의 작업 결과
ChatGPT가 5편의 첫 문맥을 **각 1개** 직접 읽고 문맥별 의미를 분해함. 총 **5 provisional claims / 5 evidence dispositions / 5 prior relation reviews / 5 immutable per-video batch receipts**. #5 도입은 의미 없는 투자 명제로 강제하지 않고 NONCLAIM 처리. **5/288문맥 접수, 283개 미처리**, 금융 사실 승인 0, 상담 승인 0, 지식 자동 병합 0. 동일 배치 재제출 시 중복 저장 0.

## 엔진 및 CI
- `ire/v5/engine.py`에 내용 기반 사전검증 `BATCH_ACCEPT` 추가(배치당 500개 모델/증거/관계 action, per-video event 1개). Invalid quote → 전체 batch reject. Multi-video set은 전수 사전검사 후 per-video 쓰기: **전 영상 물리적 atomic commit 아님**, 동일 content 재시도 가능.
- `ire/v5/batch.py`, `ire/v5/planner.py`, `ire/v5/batch_backup.py`: exactly 4/5 full-video originals, independent source hashes, fair packet scheduling, open review queue, per-video encrypted backups and full re-open proofs.
- `ire/v5_app/batch_worker.py`와 GitHub Actions 연결: 개발 브랜치에 `ire/v5_app/batch_requests/v5-gomhee-001-005-batch/{000001,000002}.json` 등록 후 `github-actions[bot]`이 `ire/v5_app/batch_states/v5-gomhee-001-005-batch.json` 생성. bot commit `ba445f550c0be1bfab1c4aef86d833068980d834`: 5 videos, 5/288, W00002 per video, facts unverified. GitHub 자체는 SRT 원본이나 개별 claim을 갖지 않음.
- Local core 53 tests (50 PASS/3 SKIP; missing old private fixtures), GitHub app 24 tests PASS. GitHub cleanroom workflow run **41674198121 SUCCESS**, source/privacy guard included.
- Bounded 25-window source-only packet: 36,510 bytes, 5-video round robin. 이는 스케줄러 측정, 25문맥 분석 성공이 아님.

## 암호화 클라우드 체크포인트
5 original files, all plans and 5 source-linked research receipts encrypted as a single multi-envelope zip; file SHA256 `47b7fb103341fa5c23f8f5990d697376e9eb3e2a718e5042c6536b38618e3d51`. Google Drive upload → readback raw bytes and hash → 5 private V5 ledgers newly restored in separate container path, exact status replay success.
- Archive https://drive.google.com/file/d/1GTsSH6PR1MaDwMgfSPcpp_XQQnQIDjng/view?usp=drivesdk
- **Recovery secret is not stored in archive/GitHub/Drive**; owner must retain separate key. A future independent ChatGPT chat recovery has not been tested.

## Release acceptance
User's desired throughput is **4–5 *fully researched videos* per one user turn**, not simply opening 5 SRT originals. Prove: each cue annotated, each atom investigated with official scope and dated rules or evidence-backed OPEN, old knowledge relation reviewed, full report with no UNPROCESSED substitution, 4–5 sealed originals + independent cloud readback, user follow-up instructions 0. Still missing **283 genuine source windows** and claim-specific reviews. Current no-API ChatGPT host may have context and time limits: GitHub Actions cannot asynchronously invoke ChatGPT meaning analysis, so an unbounded one-turn completion cannot be promised based on Python tests. **NO-GO until live 5/5 proof**.

No main edits, no private SRT, claim text or keys committed.