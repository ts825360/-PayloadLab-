// Completion describes an observation and a checked explanation, not exploit success.
const executed = (category, check) => (trace, result) => Boolean(
  trace?.category === category && trace.phase !== "analysis" && trace.execution && check(trace, result),
);
const status = (category, ...values) => executed(category, (trace) => values.includes(trace.execution.status));
const choice = (value, label) => ({ value, label });
const step = (id, title, instruction, suggestion, observation, accept, quiz = {}) => ({
  id, title, instruction, suggestion, observation, accept, ...quiz,
});
const quiz = (question, answer, choices) => ({ question, answer, choices });
const sqlGuest = executed("sql_injection", (trace) => {
  const tree = trace.condition_tree;
  const comparison = tree?.children?.find((node) => node.id === "comparison");
  return trace.execution.status === "matched" && tree?.op === "OR" &&
    comparison?.values?.length > 0 && comparison.values.every((value) => value === true) &&
    trace.table?.rows?.some((row) => row.matched && row.cells?.includes("guest"));
});
const sqlQuiz = quiz("이름이 다른 guest까지 조회된 이유는 무엇인가요?", "always_true", [
  choice("same_name", "guest의 이름도 admin으로 바뀌었기 때문"),
  choice("always_true", "항상 참인 비교가 OR로 연결되어 guest도 조건을 만족했기 때문"),
  choice("known_password", "비밀번호를 알아냈기 때문"),
]);
const xssQuiz = quiz("태그 형태 인식 결과로 확인한 사실은 무엇인가요?", "recognition_only", [
  choice("executed", "자바스크립트가 실제 브라우저에서 실행되었다"),
  choice("recognition_only", "교육용 태그 규칙을 만족했다. 실제 실행 여부는 따로 관찰해야 한다"),
]);
const ownerQuiz = quiz("주문을 열람할 권한은 무엇으로 확인해야 하나요?", "session_owner", [
  choice("request", "요청에 적힌 사용자 번호만 믿는다"),
  choice("session_owner", "서버가 확인한 로그인 사용자와 주문 소유자를 비교한다"),
]);
const internalTarget = executed("ssrf", (trace) => trace.execution.status === "fetched" && trace.network?.internal === true);
const permissionsCommand = (pattern, statuses = ["command_ok"]) => executed("permissions", (trace) =>
  statuses.includes(trace.execution.status) && pattern.test(trace.terminal?.command || trace.raw_input || ""));

