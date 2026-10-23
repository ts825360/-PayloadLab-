import re
from typing import Callable, Optional

from app.core.lab import FlowEdge, FlowNode, Lab, LabMetadata, RuleCheck, SuccessDetail

_SCRIPT_OPEN = re.compile(r"<script", re.IGNORECASE)
_SCRIPT_CLOSE = re.compile(r"</script>", re.IGNORECASE)

_CODE_SNIPPET_EASY = 'return f"<p>\'{query}\'에 대한 검색 결과입니다</p>"'
_CODE_SNIPPET_MEDIUM = (
    "query = query.replace('<script', '')  # 소문자 <script만 지우는 순진한 필터\n"
    'return f"<p>\'{query}\'에 대한 검색 결과입니다</p>"'
)


def _identity_filter(query: str) -> str:
    return query


def _strip_lowercase_script_open(query: str) -> str:
    """Medium용 순진한 블랙리스트: 정확히 소문자 <script만 지운다 (<ScRiPt>는 못 잡음)."""
    return query.replace("<script", "")


def _render_search_page(query: str) -> str:
    # 검색어를 이스케이프 없이 그대로 HTML에 삽입 (의도적으로 취약)
    return f"<p>'{query}'에 대한 검색 결과입니다</p>"


def _make_render(filter_fn: Callable[[str], str]):
    def render_page(payload: dict) -> str:
        """실제 브라우저에서 새로 파싱되는 완전한 HTML 문서.

        프론트엔드가 이걸 <iframe src="...">로 진짜 내비게이션하면, innerHTML
        주입과 달리 <script> 태그가 실제로 실행됩니다 (DVWA와 같은 방식).
        """
        query = filter_fn(payload.get("query", ""))
        body = _render_search_page(query)
        return (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>body{font-family:sans-serif;padding:1rem;background:#fff;color:#111}</style>"
            f"</head><body>{body}</body></html>"
        )

    return render_page


def _has_script_open_raw(payload: dict) -> bool:
    return bool(_SCRIPT_OPEN.search(payload.get("query", "")))

def _has_script_close(payload: dict) -> bool:
    return bool(_SCRIPT_CLOSE.search(payload.get("query", "")))

def _script_open_survives_filter(payload: dict) -> bool:
    filtered = _strip_lowercase_script_open(payload.get("query", ""))
    return bool(_SCRIPT_OPEN.search(filtered))


def _build_flow(raw_query: str, filtered_query: str, medium: bool):
    """SQLi의 7단계 체인과 같은 논리로: 입력 -> query 변수 -> (medium만
    필터) -> HTML 삽입 -> 완성된 HTML -> 브라우저 파싱 -> 스크립트 실행 성공."""
    nodes = [FlowNode(id="input", kind="input", label="사용자 입력값", value=raw_query)]
    edges = []

    if medium:
        nodes.append(FlowNode(
            id="action_filter", kind="action", label="블랙리스트 필터 적용",
            value="정확히 소문자 '<script'만 제거합니다 — 대소문자를 섞으면(<ScRiPt>) 그대로 통과합니다.",
            code_line=0,
        ))
        nodes.append(FlowNode(
            id="var_query", kind="variable", label="query 변수 (필터 통과 후)",
            value=filtered_query, highlight=filtered_query, code_line=0,
        ))
        insert_line = 1
        edges += [
            FlowEdge(source="input", target="action_filter"),
            FlowEdge(source="action_filter", target="var_query"),
        ]
    else:
        nodes.append(FlowNode(
            id="var_query", kind="variable", label="query 변수",
            value=filtered_query, highlight=filtered_query, code_line=0,
        ))
        insert_line = 0
        edges.append(FlowEdge(source="input", target="var_query"))

    body = _render_search_page(filtered_query)
    nodes.append(FlowNode(
        id="action_insert", kind="action", label="HTML 삽입",
        value="이스케이프 없이 그대로 HTML 문자열에 끼워 넣습니다 (f-string).",
        code_line=insert_line,
    ))
    nodes.append(FlowNode(
        id="var_html", kind="query", label="완성된 HTML",
        value=body, highlight=filtered_query, code_line=insert_line,
    ))
    nodes.append(FlowNode(
        id="action_render", kind="action", label="브라우저가 페이지를 파싱",
        value="응답으로 받은 HTML을 그대로 새로 파싱합니다 — 위 실행 결과가 그 화면입니다.",
    ))
    nodes.append(FlowNode(
        id="result", kind="result", label="스크립트 실행 성공",
        value="입력한 <script>가 데이터가 아니라 코드로 실행됩니다.",
    ))

    edges += [
        FlowEdge(source="var_query", target="action_insert"),
        FlowEdge(source="action_insert", target="var_html"),
        FlowEdge(source="var_html", target="action_render"),
        FlowEdge(source="action_render", target="result"),
    ]
    return nodes, edges


def _make_resolve(filter_fn: Callable[[str], str], code_snippet: str, medium: bool):
    def _resolve(payload: dict) -> tuple[bool, Optional[SuccessDetail]]:
        raw_query = payload.get("query", "")
        filtered_query = filter_fn(raw_query)
        success = bool(_SCRIPT_OPEN.search(filtered_query)) and bool(_SCRIPT_CLOSE.search(filtered_query))
        if not success:
            return False, None

        nodes, edges = _build_flow(raw_query, filtered_query, medium)
        return True, SuccessDetail(flow_nodes=nodes, flow_edges=edges, code_snippet=code_snippet)

    return _resolve


reflected_xss_easy = Lab(
    metadata=LabMetadata(
        id="reflected-xss-easy",
        name="Reflected XSS (Easy)",
        category="reflected_xss",
        difficulty="easy",
        route="/labs/reflected-xss-easy",
    ),
    rules=[
        RuleCheck("script_open", "<script> 여는 태그가 없습니다.", _has_script_open_raw),
        RuleCheck("script_close", "여는 태그는 있지만 </script> 닫는 태그가 없어 브라우저가 스크립트로 인식하지 못합니다.", _has_script_close),
    ],
    resolve=_make_resolve(_identity_filter, _CODE_SNIPPET_EASY, medium=False),
    render=_make_render(_identity_filter),
)

reflected_xss_medium = Lab(
    metadata=LabMetadata(
        id="reflected-xss-medium",
        name="Reflected XSS (Medium)",
        category="reflected_xss",
        difficulty="medium",
        route="/labs/reflected-xss-medium",
    ),
    rules=[
        RuleCheck("script_open", "<script> 여는 태그가 없습니다.", _has_script_open_raw),
        RuleCheck("filter_bypass", "필터가 정확히 소문자 <script만 제거합니다. <ScRiPt>처럼 대소문자를 섞어보세요.", _script_open_survives_filter),
        RuleCheck("script_close", "여는 태그는 있지만 </script> 닫는 태그가 없어 브라우저가 스크립트로 인식하지 못합니다.", _has_script_close),
    ],
    resolve=_make_resolve(_strip_lowercase_script_open, _CODE_SNIPPET_MEDIUM, medium=True),
    render=_make_render(_strip_lowercase_script_open),
)
