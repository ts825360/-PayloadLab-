# 터미널 UX 구현 검증 근거

연결: [#22](https://github.com/ts825360/-PayloadLab-/issues/22), [#13](https://github.com/ts825360/-PayloadLab-/issues/13). 진행 상태는 [WORK-STATE](../WORK-STATE.md)에서만 관리한다.

## UX-01 — 진단 어댑터

2026-10-24, 착수 기준 main `4392096`. frontend/src/terminal/diagnostics.js와 테스트를 추가했다. 기존 API·랩·화면은 변경하지 않았다.

- Red: 모듈 부재 확인 후 빈 함수에서 8개 중 대표 진단·유니코드 2개 실패, 폴백 6개 통과.
- Green: 실제 Permission denied 구절을 코드포인트 범위로 지정하고 기존 Lens의 why/next를 재사용했다. 신규 8개 모두 통과.
- 전체 Docker Vitest: **13개 파일, 62개 테스트 통과**.
- Docker Vite build: **종료 코드 0**, 478개 모듈. 새 어댑터는 아직 화면에 import하지 않아 기존 bundle에 연결되지 않았다.
- 브라우저 확인: 이 단계는 순수 함수이며 UI가 없어 해당 없음. 실제 밑줄·hover/Lens 연결이 완료됐다고 보고하지 않는다.

검증 명령:

```powershell
docker compose exec -T frontend npm test -- src/terminal/diagnostics.test.js --reporter=dot --maxWorkers=1 --minWorkers=1
docker compose exec -T frontend npm test -- --reporter=dot --maxWorkers=1 --minWorkers=1 --testTimeout=15000
docker compose exec -T frontend npm run build
```

시행착오: 기본 워커는 컨테이너 프로세스 제한에서 spawn EAGAIN이 발생했다. 워커를 제한해 해결했다. 전체 2개 워커 검사에서는 기존 13개 조합 UI 시험이 5초 제한을 초과해 61/62 통과였으며, **assertion을 변경하지 않고** 1CPU 환경에서 단일 워커·15초 예산으로 재실행해 62/62 통과했다. 해당 UI 시험의 실제 실행 시간은 재검사에서 2.7초였다. 위 설정은 검사 명령에만 적용했으며 앱·Docker 자원 제한·테스트 전역 설정은 바꾸지 않았다.

소스 자가 검토: 알려진 category/status와 실제 stderr 구절을 모두 확인한다. 원문은 수정하지 않고 미지원 trace에서 원인을 지어내지 않는다. 범위를 JS UTF-16 offset으로 소비하지 않도록 후속 렌더러도 코드포인트 slicing을 사용해야 한다.
