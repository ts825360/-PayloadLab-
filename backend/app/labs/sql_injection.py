import re
import sqlite3
from typing import Callable, Optional

from app.core.lab import (
    FlowEdge,
    FlowNode,
    Lab,
    LabMetadata,
    RuleCheck,
    SuccessDetail,
    TableState,
)

# 실제 취약한 로그인 조회를 흉내내기 위해, 매 시도마다 :memory: SQLite DB를
# 새로 만들고 시드 데이터를 넣습니다. 진짜 쿼리 실행 결과로 성공/실패를
# 판정합니다 (스파이크 단계의 문자열 패턴 매칭과 달리, 실제 DB 엔진을 씀).

_SEED_USERS = [
    (1, "admin", "s3cr3t_password"),
    (2, "guest", "guest123"),
]


def _seed_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    conn.executemany("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", _SEED_USERS)
    conn.commit()
    return conn


def _identity_filter(username: str) -> str:
    return username


def _strip_uppercase_or(username: str) -> str:
    """Medium용 순진한 블랙리스트: 정확히 대문자 OR만 지운다 (Or, oR은 못 잡음)."""
    return username.replace("OR", "")


QUERY_PREFIX = "SELECT * FROM users WHERE username = '"
QUERY_SUFFIX = "' AND password = 'this_is_definitely_wrong'"


def compose_query(filtered: str) -> str:
    return QUERY_PREFIX + filtered + QUERY_SUFFIX


def _run_login_query(username: str, filter_fn: Callable[[str], str]) -> tuple[bool, str, list[tuple]]:
    """공격자는 비밀번호를 모른다고 가정 -- 항상 틀린 비밀번호로 시도."""
    filtered = filter_fn(username)
    conn = _seed_db()
    query = compose_query(filtered)
    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        conn.close()
    return bool(rows), query, rows


_CODE_SNIPPET_EASY = (
    "query = f\"SELECT * FROM users WHERE username = '{username}' \"\n"
    "        \"AND password = '{password}'\"\n"
    "rows = conn.execute(query).fetchall()"
)

_CODE_SNIPPET_MEDIUM = (
    "username = username.replace('OR', '')  # 대문자 OR만 지우는 순진한 필터\n"
    "query = f\"SELECT * FROM users WHERE username = '{username}' \"\n"
    "        \"AND password = '{password}'\"\n"
    "rows = conn.execute(query).fetchall()"
)


def _users_table(matched_indices: list[int]) -> TableState:
    return TableState(
        name="users",
        columns=["id", "username", "password"],
        rows=[[str(u[0]), u[1], u[2]] for u in _SEED_USERS],
        matched_row_indices=matched_indices,
    )


def _build_flow(username: str, filtered: str, query: str, rows: list[tuple], medium: bool):
    """랩마다 실제로 일어난 일 그대로 노드 체인을 구성한다 (공용 4단계 템플릿
    대신, SQLi easy 기준 요구된 7단계: 입력 -> username 변수 -> 문자열 결합
    -> 완성된 쿼리 -> users 테이블 -> 반환된 행 -> 결과. Medium은 필터 적용
    노드가 입력과 username 변수 사이에 하나 더 끼어든다)."""
    matched_indices = [i for i, u in enumerate(_SEED_USERS) if u in rows]

    nodes = [FlowNode(id="input", kind="input", label="사용자 입력값", value=username)]
    edges = []

    if medium:
        nodes.append(FlowNode(
            id="action_filter", kind="action", label="블랙리스트 필터 적용",
            value="정확히 대문자 'OR'만 제거합니다 — 대소문자를 섞으면 그대로 통과합니다.",
            code_line=0,
        ))
        nodes.append(FlowNode(
            id="var_username", kind="variable", label="username 변수 (필터 통과 후)",
            value=filtered, highlight=filtered, code_line=0,
        ))
        concat_line, exec_line = 1, 3
        edges += [
            FlowEdge(source="input", target="action_filter"),
            FlowEdge(source="action_filter", target="var_username"),
        ]
    else:
        nodes.append(FlowNode(
            id="var_username", kind="variable", label="username 변수",
            value=filtered, highlight=filtered, code_line=0,
        ))
        concat_line, exec_line = 0, 2
        edges.append(FlowEdge(source="input", target="var_username"))

    nodes.append(FlowNode(
        id="action_concat", kind="action", label="문자열 결합",
        value="username을 이스케이프 없이 SQL 문자열에 그대로 끼워 넣습니다 (f-string).",
        code_line=concat_line,
    ))
    nodes.append(FlowNode(
        id="var_query", kind="query", label="완성된 SQL Query",
        value=query, highlight=filtered, code_line=concat_line,
    ))
    nodes.append(FlowNode(
        id="table_users", kind="table", label="users 테이블",
        value=f"{len(matched_indices)}개 행 매칭", code_line=exec_line,
        table=_users_table(matched_indices),
    ))
    nodes.append(FlowNode(
        id="var_rows", kind="variable", label="반환된 행",
        value=str(rows), code_line=exec_line,
    ))
    nodes.append(FlowNode(
        id="result", kind="result", label="로그인 우회 성공",
        value="비밀번호를 몰라도 인증을 통과했습니다.",
    ))

    edges += [
        FlowEdge(source="var_username", target="action_concat"),
        FlowEdge(source="action_concat", target="var_query"),
        FlowEdge(source="var_query", target="table_users"),
        FlowEdge(source="table_users", target="var_rows"),
        FlowEdge(source="var_rows", target="result"),
    ]
    return nodes, edges


