from typing import Optional

from app.core.lab import FlowEdge, FlowNode, Lab, LabMetadata, RuleCheck, SuccessDetail, TableState

# 로그인한 사용자는 항상 1042번 주문의 소유자라고 가정 (데모용 고정 세션)
_CURRENT_USER_ID = 1042
_ORDER_IDS = [1042, 1043]
_ORDERS = {
    1042: {"owner_id": 1042, "item": "노트북 파우치", "address": "본인 주소"},
    1043: {"owner_id": 2001, "item": "기계식 키보드", "address": "다른 사용자 주소"},
}

_CODE_SNIPPET_EASY = (
    "order = orders.get(requested_id)\n"
    "# owner_id == current_user.id 검사가 없음"
)

_CODE_SNIPPET_MEDIUM = (
    "order = orders.get(requested_id)\n"
    "# 세션이 아니라 요청 파라미터 claimed_user_id를 그대로 신뢰함\n"
    "if payload['claimed_user_id'] == order['owner_id']:\n"
    "    return order"
)


def _requested_someone_elses_resource(payload: dict) -> bool:
    return payload.get("requested_id") != _CURRENT_USER_ID

def _resource_exists(payload: dict) -> bool:
    return payload.get("requested_id") in _ORDERS

def _id_is_guessable(payload: dict) -> bool:
    return isinstance(payload.get("requested_id"), int)

def _claims_correct_owner(payload: dict) -> bool:
    requested_id = payload.get("requested_id")
    if requested_id not in _ORDERS:
        return False
    return payload.get("claimed_user_id") == _ORDERS[requested_id]["owner_id"]


def _orders_table(requested_id: int) -> TableState:
    return TableState(
        name="orders",
        columns=["order_id", "owner_id", "item"],
        rows=[[str(oid), str(_ORDERS[oid]["owner_id"]), _ORDERS[oid]["item"]] for oid in _ORDER_IDS],
        matched_row_indices=[_ORDER_IDS.index(requested_id)],
    )


def _build_flow_easy(requested_id: int) -> tuple[list[FlowNode], list[FlowEdge]]:
    order = _ORDERS[requested_id]
    nodes = [
        FlowNode(
            id="input", kind="input", label="사용자 입력값",
            value=f"주문번호를 {_CURRENT_USER_ID}(본인)에서 {requested_id}(타인)로 변경",
        ),
        FlowNode(
            id="var_requested_id", kind="variable", label="requested_id 변수",
            value=str(requested_id), highlight=str(requested_id), code_line=0,
        ),
        FlowNode(
            id="action_lookup", kind="action", label="딕셔너리 조회",
            value="orders.get(requested_id) — 소유자 확인 없이 바로 조회합니다.",
            code_line=0,
        ),
        FlowNode(
            id="table_orders", kind="table", label="orders 테이블",
            value="1개 행 매칭", code_line=0, table=_orders_table(requested_id),
        ),
        FlowNode(
            id="var_order", kind="variable", label="반환된 레코드",
            value=str(order), code_line=0,
        ),
        FlowNode(
            id="action_missing_check", kind="action", label="소유자 검사 누락",
            value="owner_id == current_user.id 같은 인가 검사가 아예 없습니다.",
            code_line=1,
        ),
        FlowNode(
            id="result", kind="result", label="다른 사용자 정보 노출",
            value=f"타인의 주문 정보를 그대로 열람했습니다: {order}",
        ),
    ]
    edges = [
        FlowEdge(source="input", target="var_requested_id"),
        FlowEdge(source="var_requested_id", target="action_lookup"),
        FlowEdge(source="action_lookup", target="table_orders"),
        FlowEdge(source="table_orders", target="var_order"),
        FlowEdge(source="var_order", target="action_missing_check"),
        FlowEdge(source="action_missing_check", target="result"),
    ]
    return nodes, edges


