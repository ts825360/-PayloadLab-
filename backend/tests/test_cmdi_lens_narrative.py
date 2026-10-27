"""Explain only the bounded command model's actual decisions."""
import pytest

from app.labs.practice_extensions import get_extension_trace


def trace(value, medium=False, analysis=False):
    return get_extension_trace('command-injection-medium' if medium else 'command-injection-easy',
                               {'hostname': value}, analysis=analysis)


def story(result):
    return ' '.join(result['lens'][key] for key in ('what', 'why', 'next'))


@pytest.mark.parametrize('medium', [False, True])
def test_plain_host_is_normal_input_not_failed_attack(medium):
    result = trace('example.com', medium)
    text = story(result)
    assert result['execution']['status'] == 'command_ok'
    assert 'ping -c 1 example.com' in text
    assert '일반 입력' in text and '추가 명령은 없' in text
    assert '실제 셸' in text and '네트워크' in text
    assert 'example.com' in result['execution']['stdout']


@pytest.mark.parametrize('command,meaning,output', [
    ('whoami', '사용자 이름', 'webapp'),
    ('pwd', '작업 폴더', '/srv/preview'),
    ('id', '사용자·그룹 번호', 'uid=1001'),
])
@pytest.mark.parametrize('separator,medium', [(';', False), ('&&', False), ('&&', True)])
def test_additional_command_connects_boundary_to_dummy_output(command, meaning, output, separator, medium):
    result = trace(f'example.com {separator} {command}', medium)
    text = story(result)
    assert result['execution']['status'] == 'injected'
    assert f'ping -c 1 example.com {separator} {command}' in text
    assert meaning in text and output in text
    assert '추가 명령' in text and '고정된' in text
    assert ('앞 명령의 성공 여부와 관계없이' if separator == ';' else '앞 명령이 성공했을 때') in text
    if medium:
        assert '&&는' in text and '남아' in text


def test_normal_block_does_not_claim_replacement_or_command_execution():
    result = trace('example.com; whoami', True)
    text = story(result)
    assert result['execution']['status'] == 'blocked'
    assert result['raw_input'] == result['effective_input'] == 'example.com; whoami'
    assert '지우거나 바꾼' in text and '실행하지 않았' in text
    assert 'whoami' in text and 'ping -c 1 example.com; whoami' in text
    assert result['execution']['stdout'] == ''


@pytest.mark.parametrize('value,expected', [
    ('', '비어'), ('   ', '비어'),
    ('example.com;', '뒤에 추가 명령이 없'),
    ('example.com &&', '뒤에 추가 명령이 없'),
    ('example.com || whoami', '||'),
    ('example.com; uname', 'uname'),
    ("example.com'", '지원 범위'),
    ('$(whoami)', '지원 범위'),
    ('example.com; whoami; pwd', '지원 범위'),
])
def test_unsupported_is_not_a_guessed_shell_error(value, expected):
    result = trace(value)
    text = story(result)
    assert result['execution']['status'] == 'unsupported'
    assert expected in text
    assert '실제 셸의 문법 오류' in text and '단정하지 않' in text
    assert '추가 명령을 교육용 모형이 인식했습니다' not in text
    assert '지원 범위' in result['execution']['stderr']
    assert result['execution']['stdout'] == ''


@pytest.mark.parametrize('value,medium', [
    ('example.com', False), ('example.com; whoami', False),
    ('example.com && id', True), ('example.com; pwd', True), ('', False),
])
def test_analysis_keeps_input_and_structure_but_has_no_result(value, medium):
    result = trace(value, medium, True)
    assert result['execution'] is None
    assert result['phase'] == 'analysis'
    assert '실행 전 분석' in result['lens']['what']
    assert '출력을 만들지 않았' in result['lens']['what']
    assert all(node['state'] == 'pending' for node in result['simulation']['nodes'])


def test_focus_uses_original_separator_after_outer_space():
    result = trace('  example.com && pwd  ')
    focus = result['lens']['focus']
    assert result['raw_input'][focus['start']:focus['end']] == '&&'
    assert '공백' in story(result)


def test_normal_focus_points_to_blocking_semicolon_even_after_other_separator():
    value = 'example.com && whoami; pwd'
    result = trace(value, True)
    focus = result['lens']['focus']
    assert result['execution']['status'] == 'blocked'
    assert value[focus['start']:focus['end']] == ';'
    assert result['command_model']['separator'] == '&&'  # First parsed boundary stays intact.


def test_blocked_explanation_distinguishes_stdout_from_visible_policy_error():
    result = trace('example.com; whoami', True)
    assert result['execution']['stdout'] == ''
    assert result['execution']['stderr']
    assert '표준 출력' in result['lens']['what']
    assert '차단 안내' in result['lens']['what']


def test_analysis_next_step_does_not_assume_a_result_already_exists():
    result = trace('example.com && id', True, True)
    assert '실행한 뒤' in result['lens']['next']
