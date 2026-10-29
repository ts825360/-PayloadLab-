import pytest

from app.routes.labs import analyze_lab, attempt_lab


def run(lab, **payload):
    return attempt_lab(lab, payload).learning_trace


@pytest.mark.parametrize('name', ['박태성', ''])
def test_normal_names_explain_value_comparison_and_the_actual_result_window(name):
    data = run('sql-injection-easy', username=name)
    assert data['execution']['status'] == 'empty'
    assert '따옴표' in data['lens']['what']
    assert '문법 오류' in data['lens']['what']
    assert '결과 창' in data['lens']['next']
    assert '오른쪽' not in data['lens']['next']
    assert all(account in data['lens']['what'] for account in ['admin', 'guest'])


def test_sql_success_story_explains_why_guest_is_returned():
    data = run('sql-injection-easy', username="admin' OR '1'='1'--")
    guest = data['row_explanations'][1]
    assert guest['username_matches'] is False
    assert all(text in guest['explanation'] for text in ['admin', 'guest', '거짓', "'1'='1'", '참', 'OR', '반환'])
    assert '2개' in data['lens']['what']
    assert 'OR' in data['lens']['why']


def test_sql_story_keeps_password_precedence_when_no_comment_is_used():
    data = run('sql-injection-easy', username="admin' OR '1'='1")
    assert data['execution']['count'] == 1
    assert '비밀번호' in data['row_explanations'][1]['explanation']
    assert '반환되지' in data['row_explanations'][1]['explanation']
    assert '주석으로 제외' not in data['row_explanations'][1]['explanation']


def test_sql_filter_explains_the_changed_connector_without_predicting_analysis_rows():
    raw = "admin' OR '1'='1'--"
    data = run('sql-injection-medium', username=raw)
    assert data['execution']['status'] == 'syntax_error'
    assert data['effective_input'] in data['lens']['what']
    assert '연결' in data['lens']['why'] and '문법' in data['lens']['why']
    analysis = analyze_lab('sql-injection-medium', {'username': raw})
    assert analysis['execution'] is None
    assert '조회 전' in analysis['lens']['what']


def test_sql_unknown_success_does_not_invent_a_condition_story():
    data = run('sql-injection-easy', username="admin'--")
    assert data['execution']['status'] == 'matched'
    assert data['condition_tree'] is None
    assert 'row_explanations' not in data
    assert '지원 범위' in data['lens']['why']
    assert 'OR' not in data['lens']['why']


@pytest.mark.parametrize('query', ['hello', '<b>hello</b>', '<script>', '<script></script>'])
def test_xss_story_connects_reflection_and_rule_recognition_without_claiming_execution(query):
    data = run('reflected-xss-easy', query=query)
    assert query in data['lens']['what']
    assert '<p>' in data['lens']['what']
    assert data['browser_execution_verified'] is False
    assert '실행' in data['lens']['why']
    assert '결과 창' in data['lens']['next']


def test_xss_filter_shows_both_values_in_the_story():
    raw = '<script>hello</script>'
    data = run('reflected-xss-medium', query=raw)
    assert raw in data['lens']['what']
    assert data['effective_input'] in data['lens']['what']
    analysis = analyze_lab('reflected-xss-medium', {'query': raw})
    assert analysis['execution'] is None
    assert '실행 전' in analysis['lens']['what']


@pytest.mark.parametrize('oid,status,owner', [(1042, 'own', 1042), (1043, 'exposed', 2001), (9999, 'missing', None)])
def test_idor_story_names_the_requested_order_current_user_and_real_outcome(oid, status, owner):
    data = run('idor-easy', requested_id=oid)
    assert data['execution']['status'] == status
    assert str(oid) in data['lens']['what']
    if owner is not None:
        assert str(owner) in data['lens']['what']
        assert '1042' in data['lens']['what']
    assert '반환' in data['lens']['what']
    assert '주문번호' in data['lens']['why']


def test_idor_normal_explains_claim_mismatch_and_avoids_a_fake_session():
    data = run('idor-medium', requested_id=1043, claimed_user_id=1)
    assert data['execution']['status'] == 'blocked'
    assert 'claimed_user_id=1' in data['lens']['what']
    assert '2001' in data['lens']['what']
    assert '반환되지' in data['lens']['what']
    assert '실제 인증' in data['lens']['why']
    analysis = analyze_lab('idor-medium', {'requested_id': 1043, 'claimed_user_id': 2001})
    assert analysis['execution'] is None
    assert '조회 전' in analysis['lens']['what']
    assert '반환됐' not in analysis['lens']['what']
