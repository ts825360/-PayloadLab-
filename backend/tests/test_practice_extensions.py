"""Contract tests for the deliberately bounded, in-memory educational adapters."""
import importlib
import importlib.util

import pytest


def extension_module():
    assert importlib.util.find_spec('app.labs.practice_extensions'), 'extension adapters are missing'
    return importlib.import_module('app.labs.practice_extensions')


def trace(lab_id, payload, **kwargs):
    return extension_module().get_extension_trace(lab_id, payload, **kwargs)


def test_seven_extensions_are_registered_without_permissions_medium():
    from app.labs import REGISTRY
    expected = {'ssrf-easy', 'ssrf-medium', 'command-injection-easy',
                'command-injection-medium', 'linux-basics-easy',
                'linux-basics-medium', 'permissions-easy'}
    assert {lab.metadata.id for lab in extension_module().EXTENSION_LABS} == expected
    assert expected <= REGISTRY.keys()
    assert 'permissions-medium' not in REGISTRY
    assert trace('permissions-medium', {'command': 'whoami'}) is None


@pytest.mark.parametrize('url,internal', [
    ('https://example.com/news', False), ('http://127.0.0.1/admin', True),
    ('http://localhost/admin', True), ('http://[::1]/admin', True),
])
def test_ssrf_distinguishes_parsed_public_and_loopback_destinations(url, internal):
    result = trace('ssrf-easy', {'target_url': url})
    assert result['execution']['status'] == 'fetched'
    assert result['network']['internal'] is internal
    assert result['network']['requested'] is False
    assert result['simulated'] is True
    lab = next(lab for lab in extension_module().EXTENSION_LABS if lab.metadata.id == 'ssrf-easy')
    assert lab.attempt({'target_url': url}).success is internal


def test_ssrf_medium_incomplete_string_policy_separates_authority_hostname():
    blocked = trace('ssrf-medium', {'target_url': 'http://127.0.0.1/admin'})
    bypass = trace('ssrf-medium', {'target_url': 'http://preview.lab.invalid@127.0.0.1/admin'})
    assert blocked['execution']['status'] == 'blocked'
    assert bypass['execution']['status'] == 'fetched'
    assert bypass['network']['hostname'] == '127.0.0.1'
    assert bypass['network']['internal'] is True
    assert '문자열' in bypass['lens']['why']


@pytest.mark.parametrize('url', ['file:///etc/passwd', 'not a url', 'http://[broken', 'https://x:bad'])
def test_ssrf_malformed_and_non_http_urls_are_diagnostic(url):
    result = trace('ssrf-easy', {'target_url': url})
    assert result['execution']['status'] == 'unsupported'
    assert result['execution']['count'] == 0


@pytest.mark.parametrize('lab_id,value,status,expected', [
    ('command-injection-easy', 'example.com', 'command_ok', 'PING'),
    ('command-injection-easy', 'example.com; whoami', 'injected', 'webapp'),
    ('command-injection-easy', 'example.com && pwd', 'injected', '/srv/preview'),
    ('command-injection-medium', 'example.com; whoami', 'blocked', ''),
    ('command-injection-medium', 'example.com && id', 'injected', 'uid=1001'),
    ('command-injection-easy', 'example.com; rm -rf /', 'unsupported', ''),
    ('command-injection-easy', '$(whoami)', 'unsupported', ''),
])
def test_command_injection_models_only_supported_tokens(lab_id, value, status, expected):
    result = trace(lab_id, {'hostname': value})
    assert result['execution']['status'] == status
    assert expected in result['execution']['stdout']
    assert result['execution']['label'] == '교육용 모의 실행'


@pytest.mark.parametrize('lab_id,command,correct', [
    ('linux-basics-easy', 'ls', True), ('linux-basics-easy', 'ls /lab', True),
    ('linux-basics-easy', 'cat /lab', False),
    ('linux-basics-medium', 'ls -l /lab', True),
    ('linux-basics-medium', 'ls /lab', False),
])
def test_linux_basics_is_explicitly_a_token_quiz(lab_id, command, correct):
    result = trace(lab_id, {'command': command})
    assert result['execution']['status'] == ('quiz_correct' if correct else 'quiz_incorrect')
    assert result['terminal']['mode'] == 'quiz'
    assert result['terminal']['simulated'] is True


def test_permission_denial_is_not_an_unknown_command():
    result = trace('permissions-easy', {'command': 'cat /lab/report.txt'})
    assert result['execution']['status'] == 'permission_denied'
    assert 'Permission denied' in result['terminal']['stderr']
    assert result['terminal']['current_user'] == 'student'
    assert result['terminal']['files'][0]['permissions'] == '-rw-------'


def test_permission_history_replays_only_virtual_helper_and_exit():
    helper = trace('permissions-easy', {'command': 'sudo -l'})
    assert 'sudo /lab/maintenance' in helper['terminal']['stdout']
    elevated = trace('permissions-easy', {'command': 'sudo /lab/maintenance'})
    assert elevated['execution']['status'] == 'elevated'
    assert elevated['terminal']['current_user'] == 'root'
    history = ['whoami', 'sudo -l', 'sudo /lab/maintenance']
    result = trace('permissions-easy', {'command': 'cat /lab/report.txt', 'history': history})
    assert result['terminal']['stdout'] == 'training-report\n'
    assert result['terminal']['current_user'] == 'root'
    exited = trace('permissions-easy', {'command': 'whoami', 'history': history + ['exit']})
    assert exited['terminal']['stdout'] == 'student\n'
    assert '인위적' in elevated['lens']['why']


