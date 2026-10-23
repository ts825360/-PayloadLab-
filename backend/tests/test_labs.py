"""#10 Lens 회귀 테스트 스위트.

각 랩의 known payload -> 기대 결과(성공/실패 및 어느 규칙에서 멈추는지)를
고정해둔다. 팀원이 #14~#16 작업으로 backend/app/labs/*.py 안의 description/
note 문자열을 고치다가 실수로 로직(정규식, 필터 등)까지 건드리면 여기서
바로 잡힌다.
"""

from app.labs import REGISTRY, sql_injection, reflected_xss, idor


def test_all_mvp_labs_registered():
    expected_ids = {
        "sql-injection-easy", "sql-injection-medium",
        "reflected-xss-easy", "reflected-xss-medium",
        "idor-easy", "idor-medium",
    }
    assert expected_ids <= REGISTRY.keys()


# ---------------------------------------------------------------- SQL Injection

def test_sqli_easy_success():
    result = sql_injection.sql_injection_easy.attempt({"username": "admin' OR '1'='1' --"})
    assert result.success is True
    table_node = next(n for n in result.flow_nodes if n.kind == "table")
    assert table_node.table.matched_row_indices  # 최소 한 행은 매칭됨


def test_sqli_easy_fails_at_quote_escape():
    result = sql_injection.sql_injection_easy.attempt({"username": "admin"})
    assert result.success is False
    assert result.lens_rule_id == "quote_escape"
    assert result.lens_passed_count == 0


def test_sqli_easy_fails_at_always_true():
    result = sql_injection.sql_injection_easy.attempt({"username": "admin'"})
    assert result.success is False
    assert result.lens_rule_id == "always_true"
    assert result.lens_passed_count == 1


def test_sqli_easy_fails_at_comment_terminator():
    # 'admin' 자체가 실존 유저라 "admin' OR ..."는 주석 없이도 성공해버린다
    # (OR 왼쪽만으로 매칭됨 -- 실제 실행 오라클의 정확성을 보여준 사례,
    # #9 스파이크에서도 같은 걸 확인함). 그래서 존재하지 않는 유저로 테스트.
    result = sql_injection.sql_injection_easy.attempt({"username": "nonexistent' OR '1'='1"})
    assert result.success is False
    assert result.lens_rule_id == "comment_terminator"
    assert result.lens_passed_count == 2


def test_sqli_easy_malformed_input_falls_back_instead_of_crashing():
    result = sql_injection.sql_injection_easy.attempt({"username": 12345})
    assert result.success is False
    assert result.lens_rule_id == "fallback_unrecognized_input"


def test_sqli_medium_easy_style_payload_now_fails_at_filter():
    """Easy에서 통했던 정확한 대문자 OR가 Medium에서는 필터에 걸린다."""
    result = sql_injection.sql_injection_medium.attempt({"username": "admin' OR '1'='1' --"})
    assert result.success is False
    assert result.lens_rule_id == "filter_bypass"
    assert result.lens_passed_count == 1


def test_sqli_medium_case_varied_bypass_succeeds():
    result = sql_injection.sql_injection_medium.attempt({"username": "admin' oR '1'='1' --"})
    assert result.success is True


def test_sqli_medium_fails_at_always_true_after_surviving_filter():
    result = sql_injection.sql_injection_medium.attempt({"username": "admin' or"})
    assert result.success is False
    assert result.lens_rule_id == "always_true"
    assert result.lens_passed_count == 2


def test_sqli_medium_fails_at_comment_terminator():
    result = sql_injection.sql_injection_medium.attempt({"username": "nonexistent' or '1'='1"})
    assert result.success is False
    assert result.lens_rule_id == "comment_terminator"
    assert result.lens_passed_count == 3


# ---------------------------------------------------------------- Reflected XSS

def test_xss_easy_success():
    result = reflected_xss.reflected_xss_easy.attempt({"query": "<script>alert(1)</script>"})
    assert result.success is True


def test_xss_easy_fails_at_script_open():
    result = reflected_xss.reflected_xss_easy.attempt({"query": "hello"})
    assert result.success is False
    assert result.lens_rule_id == "script_open"


def test_xss_easy_fails_at_script_close():
    result = reflected_xss.reflected_xss_easy.attempt({"query": "<script>alert(1)"})
    assert result.success is False
    assert result.lens_rule_id == "script_close"


def test_xss_easy_malformed_input_falls_back_instead_of_crashing():
    result = reflected_xss.reflected_xss_easy.attempt({"query": 12345})
    assert result.success is False
    assert result.lens_rule_id == "fallback_unrecognized_input"


