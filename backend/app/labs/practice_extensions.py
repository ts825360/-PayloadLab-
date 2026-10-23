"""Bounded educational models. No network, shell, host files, or credentials.

URLs are parsed as strings, commands are matched against tiny token grammars,
and permission history is replayed in fresh virtual state on every request.
These models illustrate specific lessons; they are not general interpreters.
"""
import ipaddress
import re
from urllib.parse import urlsplit

from app.core.lab import Lab, LabMetadata, RuleCheck, SuccessDetail


MAX_INPUT = 2000
MAX_HISTORY = 40
TRUSTED_HOST = 'preview.lab.invalid'
FILES = (
    dict(path='/lab/report.txt', owner='mentor', permissions='-rw-------', content='training-report'),
    dict(path='/lab/readme.txt', owner='student', permissions='-rw-r--r--', content='virtual lab readme'),
)
PERMISSION_COMMANDS = (
    'whoami', 'id', 'pwd', 'ls', 'ls /lab', 'ls -l /lab',
    'ls /lab/report.txt', 'ls -l /lab/report.txt', 'cat /lab/report.txt',
    'cat /lab/readme.txt', 'sudo -l', 'sudo /lab/maintenance', 'exit',
)


def _lens(key, title, what, why, next_action, raw='', start=0, end=None, lesson='simulation'):
    return dict(id=key, title=title, what=what, why=why, next=next_action,
                focus=dict(start=start, end=len(raw) if end is None else end), lesson=lesson)


def _execution(status, stdout='', stderr='', count=0):
    return dict(status=status, count=count, error=stderr, label='교육용 모의 실행',
                stdout=stdout, stderr=stderr, exit_code=1 if stderr else 0)


def _base(category, raw, prefix='', suffix=''):
    return dict(category=category, raw_input=raw, effective_input=raw, phase='result', simulated=True,
                composition=dict(prefix=prefix, value=raw, suffix=suffix, full=prefix + raw + suffix,
                                 ranges=dict(input=dict(start=0, end=len(raw)))),
                execution=None, lens=None, condition_tree=None, table=None,
                simulation=dict(nodes=[], edges=[]))


def _graph(trace, entries, analysis):
    trace['simulation'] = dict(
        nodes=[dict(id=key, label=label, value=str(value), state='pending' if analysis else state)
               for key, label, value, state in entries],
        edges=[dict(source=entries[i][0], target=entries[i + 1][0]) for i in range(len(entries) - 1)],
    )


