"""Permission Lens must describe the bounded model's actual command and identity."""
import pytest
from app.labs.practice_extensions import get_extension_trace


def trace(command, history=None, analysis=False, **extra):
    payload={'command':command,**extra}
    if history is not None: payload['history']=history
    return get_extension_trace('permissions-easy',payload,analysis=analysis)


def story(result):
    return ' '.join(result['lens'][key] for key in ['what','why','next'])


@pytest.mark.parametrize('command,history,user,output',[
    ('whoami',[], 'student','student'),
    ('whoami',['sudo /lab/maintenance'],'root','root'),
    ('id',[],'student','uid=1000(student)'),
    ('id',['sudo /lab/maintenance'],'root','uid=0(root)'),
    ('pwd',[],'student','/lab'),
])
def test_identity_commands_explain_their_own_output(command,history,user,output):
    result=trace(command,history)
    assert result['terminal']['current_user']==user
    assert output in result['execution']['stdout']
    assert command in result['lens']['what'] and output in result['lens']['what']
    assert '실제' in result['lens']['why']
    assert 'report.txt는 mentor 소유의 0600' not in result['lens']['why']


def test_denial_connects_current_user_owner_and_exact_raw_error():
    result=trace('cat /lab/report.txt')
    assert result['execution']['stderr']=='cat: /lab/report.txt: Permission denied\n'
    text=story(result)
    for phrase in ['student','mentor','/lab/report.txt','-rw-------','다른 사용자','읽기','거부']:
        assert phrase in text
    assert '오타' in text
    focus=result['lens']['focus']
    assert result['raw_input'][focus['start']:focus['end']]=='/lab/report.txt'
    assert result['lens']['next'].count('sudo')==0  # One observation before escalation.


@pytest.mark.parametrize('history',[[],['sudo /lab/maintenance']])
def test_readme_story_does_not_borrow_the_report_denial(history):
    result=trace('cat /lab/readme.txt',history)
    assert result['execution']['status']=='command_ok'
    for phrase in ['/lab/readme.txt','student','-rw-r--r--','virtual lab readme']:
        assert phrase in story(result)
    assert 'Permission denied' not in result['lens']['why']
    assert 'readme.txt' in next(node['value'] for node in result['simulation']['nodes'] if node['id']=='file')


def test_root_report_read_explains_model_rule_and_goal():
    result=trace('cat /lab/report.txt',['sudo -l','sudo /lab/maintenance'])
    assert result['execution']['stdout']=='training-report\n'
    for phrase in ['root','mentor','training-report','모형','읽기']:
        assert phrase in story(result)
    assert '목표' in result['lens']['what']


@pytest.mark.parametrize('command',['ls','ls /lab','ls -l /lab','ls /lab/report.txt','ls -l /lab/report.txt'])
def test_listing_explains_listing_without_claiming_file_read(command):
    result=trace(command)
    assert command in result['lens']['what']
    assert '목록' in result['lens']['what']
    assert '내용을 읽은' in result['lens']['why']
    if '-l' in command:
        assert '소유자' in story(result) and '권한' in story(result)


def test_sudo_list_explains_a_rule_not_a_user_transition():
    result=trace('sudo -l')
    assert result['terminal']['current_user']=='student'
    for phrase in ['NOPASSWD','/lab/maintenance','아직','사용자']:
        assert phrase in story(result)


@pytest.mark.parametrize('history,previous',[([], 'student'),(['sudo /lab/maintenance'],'root')])
def test_helper_uses_previous_identity_and_does_not_claim_host_root(history,previous):
    result=trace('sudo /lab/maintenance',history)
    assert result['terminal']['current_user']=='root'
    assert previous in result['lens']['what'] and 'root' in result['lens']['what']
    assert '실제 sudo' in result['lens']['why'] and '인위적' in result['lens']['why']
    assert '파일을 읽' in result['lens']['what']
    if previous=='root': assert '이미' in result['lens']['what']


@pytest.mark.parametrize('history',[[],['sudo /lab/maintenance']])
def test_exit_explains_return_to_student(history):
    result=trace('exit',history)
    assert result['terminal']['current_user']=='student'
    assert 'exit' in result['lens']['what'] and 'student' in result['lens']['what']
    assert ('root' if history else '이미') in result['lens']['what']


@pytest.mark.parametrize('command',['','chmod 777 /lab/report.txt','cat /etc/passwd'])
def test_unsupported_is_a_model_limit_not_a_permission_denial(command):
    result=trace(command)
    assert result['execution']['status']=='unsupported'
    assert '지원 범위' in story(result)
    assert '실제 Linux' in result['lens']['why']
    assert '모른' in result['lens']['why'] or '판정하지' in result['lens']['why']


def test_bad_history_has_no_partially_replayed_root():
    result=trace('whoami',['sudo /lab/maintenance','unmodeled'])
    assert result['terminal']['current_user']=='student'
    assert '기록' in result['lens']['what'] and '재생하지' in result['lens']['what']
    assert result['execution']['stdout']==''


@pytest.mark.parametrize('command',['cat /lab/report.txt','sudo /lab/maintenance','exit'])
def test_analysis_replays_previous_identity_but_never_executes_current_command(command):
    result=trace(command,['sudo /lab/maintenance'],analysis=True)
    assert result['terminal']['current_user']=='root'
    assert result['execution'] is None
    assert not result['terminal']['stdout'] and not result['terminal']['stderr']
    assert command in result['lens']['what'] and '아직' in result['lens']['what']
    assert '표시했어요' not in result['lens']['what']


@pytest.mark.parametrize('padding',['  ','\u3000'])
def test_denial_explains_outer_whitespace_and_the_command_actually_used(padding):
    command='cat /lab/report.txt'
    raw=padding+command+padding
    result=trace(raw)
    assert result['raw_input']==raw
    assert result['execution']['status']=='permission_denied'
    assert '앞뒤 공백' in story(result)
    assert repr(command) in result['lens']['what']
    focus=result['lens']['focus']
    assert raw[focus['start']:focus['end']]=='/lab/report.txt'
