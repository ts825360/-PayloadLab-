from app.routes.labs import attempt_lab, analyze_lab


def test_extension_endpoints_return_shared_trace_and_analysis_without_execution():
    for lab_id, payload in (
        ('ssrf-medium', {'target_url': 'http://preview.lab.invalid@127.0.0.1/admin'}),
        ('command-injection-medium', {'hostname': 'example.com && whoami'}),
        ('linux-basics-medium', {'command': 'ls -l /lab'}),
        ('permissions-easy', {'command': 'cat /lab/report.txt'}),
    ):
        result = attempt_lab(lab_id, payload)
        assert result.learning_trace['simulated'] is True
        assert result.learning_trace['execution']['label'] == '교육용 모의 실행'
        analysis = analyze_lab(lab_id, payload)
        assert analysis['phase'] == 'analysis'
        assert analysis['execution'] is None


def test_plain_unregistered_name_explains_comparison_without_calling_it_attack():
    trace = attempt_lab('sql-injection-easy', {'username': '박태성'}).learning_trace
    assert '박태성' in trace['lens']['what']
    assert 'admin' in trace['lens']['what'] and 'guest' in trace['lens']['what']
    assert '공격 실패' not in trace['lens']['what']
    assert trace['row_explanations'][0]['username_matches'] is False
    assert 'AND' in trace['row_explanations'][0]['explanation']
    analysis = analyze_lab('sql-injection-easy', {'username': '박태성'})
    assert analysis.get('row_explanations') is None
