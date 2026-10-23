from unittest.mock import patch

from app.routes.labs import analyze_lab
from app.labs import sql_injection
from app.learning_trace import sql_trace


def test_typing_analysis_does_not_run_login_or_claim_rows():
    with patch.object(sql_injection, '_run_login_query', side_effect=AssertionError('must not execute')):
        data = analyze_lab('sql-injection-easy', {'username': "admin' OR '1'='1'--"})
    assert data['phase'] == 'analysis'
    assert data['execution'] is None
    assert data['table'] is None
    assert data['lens']['id'] == 'ready_to_try'
    assert '실행' in data['lens']['next']


def test_typing_missing_operator_retains_focus_and_explanation():
    data = analyze_lab('sql-injection-easy', {'username': "admin' '1'='1'--"})
    assert data['lens']['id'] == 'missing_operator'
    assert data['lens']['focus']['start'] == 6
    assert data['condition_tree'] is None


def test_removing_or_without_spaces_explains_escaped_quotes():
    raw = "admin''1'='1'--"
    data = analyze_lab('sql-injection-easy', {'username': raw})
    assert data['lens']['id'] == 'escaped_quote'
    assert data['lens']['focus'] == {'start': 5, 'end': 7}
    assert 'OR' in data['lens']['next']
    executed = sql_trace(raw, False)
    assert executed['execution']['status'] == 'empty'
    assert not executed['execution']['error']
    assert executed['lens']['id'] == 'escaped_quote'


def test_analysis_invalid_value_and_filter_are_handled():
    assert analyze_lab('sql-injection-easy', {'username': []})['lens']['id'] == 'invalid_input'
    filtered = analyze_lab('sql-injection-medium', {'username': "admin' OR '1'='1'--"})
    assert filtered['lens']['id'] == 'filter_changed'
    assert 'OR' not in filtered['composition']['value']


def test_xss_analysis_does_not_claim_browser_execution():
    data = analyze_lab('reflected-xss-easy', {'query': '<script></script>'})
    assert data['execution'] is None
    assert data['browser_execution_verified'] is False


def test_idor_analysis_does_not_claim_returned_record():
    data = analyze_lab('idor-medium', {'requested_id': 1043, 'claimed_user_id': 2001})
    assert data['execution'] is None
    assert data['table'] is None
    assert 'allowed' not in data['relations']