const easy = {
  sql_injection: [
    step("sql-value", "이름을 값으로 조회하기", "admin을 넣고 실행한 뒤, 조립된 SQL의 따옴표와 이름·비밀번호 조건을 찾아보세요.", "admin", "admin 이름 비교가 참이어도 잘못된 비밀번호와 AND로 묶이면 행이 반환되지 않아요.", executed("sql_injection", (trace) => trace.execution.status === "empty" && trace.lens?.id === "string_value")),
    step("sql-boundary", "따옴표 경계 확인하기", "이름 뒤에 작은따옴표 하나를 더하고 실행해보세요. 완성된 SQL과 오류 위치를 비교하세요.", "admin'", "예상한 문법 오류도 관찰 결과예요. 입력의 따옴표가 문자열을 닫으면서 뒤에 붙는 문장과 짝이 달라졌어요.", status("sql_injection", "syntax_error")),
    step("sql-condition", "조건을 만들고 guest 비교하기", "OR 뒤의 비교식과 -- 뒤의 주석을 확인하세요. 실행 후 admin과 guest 각각의 조건을 읽어보세요.", "admin' OR '1'='1'--", "'1'='1'은 계정 이름과 관계없이 참이에요. OR로 연결되고 뒤의 비밀번호 조건이 주석이 되면 guest도 조회될 수 있어요.", sqlGuest, sqlQuiz),
  ],
  reflected_xss: [
    step("xss-text", "입력이 HTML에 들어가는 자리", "일반 검색어를 실행한 뒤 HTML 본문의 <p> 사이에서 입력을 찾아보세요.", "hello", "일반 글자도 서버가 만든 HTML 본문에 삽입돼요. 아직 script 태그 규칙을 만족하지 않은 결과예요.", executed("reflected_xss", (trace) => trace.execution.status === "unrecognized" && trace.lens?.id === "html_text")),
    step("xss-markup", "글자와 표시 태그 비교하기", "표시 태그를 넣고 실행한 뒤 조립된 HTML에서 시작·닫는 태그를 확인하세요. 원할 때 결과 미리보기도 관찰해보세요.", "<b>hello</b>", "<b>는 HTML 표시 구조예요. 태그를 넣었다는 사실과 자바스크립트 코드를 넣었다는 사실은 달라요.", executed("reflected_xss", (trace) => trace.execution.status === "unrecognized" && /<b\b[^>]*>.*<\/b>/is.test(trace.composition?.value || trace.effective_input || ""))),
    step("xss-recognition", "HTML 안의 코드와 실행 구분하기", "script 안의 자바스크립트 문장을 확인하고 실행 결과의 태그 규칙을 읽어보세요.", "<script>alert('hello')</script>", "이번 결과는 태그 형태 인식이며 실제 브라우저의 자바스크립트 실행을 검증하지 않아요. HTML·코드·브라우저 동작을 구분해 관찰하세요.", status("reflected_xss", "recognized"), xssQuiz),
  ],
  idor: [
    step("idor-own", "현재 사용자와 본인 주문 연결하기", "본인 주문을 조회하고 현재 사용자와 주문 소유자 연결을 확인하세요.", "1042", "번호는 조회 대상을 고릅니다. 현재 사용자와 소유자가 같은지 별도로 비교해요.", executed("idor", (trace) => trace.execution.status === "own" && trace.relations?.owner != null && trace.relations?.current_user === trace.relations.owner)),
    step("idor-other", "타인 주문에서 빠진 검사 찾기", "주문번호를 바꾸고 소유자가 달라도 조회되는지 관찰해보세요.", "1043", "다른 사람의 주문번호를 안다고 권한이 생기지 않아요. 소유 관계가 다른데 조회됐다면 서버의 권한 검사가 빠진 거예요.", executed("idor", (trace) => trace.execution.status === "exposed" && trace.relations?.owner != null && trace.relations.owner !== trace.relations.current_user), ownerQuiz),
  ],
  ssrf: [
    step("ssrf-public", "요청의 출발점 확인하기", "공개 URL을 넣고 요청자 → 서버 → 목적지 연결을 살펴보세요.", "https://example.com/", "URL을 전달받은 서버가 목적지에 접근하는 상황을 모의 관찰합니다. 이 실습은 실제 네트워크 요청을 보내지 않아요.", executed("ssrf", (trace) => trace.execution.status === "fetched" && trace.network?.internal === false)),
    step("ssrf-internal", "서버 내부 주소와 비교하기", "목적지를 루프백 주소로 바꾸고 파싱된 호스트와 내부 자원 연결을 비교해보세요.", "http://127.0.0.1/admin", "127.0.0.1은 요청을 처리하는 서버 자신의 루프백 주소예요. 사용자가 고른 URL로 서버가 내부 자원을 읽는 관계를 확인하세요.", internalTarget, quiz("SSRF에서 내부 자원에 접근하는 주체는 누구인가요?", "server", [choice("browser", "사용자의 브라우저"), choice("server", "입력 URL을 처리하는 서버")])),
  ],
  command_injection: [
    step("cmd-host", "호스트 값이 들어가는 자리", "일반 호스트를 넣고 모의 명령의 고정 부분과 입력 부분을 구분해보세요.", "example.com", "호스트는 원래 한 명령의 인자예요. stdout과 교육용 해설은 서로 다른 정보입니다.", status("command_injection", "command_ok")),
    step("cmd-separator", "명령 구분자가 만드는 관계", "호스트 뒤에 구분자와 whoami를 이어 보고 명령 연결과 모의 stdout을 확인하세요.", "example.com; whoami", "구분자를 셸 문법으로 해석하면 입력이 인자에서 별도 명령으로 바뀔 수 있어요. 여기서는 허용된 명령만 모의 처리하며 실제 셸을 실행하지 않아요.", status("command_injection", "injected"), quiz("명령 삽입의 원인은 무엇인가요?", "shell_boundary", [choice("host_length", "호스트 이름이 길어서"), choice("shell_boundary", "입력의 구분자가 명령을 연결하는 셸 문법으로 해석되어서")])),
  ],
  linux_basics: [
    step("linux-command", "명령과 인자를 읽어보기", "퀴즈의 작업 목표를 읽고 파일 목록을 보여줄 명령을 골라보세요. 반환된 퀴즈 결과와 설명을 확인하세요.", "ls", "ls는 디렉터리의 파일 목록을 보여주는 명령이에요. 이 화면은 명령 퀴즈이며 실제 터미널을 실행하지 않아요.", executed("linux_basics", (trace) => trace.execution.status === "quiz_correct" && trace.terminal?.mode === "quiz")),
    step("linux-meaning", "명령에 대상 경로 붙이기", "ls 뒤에 /lab 경로를 붙여 다시 제출하고 명령과 대상 인자를 구분해보세요.", "ls /lab", "명령 이름은 수행할 작업을 정하고 인자·옵션은 대상을 구체화해요. 퀴즈 정답과 실제 파일 시스템의 상태는 구분해야 해요.", executed("linux_basics", (trace) => trace.execution.status === "quiz_correct" && trace.terminal?.mode === "quiz" && /^\s*ls\s+\/lab\s*$/.test(trace.terminal?.command || trace.raw_input || "")), quiz("ls /lab에서 /lab은 무엇인가요?", "directory", [choice("password", "현재 계정의 비밀번호"), choice("directory", "목록을 확인할 대상 디렉터리")])),
  ],
  permissions: [
    step("perm-user", "현재 사용자 확인하기", "whoami를 실행하고 모의 프롬프트의 사용자와 출력값을 비교하세요.", "whoami", "파일 접근은 현재 사용자 권한을 따릅니다. 이 실습은 학생 계정에서 시작하는 모의 환경이에요.", permissionsCommand(/^\s*whoami\s*$/)),
    step("perm-file", "파일 소유자와 권한 읽기", "ls -l로 파일의 소유자와 r·w·x 권한을 확인하세요.", "ls -l /lab/report.txt", "r은 읽기, w는 쓰기, x는 실행이에요. 파일 소유자와 현재 사용자를 비교하면 접근 실패의 이유를 찾을 수 있어요.", permissionsCommand(/^\s*ls\s+-l(?:\s+\/lab\/report\.txt)?\s*$/)),
    step("perm-denied", "읽기 거부도 증거로 관찰하기", "보호된 보고서 읽기를 시도하고 stderr와 종료 상태를 확인하세요.", "cat /lab/report.txt", "permission denied는 파일이 없다는 뜻과 달라요. 현재 학생 계정의 읽기 권한이 부족한 결과입니다.", status("permissions", "permission_denied")),
    step("perm-rule", "허용된 sudo 규칙 찾기", "sudo -l 결과에서 허용된 명령을 확인하세요.", "sudo -l", "sudo 권한은 허용된 명령 범위로 읽어야 해요. 여기서는 교육용 유지보수 도우미 한 개만 허용됩니다.", permissionsCommand(/^\s*sudo\s+-l\s*$/)),
    step("perm-elevated", "허용 도우미와 사용자 변화 연결하기", "허용된 도우미를 실행하고 프롬프트·현재 사용자·권한 연결이 바뀌는지 확인하세요.", "sudo /lab/maintenance", "이 모의 도우미는 root로 전환되는 취약한 권한 구성을 보여줘요. 실제 운영체제의 권한이나 파일은 바뀌지 않아요.", executed("permissions", (trace) => trace.execution.status === "elevated" && trace.terminal?.current_user === "root"), quiz("이 실습에서 root로 바뀐 근거는 무엇인가요?", "allowed_helper", [choice("typed_root", "입력에 root라는 글자를 썼기 때문"), choice("allowed_helper", "sudo 규칙의 허용 도우미를 실행해 모의 사용자 상태가 바뀌었기 때문")])),
  ],
};