def test_xss_medium_easy_style_payload_now_fails_at_filter():
    result = reflected_xss.reflected_xss_medium.attempt({"query": "<script>alert(1)</script>"})
    assert result.success is False
    assert result.lens_rule_id == "filter_bypass"


def test_xss_medium_case_varied_bypass_succeeds_and_renders():
    result = reflected_xss.reflected_xss_medium.attempt({"query": "<ScRiPt>alert(1)</script>"})
    assert result.success is True
    # 실제 실행 경로(render)도 필터가 살아있는 태그를 그대로 통과시키는지 확인
    html = reflected_xss.reflected_xss_medium.render({"query": "<ScRiPt>alert(1)</script>"})
    assert "<ScRiPt>alert(1)</script>" in html


def test_xss_medium_fails_at_script_close_after_surviving_filter():
    result = reflected_xss.reflected_xss_medium.attempt({"query": "<ScRiPt>alert(1)"})
    assert result.success is False
    assert result.lens_rule_id == "script_close"


# ---------------------------------------------------------------- IDOR

def test_idor_easy_success():
    result = idor.idor_easy.attempt({"requested_id": 1043})
    assert result.success is True


def test_idor_easy_fails_at_different_resource():
    result = idor.idor_easy.attempt({"requested_id": 1042})
    assert result.success is False
    assert result.lens_rule_id == "different_resource"


def test_idor_easy_fails_at_resource_exists():
    result = idor.idor_easy.attempt({"requested_id": 9999})
    assert result.success is False
    assert result.lens_rule_id == "resource_exists"


def test_idor_easy_malformed_input_does_not_crash():
    """resource_exists가 unhashable 타입에 dict `in`을 쓰므로 TypeError 유발."""
    result = idor.idor_easy.attempt({"requested_id": ["not", "hashable"]})
    assert result.success is False
    assert result.lens_rule_id == "fallback_unrecognized_input"


def test_idor_easy_guessable_id_rule_is_currently_unreachable_as_a_failure():
    """알려진 한계: _ORDERS 키가 전부 int라서, resource_exists를 통과하는
    값은 이미 int일 수밖에 없다 -- guessable_id가 첫 실패 지점이 되는
    입력이 존재하지 않는다. 규칙 자체는 체인에 등록돼 있는지만 확인한다."""
    rule_ids = [r.id for r in idor.idor_easy.rules]
    assert "guessable_id" in rule_ids
    assert rule_ids.index("guessable_id") == len(rule_ids) - 1


def test_idor_medium_success_requires_claimed_owner():
    result = idor.idor_medium.attempt({"requested_id": 1043, "claimed_user_id": 2001})
    assert result.success is True


def test_idor_medium_fails_without_correct_claim():
    result = idor.idor_medium.attempt({"requested_id": 1043, "claimed_user_id": 1})
    assert result.success is False
    assert result.lens_rule_id == "claims_correct_owner"


# ---------------------------------------------------------------- flow_nodes/flow_edges shape

def test_all_success_flows_have_consistent_node_ids_and_code_lines():
    """코드<->그래프 양방향 강조 UI가 의존하는 데이터 계약: edge가 가리키는
    노드가 실제로 존재하고, code_line이 code_snippet 범위 안에 있어야 한다.
    수기로 적은 code_line 오프셋이 코드와 어긋나면 여기서 잡힌다."""
    cases = [
        (sql_injection.sql_injection_easy, {"username": "admin' OR '1'='1' --"}),
        (sql_injection.sql_injection_medium, {"username": "admin' oR '1'='1' --"}),
        (reflected_xss.reflected_xss_easy, {"query": "<script>alert(1)</script>"}),
        (reflected_xss.reflected_xss_medium, {"query": "<ScRiPt>alert(1)</script>"}),
        (idor.idor_easy, {"requested_id": 1043}),
        (idor.idor_medium, {"requested_id": 1043, "claimed_user_id": 2001}),
    ]
    for lab, payload in cases:
        result = lab.attempt(payload)
        assert result.success is True, lab.metadata.id
        node_ids = [n.id for n in result.flow_nodes]
        assert len(node_ids) == len(set(node_ids)), lab.metadata.id  # 중복 id 없음

        for edge in result.flow_edges:
            assert edge.source in node_ids, lab.metadata.id
            assert edge.target in node_ids, lab.metadata.id

        line_count = len(result.code_snippet.split("\n"))
        for node in result.flow_nodes:
            if node.code_line is not None:
                assert 0 <= node.code_line < line_count, (lab.metadata.id, node.id)
