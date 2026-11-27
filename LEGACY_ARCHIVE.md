# 과거 연구 보존 및 Clean Start 경계 (D0)

보존 브랜치: [audit/full-repository-snapshot-20261122](https://github.com/yhappcom/pensionport/tree/audit/full-repository-snapshot-20261122). 기존 통합 브랜치를 참조 전용으로 지정해 두 개의 브랜치만 유지한다.
- 기존 통합 head: 7e3b40d680c12e7301a00a65997b688c32c207a4
- 기존 통합 tree: e69409c21f5dcebee1f11fa11b1af9d0dd94e6cf
- 동결 선언 head: 8e21fd24cf547802e7d943dbc6d74c32fbe78e7e
- 전환 전 main: d613fd201f4bb077f1ccc74d28dee937b11bfcb2
- 기존 main은 통합 브랜치의 조상(뒤처짐 0). 통합 브랜치의 기존 2,653개 파일 경로·모드·blob 해시가 전부 보존됨. 동결 문서 2개만 추가.
- 기존 동결 선언: [LEGACY_FREEZE_20261127.md](https://github.com/yhappcom/pensionport/blob/8e21fd24cf547802e7d943dbc6d74c32fbe78e7e/LEGACY_FREEZE_20261127.md), [영수증](https://github.com/yhappcom/pensionport/blob/8e21fd24cf547802e7d943dbc6d74c32fbe78e7e/LEGACY_FREEZE_20261127.json).
- 접근 가능한 미반영 연구 ZIP 21개 등 고유 파일 55개를 Library의 IRE_D0_20261127 폴더에 D0_LEGACY_RESEARCH_FREEZE_20261127.zip으로 보존함. SHA-256 75e0c2bd180c28a76eeb86783eba1f490a3ca13c28a43c57ad3f83e1b7c90bf5, 57,736,523 bytes. 개별 해시는 동봉 MANIFEST.json에 있음. 전체 역사상의 비공개 파일을 전수 확보했다는 인증은 아니다.
- SRT 전용 신규 입력: D0_SRT_ONLY_PILOT_20261127.zip, SHA-256 a7f7f806e36de1a786aa147ff55d2a552eab7b01923582bcb43b4db5851fd6a0, 실제 원본 3개/645 자막. 원본의 바이트 그대로이며 이름은 내용 해시 기반이다. 파일 외 별도 과거 연구 내용 없음. 개인 Library에 저장.
- Google Drive SRT 보관함은 발견했으나 현재 연결에서 내부 파일이 조회되지 않음. 전체 791편 확보·미노출 여부는 D3/D6에서 별도 확인한다. Google Drive 원본은 변경하지 않았다.
- 사용자 추가 확인: 실제 업로드 범위는 약 1~300번이다. 이는 업로드 범위에 관한 사용자 제공 정보이며 전수 파일 존재·접근·무결성 검증 결과가 아니다. 현재 직접 확보한 시범 원본 3편과 구분한다.
- 브랜치 보호 설정 조회는 연결 권한 제한으로 실패했다. 동결은 관리 정책이며 실제 쓰기 보호 잠금의 인증이 아니다.

**금지:** 과거 투자지식 116개, P4 29개, 원자 기록, 기존 금융근거, 코드, 정답셋, 검증자료, 이전 연구 결과의 신규 연구 입력 사용. 오직 SRT 원문만 사용할 수 있다. 기존 연구는 보존·복구 용도 외 참조하지 않는다. 신규 main에 과거 연구 파일을 복사하지 않는다. Git의 기존 역사 자체는 삭제하거나 강제 재작성하지 않는다.