def test_permission_client_privilege_flags_cannot_elevate_or_read_report():
    result = trace('permissions-easy', {'command': 'cat /lab/report.txt',
                   'state': {'current_user': 'root'}, 'user': 'root', 'root': True})
    assert result['execution']['status'] == 'permission_denied'


@pytest.mark.parametrize('history', [None, 'sudo /lab/maintenance', [None],
    ['sudo /lab/maintenance'] * 41, ['x' * 2001],
    ['sudo /lab/maintenance', 'chmod 777 /lab/report.txt']])
def test_invalid_or_unbounded_histories_do_not_change_privilege(history):
    result = trace('permissions-easy', {'command': 'whoami', 'history': history})
    assert result['execution']['status'] == 'unsupported'
    assert result['terminal']['current_user'] == 'student'


@pytest.mark.parametrize('payload', [None, [], {'command': {}}, {'command': 'x' * 2001}])
def test_malformed_inputs_are_bounded_diagnostics(payload):
    result = trace('permissions-easy', payload)
    assert result['execution']['status'] == 'unsupported'
    assert len(result['raw_input']) <= 2000


def test_oversized_command_cannot_leave_a_successful_graph_or_privilege_transition():
    result = trace('permissions-easy', {'command': 'sudo /lab/maintenance' + ' ' * 2001})
    assert result['execution']['status'] == 'unsupported'
    assert not any(node['state'] == 'elevated' for node in result['simulation']['nodes'])
    assert result['terminal']['current_user'] == 'student'


@pytest.mark.parametrize('lab_id,payload', [
    ('ssrf-medium', {'target_url': 'http://preview.lab.invalid@127.0.0.1/admin'}),
    ('command-injection-easy', {'hostname': 'example.com; whoami'}),
    ('command-injection-medium', {'hostname': 'example.com && id'}),
    ('linux-basics-easy', {'command': 'ls /lab'}),
    ('linux-basics-medium', {'command': 'ls -l /lab'}),
    ('permissions-easy', {'command': 'cat /lab/report.txt', 'history': ['sudo /lab/maintenance']}),
])
def test_registered_lab_oracles_accept_only_observed_exercise_goal(lab_id, payload):
    from app.labs import get_lab
    result = get_lab(lab_id).attempt(payload)
    assert result.success is True
    assert result.flow_nodes == []
    assert '교육용' in result.code_snippet


def test_permission_helper_alone_does_not_complete_report_observation_goal():
    from app.labs import get_lab
    assert get_lab('permissions-easy').attempt({'command': 'sudo /lab/maintenance'}).success is False


@pytest.mark.parametrize('lab_id,payload', [
    ('ssrf-easy', {'target_url': 'http://127.0.0.1/admin'}),
    ('command-injection-easy', {'hostname': 'example.com; whoami'}),
    ('linux-basics-easy', {'command': 'ls /lab'}),
    ('permissions-easy', {'command': 'sudo /lab/maintenance'}),
])
def test_analysis_has_no_execution_or_future_terminal_state(lab_id, payload):
    result = trace(lab_id, payload, analysis=True)
    assert result['phase'] == 'analysis'
    assert result['execution'] is None
    assert result['table'] is None
    assert all(node['state'] == 'pending' for node in result['simulation']['nodes'])
    if result.get('terminal'):
        assert result['terminal']['stdout'] == result['terminal']['stderr'] == ''
        if lab_id == 'permissions-easy':
            assert result['terminal']['current_user'] == 'student'


def test_permission_analysis_uses_only_prior_history_and_keeps_model_pure():
    payload = {'command': 'exit', 'history': ['sudo /lab/maintenance']}
    result = trace('permissions-easy', payload, analysis=True)
    assert result['terminal']['current_user'] == 'root'
    assert result['terminal']['prompt'].endswith('# ')
    assert payload == {'command': 'exit', 'history': ['sudo /lab/maintenance']}
    assert trace('permissions-easy', {'command': 'whoami'})['terminal']['current_user'] == 'student'


def test_permissions_unknown_commands_are_explicitly_unsupported():
    result = trace('permissions-easy', {'command': 'sudo cat /etc/shadow'})
    assert result['execution']['status'] == 'unsupported'
    assert result['execution']['exit_code'] != 0
    assert '지원' in result['lens']['what']


def test_all_extension_envelopes_supply_composition_ranges_and_graphs():
    for lab in extension_module().EXTENSION_LABS:
        field = {'ssrf': 'target_url', 'command_injection': 'hostname'}.get(lab.metadata.category, 'command')
        result = trace(lab.metadata.id, {field: 'hello'})
        assert result['composition']['ranges']['input'] == {'start': 0, 'end': 5}
        assert result['simulation']['nodes'] and result['simulation']['edges']
        assert set(result['lens']) >= {'id', 'title', 'what', 'why', 'next', 'focus', 'lesson'}

