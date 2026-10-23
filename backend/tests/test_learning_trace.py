from app.routes.labs import attempt_lab


def trace(lab, payload):
    return attempt_lab(lab, payload).learning_trace


def test_plain_input_has_actual_query_and_no_matches():
    t = trace('sql-injection-easy', {'username': 'abc'})
    assert t['composition']['value'] == 'abc'
    assert "username = 'abc'" in t['composition']['full']
    assert t['execution']['status'] == 'empty'
    assert not any(row['matched'] for row in t['table']['rows'])
    assert t['lens']['id'] == 'string_value'


def test_syntax_error_is_not_reported_as_empty_query_result():
    t = trace('sql-injection-easy', {'username': "admin'"})
    assert t['execution']['status'] == 'syntax_error'
    assert t['execution']['error']
    assert t['condition_tree'] is None


def test_missing_operator_has_exact_insertion_point_and_reason():
    raw = "admin' '1'='1'--"
    t = trace('sql-injection-easy', {'username': raw})
    assert t['lens']['id'] == 'missing_operator'
    assert t['lens']['focus']['start'] == 6
    assert 'OR' in t['lens']['why']


def test_success_uses_actual_rows_and_condition_tree():
    t = trace('sql-injection-easy', {'username': "admin'OR'1'='1'--"})
    assert t['execution']['status'] == 'matched'
    assert len([r for r in t['table']['rows'] if r['matched']]) == 2
    assert t['condition_tree']['op'] == 'OR'
    assert t['condition_tree']['children'][1]['text'] == "'1'='1'"
    span = t['composition']['ranges']['logic']
    assert t['effective_input'][span['start']:span['end']] == "OR'1'='1'"


def test_no_comment_preserves_and_precedence_and_actual_success():
    t = trace('sql-injection-easy', {'username': "admin' OR '1'='1"})
    assert t['execution']['status'] == 'matched'
    assert t['condition_tree']['children'][1]['op'] == 'AND'
    assert len([r for r in t['table']['rows'] if r['matched']]) == 1
    assert t['lens']['id'] == 'success'


def test_alternative_success_does_not_invent_one_equals_one():
    t = trace('sql-injection-easy', {'username': "' OR 2=2--"})
    assert t['execution']['status'] == 'matched'
    assert t['condition_tree']['children'][1]['text'] == '2=2'


def test_unrecognized_expression_is_not_explained_as_or():
    t = trace('sql-injection-easy', {'username': "admin'--"})
    assert t['execution']['status'] == 'matched'
    assert t['condition_tree'] is None
    assert t['lens']['id'] == 'success'


def test_medium_composition_displays_filtered_input():
    raw = "admin' OR '1'='1' --"
    t = trace('sql-injection-medium', {'username': raw})
    assert t['raw_input'] == raw
    assert 'OR' not in t['composition']['value']
    assert t['lens']['id'] == 'filter_changed'


def test_escaped_quotes_remain_string_not_logic():
    t = trace('sql-injection-easy', {'username': "O''Reilly"})
    assert t['execution']['status'] == 'empty'
    assert t['condition_tree'] is None


def test_xss_trace_reports_recognition_not_execution():
    t = trace('reflected-xss-easy', {'query': '<script></script>'})
    assert t['execution']['status'] == 'recognized'
    assert t['browser_execution_verified'] is False
    assert t['composition']['value'] == '<script></script>'


def test_idor_missing_and_own_resource_are_explained():
    own = trace('idor-easy', {'requested_id': 1042})
    assert own['relations']['owner'] == own['relations']['current_user']
    missing = trace('idor-easy', {'requested_id': 9999})
    assert missing['execution']['status'] == 'missing'
    assert missing['relations']['owner'] is None


def test_idor_normal_failed_claim_does_not_mark_data_returned():
    t = trace('idor-medium', {'requested_id': 1043, 'claimed_user_id': 1})
    assert t['execution']['status'] == 'blocked'
    assert not any(r['matched'] for r in t['table']['rows'])


def test_malformed_payload_keeps_fallback_without_trace_crash():
    result = attempt_lab('sql-injection-easy', {'username': []})
    assert result.success is False
    assert result.learning_trace is None


def test_sql_comment_display_respects_string_boundaries_and_newlines():
    commented = trace('sql-injection-easy', {'username': "admin'--"})
    assert commented['composition']['suffix_commented'] is True
    string_only = trace('sql-injection-easy', {'username': '--'})
    assert string_only['composition']['suffix_commented'] is False
    next_line = trace('sql-injection-easy', {'username': "admin'--\n"})
    assert next_line['composition']['suffix_commented'] is False
    block = trace('sql-injection-easy', {'username': "admin' /* -- */ OR '1'='1"})
    assert block['composition']['suffix_commented'] is False


def test_supported_condition_maps_agree_with_sqlite_rows():
    for name in ['admin', 'guest', 'nobody']:
        for op in ['OR', 'AND']:
            for condition in ['1=1', '1=2', "'x'='x'", "'x'='y'"]:
                for suffix in ['--', '']:
                    raw = f"{name}' {op} {condition}{suffix}"
                    if not suffix:
                        raw = raw[:-1] if condition.endswith("'") else raw
                    t = trace('sql-injection-easy', {'username': raw})
                    if t['condition_tree']:
                        assert t['condition_tree']['values'] == [r['matched'] for r in t['table']['rows']], raw
