"""The Linux exercise grades token lists; it never executes a shell."""
import pytest

from app.labs.practice_extensions import get_extension_trace


def trace(value, medium=False, analysis=False):
    return get_extension_trace('linux-basics-medium' if medium else 'linux-basics-easy',
                               {'command': value}, analysis=analysis)


def story(result):
    return ' '.join(result['lens'][key] for key in ('what', 'why', 'next'))


@pytest.mark.parametrize('value', ['ls', 'ls /lab', '  ls\t/lab  '])
def test_easy_names_are_tied_to_virtual_directory_and_actual_output(value):
    result = trace(value)
    assert result['execution']['status'] == 'quiz_correct'
    text = story(result)
    for phrase in ['/lab', 'report.txt', 'readme.txt', '이름', '실제 셸', '공백']:
        assert phrase in text
    assert result['quiz']['tokens'] == value.split()
    assert '현재 가상 폴더' in text


def test_normal_explains_each_column_as_simplified_example():
    result = trace('ls -l /lab', True)
    assert result['execution']['status'] == 'quiz_correct'
    text = story(result)
    for phrase in ['ls', '-l', '/lab', '소유자', '권한', 'mentor', 'student', '간략']:
        assert phrase in text
    assert result['quiz']['comparison'] == 'matched'


@pytest.mark.parametrize('value,medium,reason', [
    ('', False, '비어'), ('   ', True, '비어'),
    ('ls', True, '-l'), ('ls /lab', True, '-l'),
    ('ls -l', True, '/lab'), ('ls -l /lab', False, '이름만'),
    ('ls /lab -l', True, '순서'), ('ls /tmp', False, '/tmp'),
    ('ls -l /tmp', True, '/tmp'),
])
def test_known_difference_explains_quiz_mismatch_not_linux_error(value, medium, reason):
    result = trace(value, medium)
    text = story(result)
    assert result['execution']['status'] == 'quiz_incorrect'
    assert result['quiz']['comparison'] == ('empty' if not value.strip() else 'goal_mismatch')
    assert reason in text
    assert '실제 Linux의 오류' in text
    assert result['execution']['stdout'] == ''
    assert '퀴즈' in result['execution']['stderr']


@pytest.mark.parametrize('value', ['pwd', 'cat /lab', "ls '/lab'", 'ls -al /lab',
                                      'ls; pwd', '박태성', '😀', 'ls && pwd'])
def test_unmodeled_form_does_not_invent_shell_interpretation(value):
    result = trace(value)
    assert result['quiz']['comparison'] == 'unmodeled'
    assert '지원 범위' in story(result)
    assert '실제 Linux의 오류' in story(result)
    assert 'command not found' not in story(result)
    assert result['execution']['stdout'] == ''


@pytest.mark.parametrize('value,medium', [('ls', False), ('ls /lab', True), ('pwd', False)])
def test_analysis_does_not_grade_or_generate_a_listing(value, medium):
    result = trace(value, medium, True)
    assert result['execution'] is None
    assert result['lens']['id'] == 'quiz_pending'
    assert '아직 채점하지 않았' in result['lens']['what']
    assert not result['terminal']['stdout'] and not result['terminal']['stderr']
    assert all(node['state'] == 'pending' for node in result['simulation']['nodes'])
    assert result['quiz']['comparison'] == 'pending'


def test_normal_missing_option_focus_is_a_real_position_and_small_next_step():
    result = trace('  ls /lab', True)
    focus = result['lens']['focus']
    assert focus == {'start': 4, 'end': 4}  # After ls in the original input.
    assert '-l' in result['lens']['next']
