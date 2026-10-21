# 국세청 상태조회 연결

실제 API 승인은 사용자 화면에서 확인했습니다. 인증키와 사업자등록번호는 아직 이 실행 환경에 없으므로 실호출 검증은 미완료입니다. 아래 구성은 인허가 상태 대신 세무상 상태를 조회하며, 전국 주유소 사업자번호를 찾아주지 않습니다.

GitHub Settings → Secrets and variables → Actions → Repository secrets:

- `NTS_API_KEY`: 공공데이터포털 일반 인증키. URL 인코딩 전(Decoding) 원문. 요청 시 코드가 URL 인코딩합니다.
- `NTS_TARGETS_JSON`: 조회 대상 연결표 JSON. 예시 형식은 아래와 같습니다. 실제 자료만 입력하세요.

```json
[{"id":"자치단체코드:관리번호","businessNumber":"사업자등록번호10자리"}]
```

현재 연결표가 없으므로 전국 수집을 시작할 수 없습니다. 우선 실제로 번호를 확인한 한 곳으로 테스트하세요. 번호·키를 채팅이나 공개 저장소에 올리지 마세요. 파일은 비밀키 공간의 크기 제한과 운영 규모를 고려해 소규모 검증용(최대 1000개)으로 제한했습니다. 전국 운영은 비공개 DB/저장소로 이관해야 합니다.

Actions → Query NTS business status → Run workflow로 수동 조회합니다. 실제 성공 후 Variables에 `NTS_SYNC_ENABLED=true`를 설정하면 매시 43분 예약 조회합니다. GitHub 지연·한도·제공기관 반영 지연이 있으므로 신고 즉시 반영을 보장하지 않습니다. 공개 사이트에는 대상 ID·상태·폐업일만 게시합니다. 번호·키 및 세무 응답 전체는 게시하지 않습니다. 공개 게시할 대상인지 확인한 연결표만 사용하세요.

명세: https://infuser.odcloud.kr/api/stages/28493/api-docs?1728017570963
POST https://api.odcloud.kr/api/nts-businessman/v1/status