def _ssrf(raw, medium, analysis):
    trace = _base('ssrf', raw, 'fetch("', '")  # 교육용 모형')
    host, internal, error = '', False, ''
    try:
        parsed = urlsplit(raw)
        host = parsed.hostname or ''
        # Accessing port validates malformed port literals without resolving anything.
        _ = parsed.port
        if parsed.scheme not in ('http', 'https') or not host or any(c.isspace() for c in raw):
            raise ValueError('HTTP/HTTPS URL 형식을 사용하세요.')
        if host == 'localhost':
            internal = True
        else:
            try:
                internal = ipaddress.ip_address(host).is_loopback
            except ValueError:
                internal = False  # No DNS resolution: hostnames remain symbolic strings.
    except (ValueError, TypeError):
        error = '지원하지 않는 URL입니다. HTTP/HTTPS와 올바른 호스트·포트를 확인하세요.'
    allowed = not error and (not medium or TRUSTED_HOST in raw)
    status = 'unsupported' if error else 'fetched' if allowed else 'blocked'
    stdout = ('모의 내부 응답: internal-admin (dummy)\n' if internal else '모의 공개 페이지: preview (dummy)\n') if allowed else ''
    stderr = error or ('' if allowed else '교육용 문자열 정책이 요청을 차단했습니다.')
    trace['network'] = dict(hostname=host, destination='loopback' if internal else 'public/symbolic',
                            internal=internal, policy_allowed=allowed, requested=False,
                            dns_resolved=False, trusted_substring=TRUSTED_HOST if medium else None)
    why = ('Normal의 불완전한 정책은 전체 URL에 신뢰 호스트 문자열이 포함되는지만 검사합니다. '
           '@ 앞은 사용자 정보이고 실제 목적지는 파싱된 hostname입니다.' if medium else
           '서버 관점의 loopback은 서버 자신입니다. 목적지 검사가 빠진 상황을 문자열 모형으로 비교합니다. DNS와 HTTP 요청은 수행하지 않습니다.')
    start = max(0, raw.rfind(host)) if host else 0
    trace['lens'] = _lens(status, 'URL의 실제 목적지를 확인하세요',
                          'URL 구조를 분석하는 단계입니다. 응답은 아직 만들지 않았습니다.' if analysis else
                          error or ('가상 내부 목적지 응답을 표시했습니다.' if internal and allowed else
                                    '가상 공개 목적지 응답을 표시했습니다.' if allowed else stderr),
                          why, '원본 URL의 권한부와 파싱된 hostname을 비교하세요.', raw, start,
                          start + len(host) if host else len(raw), lesson='network')
    _graph(trace, [('url', '입력 URL', raw, 'input'),
                   ('policy', '교육용 목적지 정책', '허용' if allowed else '차단', 'passed' if allowed else 'blocked'),
                   ('destination', '파싱된 목적지 (연결 없음)', host or '형식 오류', 'internal' if internal else 'public'),
                   ('response', '가상 응답', '실행 전' if analysis else stdout or stderr, status)], analysis)
    if not analysis:
        trace['execution'] = _execution(status, stdout, stderr, int(allowed))
    return trace


