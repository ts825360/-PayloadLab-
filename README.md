# PayloadLab

> ⚠️ 이 앱은 의도적으로 취약하게 만들어졌습니다. 로컬 Docker 환경에서만 실행하세요. 외부에 공개하거나, 여기서 배운 기법을 실제 서비스에 시도하지 마세요.

DVWA 같은 웹 공격 실습 도구를 참고하되, **왜 공격이 성공했는지 / 왜 실패했는지**를 초보자도 이해할 수 있게 만드는 교육용 웹 공격 실습 플랫폼입니다.

- 공격에 성공하면 → 입력값이 서버에서 실제로 어떻게 처리되어 공격으로 이어졌는지, Python Tutor 스타일 **상태 다이어그램**(변수 → 실제 DB/데이터 상태)으로 보여줍니다. XSS는 실제로 우리 서버가 돌려준 페이지를 iframe으로 띄워 **진짜로 실행**합니다.
- 공격에 실패하면 → **Lens**가 어떤 조건이 부족해서 실패했는지, 입력창 밑줄에 마우스를 올리면 규칙 기반으로 진단해줍니다.

## 지금 상태 — MVP 동작 중

**SQL Injection · Reflected XSS · IDOR**, 각 **Easy/Medium** 난이도까지 총 6개 랩이 실제로 동작합니다.

- SQL Injection: 실제 SQLite에 실제 취약한 쿼리를 실행해서 성공/실패를 판정 (패턴 매칭이 아님)
- Reflected XSS: 백엔드가 실제 HTML 문서를 돌려주고 프론트가 그걸 iframe으로 진짜 내비게이션 — `<script>`가 실제로 실행됨 (DVWA와 동일한 원리)
- IDOR: 세션 대신 클라이언트가 보낸 값을 그대로 신뢰하는 취약점
- Medium 난이도는 전부 "Easy와 같은 핵심 기법 + 순진한 필터 하나를 대소문자 등으로 우회"하는 구조

세부 설계 논의와 전체 이력은 이슈에 정리되어 있습니다.

- 📌 [#12 프로젝트 비전과 전체 기획](https://github.com/ts825360/payload-lab/issues/12) — 무엇을, 왜 만드는지와 전체 설계, 하위 논의 이슈 전체 목록
- 📌 [#13 깃허브 사용 방법](https://github.com/ts825360/payload-lab/issues/13) — 깃허브의 이슈/브랜치/풀 리퀘스트를 처음 써보는 팀원을 위한 단계별 안내

새로 합류한 팀원은 `#13` → `#12` 순서로 읽는 것을 권장합니다.

## 실행 방법

```bash
docker compose up --build
```

- 프론트엔드: http://localhost:5173
- 백엔드 API: http://localhost:8000

### 왜 로컬에서만 실행해야 하나요

이건 "혹시 모르니 조심하라"는 형식적 경고가 아니라, 앱 안에 **진짜로 동작하는 공격 통로**가 있어서입니다. 대표적으로 Reflected XSS 랩의 `GET /labs/{id}/render` 엔드포인트는 쿼리스트링에 들어온 값을 이스케이프 없이 그대로 HTML로 되돌려주는 **실제 reflected XSS**입니다. 앱 안에서는 이 결과를 `allow-same-origin` 없는 sandbox iframe에 가두지만, 누군가 이 URL을 브라우저 주소창에 직접 열면 백엔드 오리진에서 아무 격리 없이 스크립트가 실행됩니다. 그래서 이 서버를 공개 네트워크에 띄우면 실습용 취약점이 그대로 남에게 열린 취약점이 됩니다 — 반드시 로컬에서만 실행하세요.

## 기술 스택

Python (FastAPI) · React (Vite) · SQLite · Docker / Docker Compose

## "Lens"라는 이름은 어디서 왔나요

Lens는 VS Code의 인기 확장 프로그램 **[Error Lens](https://marketplace.visualstudio.com/items?itemName=usernamehw.errorlens)**에서 아이디어를 가져온 이름입니다. 원래 코드 에디터는 에러가 나면 밑줄만 긋고, 그 이유를 보려면 마우스를 올리거나 별도 패널을 열어야 합니다. Error Lens는 그 이유를 에러가 난 줄 바로 옆에 즉시 텍스트로 띄워줘서, 별도 클릭 없이 바로 원인을 알 수 있게 해주는 도구입니다.

팀원 로메인의 해커톤 프로젝트 [loupe](https://github.com/RomainHartmann/loupe)(프랑스어로 "돋보기")도 같은 발상입니다 — 기사 속에서 의심스러운 문장에 바로 밑줄을 긋고 그 옆에 이유를 보여줍니다.

우리 프로젝트의 Lens는 이 발상을 보안 실습에 그대로 적용한 것입니다.

## 남은 작업

- README/Lens 문안/Docker 안전 문구를 자료조사 기반으로 다듬기 ([#14](https://github.com/ts825360/payload-lab/issues/14), [#15](https://github.com/ts825360/payload-lab/issues/15), [#16](https://github.com/ts825360/payload-lab/issues/16))

## 참고 자료

- [docs/superpowers/specs/2026-07-15-web-attack-lab-design.md](docs/superpowers/specs/2026-07-15-web-attack-lab-design.md) — 초기 설계 문서 초안
- [docs/references/romain-loupe-agent-prompts.md](docs/references/romain-loupe-agent-prompts.md) — 참고한 [loupe](https://github.com/RomainHartmann/loupe) 저장소의 프롬프트/에이전트 운영 패턴 정리