const normal = {
  sql_injection: [
    step("sql-filter", "새 조건: 입력을 바꾸는 필터", "목표: 대문자 OR를 지우는 필터가 SQL 조립에 미치는 영향을 확인하세요. 원본과 서버 입력을 비교할 시도를 직접 만들어보세요.", "admin' OR '1'='1'--", "대문자 문자열 제거는 SQL의 의미를 판단하지 않아요. 필터 이후 문장과 오류를 먼저 읽어보세요.", executed("sql_injection", (trace) => trace.raw_input !== trace.effective_input && trace.lens?.id === "filter_changed")),
    step("sql-apply", "다른 표기로 조건 적용하기", "목표: 필터의 비교 방식과 SQL의 해석 차이를 이용해 guest까지 참인 조건을 만들고 설명하세요.", "admin' or 2=2--", "반환된 행과 OR의 각 비교값을 대조하세요. 특정 예시와 같은 입력인지보다 실제 조건이 무엇인지가 중요해요.", sqlGuest, sqlQuiz),
  ],
  reflected_xss: [
    step("xss-filter", "새 조건: 단순 태그 필터", "목표: 소문자 <script를 지우는 필터 전후를 비교하세요. 어떤 문자열을 비교하는지 직접 확인해보세요.", "<script>alert('hello')</script>", "HTML은 태그를 해석하고 서버의 단순 필터는 일부 문자열만 지워요. 원본과 HTML에 남은 값을 비교하세요.", executed("reflected_xss", (trace) => trace.raw_input !== trace.effective_input && trace.lens?.id === "filter_changed")),
    step("xss-apply", "태그 표기와 실행 범위 설명하기", "목표: 필터와 HTML의 해석 차이를 확인할 표기를 만들고 태그 규칙 결과를 설명하세요.", "<SCRIPT>alert('hello')</SCRIPT>", "형태 인식 결과는 실제 자바스크립트 실행 검증이 아니에요. 미리보기에서 관찰한 사실도 구분해 기록하세요.", status("reflected_xss", "recognized"), xssQuiz),
  ],
  idor: [
    step("idor-claim", "새 조건: 요청의 소유자 주장", "목표: 타인 주문을 보호하는 듯한 검사가 무엇을 믿는지 찾아보세요. 주문번호와 claimed_user_id를 각각 바꿔 비교하세요.", "1043", "단서: 주문 소유자와 요청의 claimed_user_id가 같을 때 허용되는지 살펴보세요. 요청 값은 로그인 세션이 아니에요.", executed("idor", (trace) => trace.execution.status === "exposed" && trace.relations?.medium === true && trace.relations?.claimed_user === trace.relations?.owner && trace.relations?.owner !== trace.relations?.current_user), ownerQuiz),
  ],
  ssrf: [
    step("ssrf-apply", "새 조건: 신뢰 주소 문자열 검사", "목표: 주소에 신뢰 문자열이 있다는 사실과 실제 목적지 호스트가 같은지 비교하고 내부 자원에 도달하는 구성을 찾아보세요.", "http://preview.lab.invalid@127.0.0.1/admin", "URL 전체의 부분 문자열과 파싱된 hostname은 달라요. URL의 사용자 정보·호스트 경계를 살펴보세요.", internalTarget, quiz("목적지 검사는 어떤 정보를 기준으로 해야 하나요?", "parsed_host", [choice("substring", "전체 문자열에 신뢰 단어가 들어가는지"), choice("parsed_host", "파싱한 실제 호스트와 접근 가능한 주소 범위")])),
  ],
  command_injection: [
    step("cmd-apply", "새 조건: 한 구분자만 검사", "목표: 세미콜론 검사 뒤에도 명령을 연결할 수 있는지 모의 명령 구성과 stdout으로 확인하세요.", "example.com && whoami", "입력에 ;가 있으면 전체 처리를 차단하며 문자를 제거하지는 않아요. 다른 연결 기호도 검사하는지 허용된 교육용 명령과 구분자 범위 안에서 비교하세요.", status("command_injection", "injected"), quiz("세미콜론 하나를 막으면 충분할까요?", "other_syntax", [choice("enough", "네, 명령 연결 문법은 하나뿐이에요"), choice("other_syntax", "아니요, 다른 연결 문법도 있으므로 인자를 셸 코드와 분리해야 해요")])),
  ],
  linux_basics: [
    step("linux-apply", "새 목표에 맞는 옵션 적용하기", "목표: 퀴즈의 새 작업에 맞는 명령과 옵션을 선택하세요. 옵션이 결과에 더하는 정보를 설명해보세요.", "ls -l /lab", "단서: 긴 목록 형식은 파일 권한·소유자 등의 정보를 함께 보여줘요. 실제 파일은 조회하지 않는 명령 퀴즈입니다.", executed("linux_basics", (trace) => trace.execution.status === "quiz_correct" && trace.terminal?.mode === "quiz"), quiz("ls -l의 -l은 어떤 역할인가요?", "long", [choice("delete", "파일을 삭제한다"), choice("long", "권한과 소유자 등이 포함된 긴 목록 형식을 고른다")])),
  ],
};

export function getLesson(categoryId, difficulty) {
  const isNormal = difficulty === "medium" || difficulty === "normal";
  if (!["easy", "medium", "normal"].includes(difficulty)) return null;
  const steps = (isNormal ? normal : easy)[categoryId];
  if (!steps) return null;
  return {
    title: isNormal ? "Normal · 스스로 적용하기" : "Easy · 따라 하며 이해하기",
    summary: isNormal ? "목표를 보고 직접 시도하세요. 막히면 단서를 열어 편집할 입력 예시를 볼 수 있어요." : "입력을 만들고 실행한 뒤, 코드와 결과에서 관찰한 내용을 확인하며 진행해요.",
    difficulty: isNormal ? "medium" : "easy",
    steps,
  };
}