def _build_flow_medium(requested_id: int, claimed_user_id) -> tuple[list[FlowNode], list[FlowEdge]]:
    order = _ORDERS[requested_id]
    nodes = [
        FlowNode(
            id="input", kind="input", label="사용자 입력값",
            value=f"주문번호 {requested_id} + 소유자 주장(claimed_user_id) {claimed_user_id}",
        ),
        FlowNode(
            id="var_requested_id", kind="variable", label="requested_id 변수",
            value=str(requested_id), highlight=str(requested_id), code_line=0,
        ),
        FlowNode(
            id="action_lookup", kind="action", label="딕셔너리 조회",
            value="orders.get(requested_id)로 먼저 레코드를 가져옵니다.",
            code_line=0,
        ),
        FlowNode(
            id="table_orders", kind="table", label="orders 테이블",
            value="1개 행 매칭", code_line=0, table=_orders_table(requested_id),
        ),
        FlowNode(
            id="var_order", kind="variable", label="반환된 레코드",
            value=str(order), code_line=0,
        ),
        FlowNode(
            id="var_claimed", kind="variable", label="claimed_user_id 변수 (위조된 소유자 주장)",
            value=str(claimed_user_id), highlight=str(claimed_user_id), code_line=2,
        ),
        FlowNode(
            id="action_check", kind="action", label="소유자 검사",
            value="세션이 아니라 요청 파라미터 claimed_user_id를 그대로 믿고 비교합니다 — 공격자가 원하는 값을 직접 채울 수 있습니다.",
            code_line=2,
        ),
        FlowNode(
            id="result", kind="result", label="다른 사용자 정보 노출",
            value=f"위조한 소유자 주장이 그대로 통과해 타인의 주문을 열람했습니다: {order}",
            code_line=3,
        ),
    ]
    edges = [
        FlowEdge(source="input", target="var_requested_id"),
        FlowEdge(source="var_requested_id", target="action_lookup"),
        FlowEdge(source="action_lookup", target="table_orders"),
        FlowEdge(source="table_orders", target="var_order"),
        FlowEdge(source="input", target="var_claimed"),
        FlowEdge(source="var_order", target="action_check"),
        FlowEdge(source="var_claimed", target="action_check"),
        FlowEdge(source="action_check", target="result"),
    ]
    return nodes, edges


def _resolve_easy(payload: dict) -> tuple[bool, Optional[SuccessDetail]]:
    requested_id = payload.get("requested_id")
    if not (_requested_someone_elses_resource(payload) and _resource_exists(payload) and _id_is_guessable(payload)):
        return False, None
    nodes, edges = _build_flow_easy(requested_id)
    return True, SuccessDetail(flow_nodes=nodes, flow_edges=edges, code_snippet=_CODE_SNIPPET_EASY)


def _resolve_medium(payload: dict) -> tuple[bool, Optional[SuccessDetail]]:
    requested_id = payload.get("requested_id")
    if not (
        _requested_someone_elses_resource(payload)
        and _resource_exists(payload)
        and _id_is_guessable(payload)
        and _claims_correct_owner(payload)
    ):
        return False, None
    nodes, edges = _build_flow_medium(requested_id, payload.get("claimed_user_id"))
    return True, SuccessDetail(flow_nodes=nodes, flow_edges=edges, code_snippet=_CODE_SNIPPET_MEDIUM)


idor_easy = Lab(
    metadata=LabMetadata(
        id="idor-easy",
        name="IDOR (Easy)",
        category="idor",
        difficulty="easy",
        route="/labs/idor-easy",
    ),
    rules=[
        RuleCheck("different_resource", "본인 소유 리소스를 요청했습니다. 다른 주문번호로 바꿔서 요청해보세요.", _requested_someone_elses_resource),
        RuleCheck("resource_exists", "존재하지 않는 주문번호입니다.", _resource_exists),
        RuleCheck("guessable_id", "다른 사용자의 리소스를 요청했지만 ID가 정수 형태가 아니라 추측할 수 없습니다.", _id_is_guessable),
    ],
    resolve=_resolve_easy,
)

idor_medium = Lab(
    metadata=LabMetadata(
        id="idor-medium",
        name="IDOR (Medium)",
        category="idor",
        difficulty="medium",
        route="/labs/idor-medium",
    ),
    rules=[
        RuleCheck("different_resource", "본인 소유 리소스를 요청했습니다. 다른 주문번호로 바꿔서 요청해보세요.", _requested_someone_elses_resource),
        RuleCheck("resource_exists", "존재하지 않는 주문번호입니다.", _resource_exists),
        RuleCheck("claims_correct_owner", "이 서버는 세션 대신 요청에 실린 claimed_user_id를 그대로 믿습니다. 그 주문의 실제 소유자 ID로 맞춰서 같이 보내보세요.", _claims_correct_owner),
        RuleCheck("guessable_id", "다른 사용자의 리소스를 요청했지만 ID가 정수 형태가 아니라 추측할 수 없습니다.", _id_is_guessable),
    ],
    resolve=_resolve_medium,
)
