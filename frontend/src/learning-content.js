export const CATEGORIES = [
  {
    id: "sql_injection",
    label: "SQL Injection",
    short: "SQL",
    subtitle: "데이터베이스 · 조회 조건",
    title: "문자열이 조건이 되는 순간",
    description:
      "입력한 이름이 SQL에 들어가는 자리를 찾아보세요. 작은 변화가 조회 결과를 어떻게 바꾸는지 직접 확인할 수 있어요.",
    field: "username",
    fieldLabel: "사용자 이름",
    placeholder: "이름이나 짧은 문장을 입력해보세요",
    prefix: "SELECT * FROM users WHERE username = '",
    suffix: "' AND password = 'this_is_definitely_wrong'",
    composition: "SQL",
    context: "비밀번호를 모르는 로그인 화면입니다. 이름 입력만 바꿀 수 있어요.",
    lesson: "strings",
  },
  {
    id: "reflected_xss",
    label: "Reflected XSS",
    short: "HTML",
    subtitle: "브라우저 · HTML 해석",
    title: "내 입력이 페이지의 일부가 된다면",
    description:
      "검색어가 HTML에 들어가는 과정을 따라가 보세요. 일반 글자와 태그를 브라우저가 어떻게 구분하는지 관찰해요.",
    field: "query",
    fieldLabel: "검색어",
    placeholder: "검색할 단어나 HTML을 입력해보세요",
    prefix: "<p>'",
    suffix: "'에 대한 검색 결과입니다</p>",
    composition: "HTML",
    context: "검색어가 별도의 이스케이프 처리 없이 응답 HTML에 들어갑니다.",
    lesson: "html",
  },
  {
    id: "idor",
    label: "IDOR",
    short: "ID",
    subtitle: "접근 권한 · 객체 소유 관계",
    title: "번호를 알면, 볼 권한도 있을까요?",
    description:
      "요청한 주문과 실제 소유자를 연결해보세요. 대상을 찾는 것과 권한을 확인하는 것은 다른 과정이에요.",
    field: "requested_id",
    fieldLabel: "주문번호",
    placeholder: "본인 주문 1042부터 확인해보세요",
    prefix: "GET /orders/",
    suffix: "",
    composition: "요청",
    context:
      "현재 로그인 사용자는 1042입니다. 주문 1042와 1043의 소유 관계를 비교해보세요.",
    lesson: "ownership",
    numeric: true,
  },
  {
    id:'ssrf',label:'SSRF',short:'URL',subtitle:'서버 요청 · 목적지',
    title:'내가 준 주소로, 누가 찾아갈까요?',
    description:'브라우저가 아니라 서버가 주소를 요청할 때 생기는 경계를 모의 환경에서 관찰해요.',
    field:'target_url',fieldLabel:'가져올 주소',placeholder:'https://example.com/ 부터 관찰해보세요',
    prefix:'GET ',suffix:'',composition:'서버 요청',context:'미리보기 서버의 URL 입력입니다. 실제 네트워크 요청은 하지 않아요.',lesson:'network',simulated:true,
  },
  {
    id:'command_injection',label:'Command Injection',short:'CMD',subtitle:'서버 명령 · 입력 경계',
    title:'주소가 명령의 일부가 된다면',
    description:'서버 명령에 입력이 섞일 때, 인자와 새 명령의 차이를 살펴봐요.',
    field:'hostname',fieldLabel:'호스트 이름',placeholder:'example.com',prefix:'ping -c 1 ',suffix:'',
    composition:'명령',context:'연결 확인 기능의 입력을 흉내 냅니다. 명령·ping 모두 실제로 실행하지 않아요.',lesson:'commands',simulated:true,
  },
  {
    id:'linux_basics',label:'Linux 명령어',short:'QUIZ',subtitle:'가상 파일 · 빈칸 연습',
    title:'파일을 찾고, 정보를 읽는 첫 명령',
    description:'빈칸에 맞는 명령어를 작성하고 가상 폴더의 결과를 확인해요.',
    field:'command',fieldLabel:'명령어 빈칸',placeholder:'목록을 보여주는 명령어는 무엇일까요?',prefix:'',suffix:'',composition:'명령',
    context:'가상 /lab 폴더 연습입니다. Easy는 목록, Normal은 소유자와 권한까지 확인해요.',lesson:'commands',simulated:true,terminal:true,
  },
  {
    id:'permissions',label:'권한상승 기초',short:'PERM',subtitle:'가상 사용자 · 접근 권한',
    title:'같은 파일인데, 누구는 읽을 수 있을까요?',
    description:'현재 사용자와 파일 권한을 비교하고 잘못된 관리자 도우미 설정을 모의 환경에서 관찰해요.',
    field:'command',fieldLabel:'터미널 명령어',placeholder:'whoami',prefix:'',suffix:'',composition:'명령',
    context:'student로 시작하는 교육용 가상 터미널입니다. 실제 OS 권한·파일은 바뀌지 않아요.',lesson:'permissions',simulated:true,terminal:true,plannedLevels:['medium'],
  },
];
export const LESSONS = {
  strings: {
    title: "작은따옴표는 값의 경계예요",
    lead: "SQL은 작은따옴표 안의 내용을 문자열 값으로 읽습니다.",
    example: "username = 'alice'",
    body: "여기서 alice는 명령이 아니라 비교할 이름입니다. 값이 끝나는 따옴표 뒤에는 다른 SQL 문법이 올 수 있어요. 작은따옴표 두 개를 연속으로 쓰는 이스케이프도 있으므로, 따옴표가 있다고 항상 문자열을 벗어난 것은 아닙니다.",
    question: "내가 입력한 글자는 지금 어느 따옴표 사이에 있나요?",
  },
  operators: {
    title: "조건은 어떻게 연결될까요?",
    lead: "AND는 두 조건 모두, OR는 어느 한 조건이 참이면 전체를 참으로 만듭니다.",
    example: "A OR (B AND C)",
    body: "AND가 OR보다 먼저 묶입니다. 따라서 A OR B AND C는 (A OR B) AND C와 같지 않아요. 아래 조건 그림은 선택한 계정에 대해 이 관계를 풀어 보여줍니다. --는 문자열 밖에서 그 줄의 나머지를 주석으로 만듭니다.",
    question: "한쪽 조건만 참이라면 전체는 어떻게 될까요?",
  },
  filters: {
    title: "내 입력과 서버의 입력이 다를 수 있어요",
    lead: "서버가 값을 바꾸면, 바뀐 값으로 문장이 만들어집니다.",
    example: "username.replace('OR', '')",
    body: "현재 Normal은 기존 MVP의 단순 필터 시나리오입니다. 정확히 일치하는 글자만 지우는 필터는 같은 의미의 다른 표기까지 처리하지 못할 수 있어요. 난이도의 학습 목표는 이 차이를 관찰하는 것입니다.",
    question: "필터 전후에 어떤 글자가 없어졌나요?",
  },
  html: {
    title: "HTML은 글자와 태그를 함께 읽어요",
    lead: "<b>hello</b>는 hello를 굵게 표시하는 태그 예시입니다.",
    example: "<p><b>hello</b></p>",
    body: "입력을 HTML에 그대로 넣으면 글자가 태그로 해석될 수 있습니다. script 태그의 존재와 자바스크립트 실행은 다른 사실입니다. 실행은 태그 문법·코드·브라우저 정책의 영향을 받으므로, 결과 미리보기에서 별도로 관찰해보세요.",
    question: "입력이 화면에 그대로 보이나요, 구조나 표시를 바꾸나요?",
  },
  ownership: {
    title: "식별자와 권한을 구분해보세요",
    lead: "주문번호는 대상을 찾는 값이고, 소유자는 열람 권한을 판단할 정보입니다.",
    example: "order.owner_id == session.user_id",
    body: "서버는 로그인 세션의 사용자와 주문 소유자를 확인해야 합니다. 사용자 요청에 적힌 소유자 번호만 믿으면 그 번호도 바꿀 수 있어요. 이 실습에서는 두 주문과 고정된 교육용 사용자를 비교합니다.",
    question: "서버가 믿는 사용자 정보는 어디에서 왔나요?",
  },
  network:{title:'주소를 따라가는 주체를 확인해요',lead:'서버가 사용자 주소로 요청하면 서버의 네트워크 위치가 기준이 됩니다.',example:'입력 URL → 실제 hostname → 서버 요청 목적지',body:'화면의 주소에 신뢰하는 이름이 들어 있어도 실제 hostname이 다른 곳일 수 있어요. 이 실습은 주소를 파싱해 더미 목적지만 표시하며 DNS·HTTP 요청을 하지 않습니다.',question:'화면에 적힌 이름과 실제 요청 목적지가 같나요?'},
  commands:{title:'명령 이름과 인자를 구분해요',lead:'ls는 목록을 보고 -l은 자세한 정보를 보여주는 옵션입니다.',example:'ls -l /lab',body:'문자열을 셸 명령에 그대로 합치면 구분자 뒤가 또 다른 명령이 될 수 있어요. 이 연습은 정해진 명령 조각과 가상 파일 결과만 해석하며 실제 셸이 아닙니다.',question:'입력은 한 명령의 인자인가요, 다음 명령의 시작인가요?'},
  permissions:{title:'사용자가 달라지면 적용되는 권한도 달라져요',lead:'읽기(r), 쓰기(w), 실행(x) 권한은 소유자·그룹·다른 사용자에게 따로 적용됩니다.',example:'현재 사용자 → 소유자/그룹 비교 → 적용되는 권한 → 허용/거부',body:'Permission denied는 철자 오류가 아니라 접근 권한이 없다는 결과일 수 있어요. 이 모의 실습에서는 잘못 설정된 고정 lab 도우미가 가상 관리자 셸을 여는 상황만 보여줍니다. 실제 sudo나 권한상승을 실행하지 않습니다.',question:'내가 지금 어떤 사용자이며, 어떤 권한으로 이 파일을 읽고 있나요?'},
};
export function labId(category, difficulty) {
  return `${category.replaceAll("_", "-")}-${difficulty}`;
}
export function statusLabel(status) {
  return (
    {
      matched: "조회 결과 있음",
      empty: "반환된 행 없음",
      syntax_error: "문법 오류",
      recognized: "태그 형태 인식",
      unrecognized: "태그 규칙 미충족",
      exposed: "타인 주문 노출",
      own: "본인 주문 조회",
      blocked: "조회 차단",
      missing: "주문 없음",
      fetched:'모의 요청 도달',injected:'추가 명령 감지',command_ok:'가상 명령 처리',unsupported:'지원 범위 밖',permission_denied:'읽기 권한 없음',elevated:'가상 관리자 전환',quiz_correct:'빈칸 목표 충족',quiz_incorrect:'명령을 다시 관찰해요',allowed:'접근 허용',denied:'접근 거부',success:'목표 확인',invalid_input:'입력 형태 확인',normal_input:'일반 입력',public:'공개 목적지',internal:'내부 목적지',simulated:'모의 결과',
    }[status] || "결과 확인"
  );
}