def _command_injection(raw, medium, analysis):
    trace = _base('command_injection', raw, 'ping -c 1 ', '  # 실제 셸 실행 없음')
    separator = re.search(r';|&&|\|\|', raw)
    status, stdout, stderr = 'unsupported', '', ''
    allowed_outputs = {'whoami': 'webapp\n', 'pwd': '/srv/preview\n', 'id': 'uid=1001(webapp) gid=1001(webapp)\n'}
    parts = re.split(r'\s*(;|&&|\|\|)\s*', raw.strip())
    host = parts[0]
    valid_host = bool(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?', host))
    if medium and ';' in raw:
        status, stderr = 'blocked', 'Normal의 불완전한 필터가 세미콜론(;)을 차단했습니다.'
    elif valid_host and len(parts) == 1:
        status, stdout = 'command_ok', f'PING {host}: 모의 응답 1개 (네트워크 연결 없음)\n'
    elif valid_host and len(parts) == 3 and parts[2] in allowed_outputs and parts[1] in (';', '&&'):
        status, stdout = 'injected', f'PING {host}: 모의 응답 1개\n' + allowed_outputs[parts[2]]
    else:
        stderr = '지원하지 않는 명령 형태입니다. 호스트와 구분자 ; 또는 && 뒤의 whoami, pwd, id만 모형화합니다.'
    trace['command_model'] = dict(hostname=host, separator=separator.group() if separator else None,
                                 supported_commands=list(allowed_outputs), real_shell=False)
    trace['lens'] = _lens(status, '호스트 값과 명령 경계를 구분하세요',
                         '명령 토큰을 확인하는 분석 단계입니다. 모의 명령도 아직 실행하지 않았습니다.' if analysis else
                         stderr or ('추가 명령을 교육용 모형이 인식했습니다.' if status == 'injected' else '호스트 하나를 모의 ping 대상으로 사용했습니다.'),
                         '실제 셸은 사용하지 않습니다. 이 모형에서는 ;와 &&가 명령 경계이고, Normal은 ;만 막아 &&가 남는 불완전한 정책입니다.',
                         '입력의 어느 부분이 호스트이고 어느 부분이 추가 명령인지 비교하세요.', raw,
                         separator.start() if separator else 0, separator.end() if separator else len(raw), 'commands')
    _graph(trace, [('input', '호스트 입력', raw, 'input'),
                   ('policy', '교육용 필터', '세미콜론 차단' if medium else '필터 없음', 'blocked' if status == 'blocked' else 'passed'),
                   ('command', '가상 명령 경계', separator.group() if separator else '호스트 하나', status),
                   ('output', '모의 출력', '실행 전' if analysis else stdout or stderr, status)], analysis)
    if not analysis:
        trace['execution'] = _execution(status, stdout, stderr, int(status in ('command_ok', 'injected')))
    return trace


def _file_metadata():
    return [{key: value for key, value in item.items() if key != 'content'} for item in FILES]


def _terminal(raw, user, stdout='', stderr='', mode='permissions'):
    return dict(prompt=f'{user}@practice:/lab' + ('# ' if user == 'root' else '$ '),
                command=raw, stdout=stdout, stderr=stderr, current_user=user,
                files=_file_metadata(), simulated=True, mode=mode,
                supported_commands=list(PERMISSION_COMMANDS) if mode == 'permissions' else ['ls', 'ls /lab', 'ls -l /lab'])


def _linux(raw, medium, analysis):
    trace = _base('linux_basics', raw, '', '  # 명령어 빈칸 퀴즈')
    tokens = raw.split()
    correct = tokens == ['ls', '-l', '/lab'] if medium else tokens in (['ls'], ['ls', '/lab'])
    status = 'quiz_correct' if correct else 'quiz_incorrect'
    stdout = ('-rw------- mentor /lab/report.txt\n-rw-r--r-- student /lab/readme.txt\n' if medium else 'report.txt  readme.txt\n') if correct else ''
    stderr = '' if correct else '이 명령어 퀴즈의 목표와 토큰을 다시 비교하세요.'
    trace['quiz'] = dict(kind='token_exercise', goal='long_listing' if medium else 'list_directory')
    trace['lens'] = _lens('quiz_pending' if analysis else status, 'Linux 명령어 빈칸 퀴즈',
                         '입력 토큰을 읽는 분석 단계입니다. 아직 채점하지 않았습니다.' if analysis else
                         '목표에 맞는 명령어 토큰입니다. 표시된 파일은 퀴즈용 가상 예시입니다.' if correct else stderr,
                         '-l은 소유자와 권한이 포함된 긴 목록 형식을 뜻합니다.' if medium else
                         'ls는 디렉터리의 항목 이름을 나열하는 명령입니다. 여기서는 실제 명령 실행 없이 토큰을 채점합니다.',
                         '/lab의 긴 목록을 만드는 명령어와 옵션을 구성하세요.' if medium else '/lab의 항목 이름을 나열하는 명령어를 구성하세요.',
                         raw, lesson='linux')
    trace['terminal'] = _terminal(raw, 'student', '' if analysis else stdout, '' if analysis else stderr, 'quiz')
    _graph(trace, [('input', '입력 토큰', ' | '.join(tokens), 'input'),
                   ('goal', '퀴즈 목표', '권한 포함 긴 목록' if medium else '항목 이름 목록', 'goal'),
                   ('quiz', '명령어 퀴즈 채점', '채점 전' if analysis else status, status)], analysis)
    if not analysis:
        trace['execution'] = _execution(status, stdout, stderr, int(correct))
    return trace


def _permission_command(command, user):
    """Return next virtual user and output; never interpret arbitrary text."""
    if command == 'sudo /lab/maintenance':
        return 'root', 'elevated', '교육용 helper가 인위적인 가상 root 셸을 시작했습니다.\n', ''
    if command == 'exit':
        return 'student', 'command_ok', '가상 student 셸로 돌아왔습니다.\n', ''
    if command == 'whoami':
        return user, 'command_ok', user + '\n', ''
    if command == 'id':
        return user, 'command_ok', ('uid=0(root) gid=0(root)\n' if user == 'root' else 'uid=1000(student) gid=1000(student)\n'), ''
    if command == 'pwd':
        return user, 'command_ok', '/lab\n', ''
    if command == 'sudo -l':
        return user, 'command_ok', '가상 sudo 규칙: (root) NOPASSWD: /lab/maintenance\n교육용 실행: sudo /lab/maintenance\n', ''
    if command.startswith('ls'):
        items = FILES[:1] if command.endswith('/lab/report.txt') else FILES
        stdout = ''.join(f"{item['permissions']} {item['owner']} {item['path']}\n" for item in items) if '-l' in command.split() else ''.join(item['path'] + '\n' for item in items)
        return user, 'command_ok', stdout, ''
    if command.startswith('cat '):
        item = FILES[0] if command.endswith('/lab/report.txt') else FILES[1]
        if item['owner'] != user and user != 'root' and item['permissions'][-3] != 'r':
            return user, 'permission_denied', '', f"cat: {item['path']}: Permission denied\n"
        return user, 'command_ok', item['content'] + '\n', ''
    return user, 'unsupported', '', '지원하지 않는 명령입니다. 표시된 가상 명령 목록을 확인하세요.'


def _permissions(raw, payload, analysis):
    trace = _base('permissions', raw)
    history = payload.get('history', [])
    valid_history = (isinstance(history, list) and len(history) <= MAX_HISTORY
                     and all(isinstance(command, str) and len(command) <= MAX_INPUT for command in history))
    if valid_history:
        valid_history = sum(map(len, history)) <= MAX_INPUT and all(command.strip() in PERMISSION_COMMANDS for command in history)
    user = 'student'
    if valid_history:
        for command in history:
            user, _, _, _ = _permission_command(command.strip(), user)
    previous_user = user
    command = raw.strip()
    if not valid_history:
        status, stdout, stderr = 'unsupported', '', '지원하지 않는 history입니다. 허용 명령 최대 40개·총 2000자만 재생합니다.'
    elif command not in PERMISSION_COMMANDS:
        status, stdout, stderr = 'unsupported', '', '지원하지 않는 명령입니다. 가상 명령 목록을 확인하세요.'
    elif analysis:
        status, stdout, stderr = 'pending', '', ''
    else:
        user, status, stdout, stderr = _permission_command(command, user)
    trace['terminal'] = _terminal(raw, user, '' if analysis else stdout, '' if analysis else stderr)
    trace['lens'] = _lens('permissions_pending' if analysis else status, '가상 사용자와 파일 권한을 비교하세요',
                         '이전 명령 기록으로 현재 사용자만 복원했습니다. 현재 명령은 아직 실행하지 않았습니다.' if analysis else
                         stderr or '표시된 사용자·권한·출력은 메모리 안의 교육용 모형 결과입니다.',
                         'report.txt는 mentor 소유의 0600 파일입니다. student의 Permission denied는 명령 오타가 아닙니다. '
                         'sudo /lab/maintenance는 이 실습에서만 인위적으로 가상 root 셸을 시작하는 helper입니다. '
                         '실제 sudo나 운영체제 권한은 바뀌지 않습니다.',
                         'whoami, ls -l /lab/report.txt, cat /lab/report.txt를 비교하고 sudo -l로 가상 허용 목록을 확인하세요.',
                         raw, lesson='permissions')
    _graph(trace, [('identity', '기록에서 복원한 가상 사용자', previous_user, 'identity'),
                   ('file', '가상 파일의 소유자와 권한', 'mentor / -rw------- / /lab/report.txt', 'permissions'),
                   ('command', '허용 목록의 가상 명령', raw, 'input'),
                   ('result', '권한 검사 결과', '실행 전' if analysis else status + ' / ' + user, status)], analysis)
    if not analysis:
        trace['execution'] = _execution(status, stdout, stderr, int(status in ('command_ok', 'elevated')))
    return trace


_SPECS = [
    ('ssrf', 'SSRF', 'target_url', ('easy', 'medium')),
    ('command_injection', 'Command Injection', 'hostname', ('easy', 'medium')),
    ('linux_basics', 'Linux 명령어 퀴즈', 'command', ('easy', 'medium')),
    ('permissions', '권한 상승 기초 (가상 실습)', 'command', ('easy',)),
]
_LAB_SPECS = {f"{category.replace('_', '-')}-{difficulty}": (category, field, difficulty)
              for category, _, field, difficulties in _SPECS for difficulty in difficulties}


def get_extension_trace(lab_id, payload, analysis=False):
    """Return a shared trace, or None for a category outside this adapter."""
    spec = _LAB_SPECS.get(lab_id)
    if spec is None:
        return None
    category, field, difficulty = spec
    valid_payload = isinstance(payload, dict)
    payload = payload if valid_payload else {}
    raw = payload.get(field, '')
    valid_input = valid_payload and isinstance(raw, str) and len(raw) <= MAX_INPUT
    raw = raw[:MAX_INPUT] if isinstance(raw, str) else ''
    if not valid_input:
        # Reject before interpretation: truncation must never turn oversized text
        # into a valid command and leave a misleading successful graph.
        message = f'{field} 입력은 최대 {MAX_INPUT}자의 문자열이어야 합니다.'
        trace = _base(category, raw)
        trace['lens'] = _lens('unsupported', '입력 형식을 확인하세요', message,
                              '이 교육용 모형은 제한된 문자열만 처리합니다.', '입력 길이와 자료형을 확인하세요.', raw)
        _graph(trace, [('input', '지원 범위 밖의 입력', raw, 'input'),
                       ('validation', '입력 검증', message, 'unsupported')], analysis)
        if category in ('permissions', 'linux_basics'):
            trace['terminal'] = _terminal(raw, 'student', stderr='' if analysis else message,
                                           mode='quiz' if category == 'linux_basics' else 'permissions')
        if analysis:
            trace['phase'] = 'analysis'
        else:
            trace['execution'] = _execution('unsupported', stderr=message)
        return trace
    medium = difficulty == 'medium'
    if category == 'ssrf':
        trace = _ssrf(raw, medium, analysis)
    elif category == 'command_injection':
        trace = _command_injection(raw, medium, analysis)
    elif category == 'linux_basics':
        trace = _linux(raw, medium, analysis)
    else:
        trace = _permissions(raw, payload, analysis)
    if analysis:
        trace['phase'] = 'analysis'
    return trace


def _goal(trace):
    execution = trace['execution']
    if execution['status'] == 'unsupported':
        return False
    if trace['category'] == 'ssrf':
        return execution['status'] == 'fetched' and trace['network']['internal']
    if trace['category'] == 'command_injection':
        return execution['status'] == 'injected'
    if trace['category'] == 'linux_basics':
        return execution['status'] == 'quiz_correct'
    return (trace['terminal']['current_user'] == 'root'
            and trace['terminal']['command'].strip() == 'cat /lab/report.txt'
            and execution['status'] == 'command_ok')


def _make_lab(lab_id, name, category, difficulty):
    def resolve(payload):
        trace = get_extension_trace(lab_id, payload)
        if not _goal(trace):
            return False, None
        return True, SuccessDetail(flow_nodes=[], flow_edges=[],
                                   code_snippet='# 교육용 메모리 모형: 실제 네트워크·셸·운영체제 권한 실행 없음')

    return Lab(metadata=LabMetadata(id=lab_id, name=f'{name} ({"Easy" if difficulty == "easy" else "Normal"})',
                                    category=category, difficulty=difficulty, route=f'/labs/{lab_id}'),
               rules=[RuleCheck('extension_observation', '모의 실행 결과와 Lens 설명에서 실습 목표를 확인하세요.', lambda payload: False)],
               resolve=resolve)


EXTENSION_LABS: list[Lab] = [
    _make_lab(f"{category.replace('_', '-')}-{difficulty}", name, category, difficulty)
    for category, name, _, difficulties in _SPECS for difficulty in difficulties
]