def _make_resolve(filter_fn: Callable[[str], str], code_snippet: str, medium: bool):
    def _resolve(payload: dict) -> tuple[bool, Optional[SuccessDetail]]:
        username = payload.get("username", "")
        success, query, rows = _run_login_query(username, filter_fn)
        if not success:
            return False, None

        nodes, edges = _build_flow(username, filter_fn(username), query, rows, medium)
        return True, SuccessDetail(flow_nodes=nodes, flow_edges=edges, code_snippet=code_snippet)

    return _resolve


def _has_quote_escape(payload: dict) -> bool:
    return "'" in payload.get("username", "")

def _has_always_true_condition(payload: dict) -> bool:
    username = payload.get("username", "")
    lowered = username.lower()
    return "or" in lowered and ("1'='1" in username or "1=1" in username)

def _has_comment_terminator(payload: dict) -> bool:
    username = payload.get("username", "")
    return "--" in username or "#" in username

def _or_survives_filter(payload: dict) -> bool:
    """필터가 정확한 대문자 OR만 지우므로, 대소문자를 섞으면 살아남는지 확인."""
    filtered = _strip_uppercase_or(payload.get("username", ""))
    return re.search(r"(?i)or", filtered) is not None


sql_injection_easy = Lab(
    metadata=LabMetadata(
        id="sql-injection-easy",
        name="SQL Injection (Easy)",
        category="sql_injection",
        difficulty="easy",
        route="/labs/sql-injection-easy",
    ),
    rules=[
        RuleCheck("quote_escape", "따옴표로 문자열을 탈출하지 못했습니다.", _has_quote_escape),
        RuleCheck("always_true", "따옴표 탈출은 됐지만 항상 참인 조건을 만들지 못했습니다.", _has_always_true_condition),
        RuleCheck("comment_terminator", "조건까지는 맞췄지만 비밀번호 검사를 무력화할 주석이 없습니다.", _has_comment_terminator),
    ],
    resolve=_make_resolve(_identity_filter, _CODE_SNIPPET_EASY, medium=False),
)

sql_injection_medium = Lab(
    metadata=LabMetadata(
        id="sql-injection-medium",
        name="SQL Injection (Medium)",
        category="sql_injection",
        difficulty="medium",
        route="/labs/sql-injection-medium",
    ),
    rules=[
        RuleCheck("quote_escape", "따옴표로 문자열을 탈출하지 못했습니다.", _has_quote_escape),
        RuleCheck("filter_bypass", "필터가 정확히 대문자 OR만 제거합니다. Or, oR처럼 대소문자를 섞어보세요.", _or_survives_filter),
        RuleCheck("always_true", "따옴표 탈출은 됐지만 항상 참인 조건을 만들지 못했습니다.", _has_always_true_condition),
        RuleCheck("comment_terminator", "조건까지는 맞췄지만 비밀번호 검사를 무력화할 주석이 없습니다.", _has_comment_terminator),
    ],
    resolve=_make_resolve(_strip_uppercase_or, _CODE_SNIPPET_MEDIUM, medium=True),
)
