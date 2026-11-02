# IRE V3 — 한 턴 분석의 입력·출력 병목 개선 (2026-11-03)

## 목표·제약

기존 `prepare → source reading → answer generation → execute → quality gate`의
**전체 채팅 턴 도구 호출·텍스트 반복량을 줄이는 것**이 목표다.
현재 ChatGPT가 실제 원문을 해석한다. 이 코드에는 외부 LLM 호출, 임의
금융 주장 생성, 원문 없이 비주장 지정, 누락 창 자동 승인 기능이 없다.
문맥·도구·실행시간 한계가 있어 338개 미해석 문맥의 한 턴 무조건 완주는
여전히 보장할 수 없다. 원본 연구가 완료되지 않으면 정직하게 부분 완료로 기록한다.

## 1. 유실 없는 간결한 응답 계약

`ire/v3_compact_answers.py`는 모델/호스트가 반환하는 압축형 분석 응답을
기존 `IRE_CHAT_WINDOW_ANSWER_V1`로 **완전 복원**한다. 저장되는 체크포인트
형식과 주장의 필수 frame, 기존 출처 검사는 변경하지 않는다.

```json
{
  "schema": "IRE_V3_ONE_TURN_COMPACT_ANSWERS_V1",
  "batch_fingerprint": "원본 매니페스트의 실제 SHA-256",
  "reasons": ["사실 판단이 아닌 대화형 질문만 포함하며 금융 명제 미제시"],
  "answers": [{
    "video_id": "실제 11문자 영상ID",
    "window_id": "W00009",
    "packet_sha256": "원본 패킷 실제 SHA-256",
    "claims": [{
      "proposition": "원본과 맞는 금융 발언의 원자 의미",
      "claim_types": ["STRATEGY"],
      "frame": "기존 IRE 전체 frame 객체 필수",
      "source_refs": [54, [55, "정확한 인용 부분"]]
    }],
    "cue_runs": [[54, 55, "L", -1], [56, 57, "N", 0]]
  }]
}
```

이 예시는 구조 설명용이고 실제 원본이나 유효한 주장을 나타내지 않는다.
`source_refs`의 정수는 해당 **primary cue 전체를 정확히 인용**하는 표현이다.
`[cue_id, "직접 인용"]` 또는 `[cue_id, 글자시작, 글자끝]`도 허용한다.
위치를 사용하는 경우 실제 원본 문자열에서 직접 발췌하며, 길이와 인용을
정확히 확인한다. 주변 halo의 인용을 사용하지 못한다.

`cue_runs`의 `L`, `N`, `U`는 각각 연결된 주장, 비주장 후보, 해석 미완료다.
**모든 원본 primary cue가 명시적으로 정확히 한 번 등장해야 한다.**
`N`은 8자 이상 구체적 이유가 없으면 거부된다. `L`은 해당 cue를 직접
인용한 주장이 있어야 한다. 누락된 cue를 `N`으로 암묵 처리하는 옵션은 없다.

`run_one_turn`의 `--private-answers`에 위 형식 또는 기존 V1 형식을
그대로 제출할 수 있다. 서버는 전체 압축 묶음을 먼저 복원·검증하고,
모든 인용·상태·체크포인트·고위험 의미 검사를 기존 경로로 수행한다.
어느 창이든 부적합하면 **새로운 체크포인트를 하나도 저장하지 않는다.**

## 2. 원본 cue를 중복 출력하지 않는 비공개 채팅 렌더러

```bash
python -m ire.v3_one_turn prepare \
  --private-manifest /private/ire_v3_batch.json \
  --private-packets-file /private/compact_source.json \
  --compact --max-packets 12 --max-chars 60000

python -m ire.v3_one_turn render \
  --private-manifest /private/ire_v3_batch.json \
  --private-packets-file /private/compact_source.json \
  --batch-number 1 \
  --private-rendered-file /private/chat_input_batch01.json

python -m ire.v3_one_turn execute \
  --private-manifest /private/ire_v3_batch.json \
  --private-answers /private/chatgpt_compact_answers.json \
  --private-knowledge-dir /private/ire_kb \
  --private-audit-dir /private/ire_audits
```

`render`는 한 배치 안의 모든 primary/halo cue를 출처 영상별 한 번만
표시한, ChatGPT 분석용 읽기 입력을 소유자 전용 파일에 보관한다.
세션/원본 패킷 SHA와 window의 primary·문맥 구분도 표시한다.
**렌더링 직전에 실제 원본 SRT와 현재 불변 체크포인트 전체를 다시 읽어**
계획을 재계산한다. 자체 해시만 다시 계산한 가짜 원문 계획이나 분석이
새로 저장된 뒤 사용한 낡은 계획을 차단한다. 콘솔에는 원문을 출력하지 않는다.

## 3. 실제 원본의 비용·정확성 재현 시험

#1~#5 v003 기존 분석 **8창·31개 주장**에 대한 읽기 전용 시험:

- V1 답변 묶음 직렬화 39,799바이트 → 압축 응답 24,395바이트:
  **38.7% 감소**. 주장의 텍스트, frame, 실제 인용, cue별 판정이
  바이트 수준으로 완전 복원됐으며 원본 체크포인트는 변경하지 않았다.
- 실제 비공개 338개 남은 창·29개 배치에서 처음 3개를 샘플링한 결과,
  반복 cue JSON을 읽기 좋은 원문 렌더 형식으로 대체해 배치별 표시 크기를
  약 69% 줄였다. **입력 토큰 비용·모델 연산량 전체 감소율 인증은 아님.**
- 원본 5,129cue, 346창, 이전 완료 8, 미완료 338, 새로운 자동 승인 0.
- 합성 회귀시험은 gap/overlap, 가짜 nonclaim 기본값, 오염된 인용·offset,
  원본 재해시 위조, checkpoint stale, 기존 V1/V3 경로와의 바이트 동치성,
  비공개 원문 stdout 노출 방지까지 검사한다.

## 4. 아직 필요한 것

모델이 금융 의미를 실제로 이해하고 **338개 모든 원본 문맥에 대해**
충분한 원자 주장을 생성하는 일은 여전히 채팅 모델의 역할이다.
그 결과를 확인할 독립 블라인드 골드와 금융 법규 공식 원문 심사가 없다면
소프트웨어 단위 테스트 PASS를 의미 정확도 PASS로 표시하지 않는다.
기존 P0~P2 증거·관계·자문 게이트를 우회하지 않는다.