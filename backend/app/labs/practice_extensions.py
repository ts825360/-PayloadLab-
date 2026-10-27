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
    start, end = 0, len(raw)
    try:
        parsed = urlsplit(raw)
        host = parsed.hostname or ''
        # Accessing port validates malformed port literals without resolving anything.
        _ = parsed.port
        if (parsed.scheme not in ('http', 'https') or not host
                or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in raw)):
            raise ValueError('HTTP/HTTPS URL 형식을 사용하세요.')
        # Locate the authority host, not the same text repeated in a path/query.
        authority_start = raw.find('//') + 2
        host_offset = parsed.netloc.rfind('@') + 1
        host_port = parsed.netloc[host_offset:]
        if host_port.startswith('['):
            start = authority_start + host_offset + 1
            end = start + host_port.index(']') - 1
        else:
            start = authority_start + host_offset
            end = start + len(host_port.split(':', 1)[0])
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
    stdout = ('모의 내부 응답: internal-admin (dummy)\n' if internal else '모의 일반 목적지 응답: preview (dummy)\n') if allowed else ''
    stderr = error or ('' if allowed else '교육용 문자열 정책이 요청을 차단했습니다.')
    trace['network'] = dict(hostname=host, destination='loopback' if internal else 'public/symbolic',
                            internal=internal, policy_allowed=allowed, requested=False,
                            dns_resolved=False, trusted_substring=TRUSTED_HOST if medium else None)
    if error:
        what = f"내 URL 입력은 {raw!r}입니다. 이 모형이 지원하는 HTTP/HTTPS 주소 형식에 맞지 않아 가상 응답을 만들 수 없어요."
        why = '지원 범위 밖의 주소이며 실제 서버의 연결 실패가 아닙니다. DNS 조회나 HTTP 연결 자체를 시도하지 않았어요.'
        next_action = '가져올 주소를 https://example.com/ 같은 HTTP/HTTPS 형식으로 바꿔 다시 관찰해보세요.'
    else:
        what = f"내가 입력한 URL은 {raw!r}입니다. 서버 역할의 모형이 주소를 나눠 읽으면 목적지 호스트(hostname)는 {host!r}입니다. "
        if medium:
            what += (f"전체 URL에 {TRUSTED_HOST!r} 문자열이 있어서 교육용 정책이 허용했어요. " if allowed
                     else f"전체 URL에 {TRUSTED_HOST!r} 문자열이 없어서 교육용 정책이 차단했어요. ")
        else:
            what += 'Easy 모형은 목적지를 제한하지 않고 가상 결과를 보여줘요. '
        if analysis:
            what += '아직 실행 전 분석이라 가상 응답은 만들지 않았어요.'
        elif not allowed:
            what += '따라서 이번에는 가상 응답도 반환되지 않아요.'
        else:
            what += ('이 호스트를 서버 자신의 루프백 주소로 분류해 가상 내부 응답을 표시했어요.' if internal
                     else '이 호스트는 모형의 루프백 목록에 해당하지 않아 일반 목적지용 가상 응답을 표시했어요.')
        why = ('루프백은 요청하는 서버 자신을 가리키는 주소예요. 이 모형은 localhost·루프백 IP만 구분하며, '
               '다른 주소의 실제 공개 여부나 안전성을 확인하지는 않아요. DNS 조회와 HTTP 요청은 수행하지 않습니다.')
        if medium:
            why += ' Normal은 호스트의 정확한 일치가 아니라 URL 전체의 부분 문자열만 검사해요.'
            if '@' in parsed.netloc:
                why += f" 이 모형은 마지막 @ 앞을 사용자 정보로 읽고, 뒤의 {host!r}를 목적지 호스트로 읽어요. 사용자 정보에 믿는 이름을 적어도 목적지가 그 이름으로 바뀌지는 않아요."
            if TRUSTED_HOST in parsed.path:
                why += ' 이 URL에서는 믿는 문자열이 호스트가 아닌 경로에 있어도 정책을 통과해요.'
            elif TRUSTED_HOST in parsed.query:
                why += ' 이 URL에서는 믿는 문자열이 호스트가 아닌 쿼리(물음표 뒤의 값)에 있어도 정책을 통과해요.'
            elif TRUSTED_HOST in parsed.fragment:
                why += ' 이 URL에서는 믿는 문자열이 호스트가 아닌 조각(# 뒤의 값)에 있어도 정책을 통과해요.'
            if not allowed:
                why += ' 이번 차단은 교육용 문자열 정책의 판단이며 실제 연결 실패가 아니에요.'
        next_action = ('결과 창에서 URL의 마지막 @ 뒤 호스트와 파싱된 목적지를 비교해보세요.' if '@' in parsed.netloc
                       else '결과 창에서 입력 URL의 서버 이름 부분과 파싱된 목적지 호스트를 비교해보세요.')
    trace['lens'] = _lens(status, 'URL의 실제 목적지를 확인하세요',
                          what, why, next_action, raw, start, end, lesson='network')
    _graph(trace, [('url', '입력 URL', raw, 'input'),
                   ('policy', '교육용 목적지 정책', '지원 형식 밖' if error else '허용' if allowed else '차단',
                    'unsupported' if error else 'passed' if allowed else 'blocked'),
                   ('destination', '파싱된 목적지 (연결 없음)', '형식 확인 필요' if error else host,
                    'unsupported' if error else 'internal' if internal else 'public'),
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
        stderr = '모형의 지원 범위 밖입니다. 호스트 하나 또는 호스트와 구분자 ; / && 뒤의 whoami, pwd, id 하나만 모형화합니다.'
    trace['command_model'] = dict(hostname=host, separator=separator.group() if separator else None,
                                 supported_commands=list(allowed_outputs), real_shell=False)
    what = f"호스트 이름 칸에 {raw!r}를 넣었어요. 입력은 ping -c 1 뒤에 붙어 {('ping -c 1 ' + raw)!r}라는 문장으로 조립됩니다. "
    why = 'ping은 대상에 응답을 요청하는 명령이고 -c 1은 한 번 요청한다는 뜻이에요. 여기서는 실제 셸 실행이나 네트워크 연결 없이 정해진 모의 출력만 만듭니다. '
    if raw != raw.strip():
        why += '조립 화면에는 원문을 보존하지만, 모형이 호스트와 명령 조각을 읽을 때는 바깥쪽 공백을 제외해요. '
    if medium:
        why += 'Normal은 입력에서 ;가 있는지만 검사해요. 문자를 지우거나 바꾼 것이 아니라, 있으면 처리 전체를 차단하는 불완전한 필터입니다. '
    else:
        why += 'Easy는 이 구분자를 막는 필터가 없어요. '
    if status == 'blocked':
        detail = '입력에 ;가 있어 Normal 필터가 차단 대상으로 판단했어요. '
        if not analysis:
            detail += 'ping과 뒤의 추가 명령 모두 모의 실행하지 않았어요. 명령의 표준 출력은 없고, 표준 오류에는 필터의 차단 안내만 표시해요. '
        next_action = '차단된 입력에서 필터가 검사한 ; 위치 하나를 확인해보세요.'
    elif status == 'command_ok':
        detail = f"{host!r} 전체를 ping의 대상 값으로 읽는 일반 입력이며 추가 명령은 없어요. "
        if not analysis:
            detail += f"그래서 {host!r}에 대한 모의 응답 1개만 표시했어요. 추가 명령을 관찰하는 실습 목표는 아직 충족하지 않았지만, 잘못된 공격이나 연결 실패라는 뜻은 아니에요. "
        next_action = ('example.com; whoami를 입력해 ; 앞뒤가 각각 어디에 붙는지 관찰해보세요.' if not medium else
                       '세미콜론만 막는 필터에서 다른 명령 연결 기호가 남는지 관찰해보세요.')
    elif status == 'injected':
        command = parts[2]
        detail = f"{host!r}는 ping 대상이고, {parts[1]!r} 뒤의 {command!r}는 추가 명령 조각으로 인식돼요. "
        why += (';는 앞 명령의 성공 여부와 관계없이 다음 명령으로 이어가는 경계예요. ' if parts[1] == ';' else
                '&&는 앞 명령이 성공했을 때 다음 명령으로 이어가는 경계예요. 이 모형은 지원하는 호스트의 ping이 성공한 상황을 가정해요. ')
        if medium:
            why += '이 입력에는 ;가 없고 &&는 필터에 걸리지 않고 남아 있어 추가 명령도 인식해요. '
        meaning = {'whoami': '사용자 이름', 'pwd': '작업 폴더', 'id': '사용자·그룹 번호'}[command]
        why += f"{command}는 {meaning} 확인에 쓰이는 명령이며, 여기서 값은 교육용으로 고정된 예시예요. "
        if not analysis:
            detail += f"모의 ping 응답 뒤에 {allowed_outputs[command].strip()!r}가 표시됐어요. 호스트 하나를 기대한 자리에 추가 명령이 들어가 이 실습의 목표를 충족한 거예요. "
        next_action = ('실행한 뒤 모의 출력에서 PING 줄 바로 다음 줄과 추가 명령 조각을 비교해보세요.' if analysis else
                       '모의 출력에서 PING 줄 바로 다음 줄과 추가 명령 조각을 비교해보세요.')
    else:
        if not raw.strip():
            detail = '호스트 입력이 비어 있어 ping의 대상 값을 읽을 수 없어요. '
            next_action = '호스트 이름 칸에 example.com만 넣어 기본 모의 출력을 확인해보세요.'
        elif valid_host and len(parts) == 3 and not parts[2]:
            detail = f"{parts[1]!r} 뒤에 추가 명령이 없어 모형이 처리할 조각이 완성되지 않았어요. "
            next_action = '표시된 구분자 바로 뒤에 명령 조각이 있는지 확인해보세요.'
        elif valid_host and len(parts) == 3 and parts[1] == '||':
            detail = '||는 앞 명령이 실패했을 때 이어가는 기호지만, 이 모형은 그 분기를 해석하지 않아요. '
            next_action = '지원하는 구분자 ; 또는 && 중 하나와 현재 기호를 비교해보세요.'
        elif valid_host and len(parts) == 3:
            detail = f"구분자 뒤의 {parts[2]!r}는 모형이 지원하는 whoami, pwd, id 중 하나와 일치하지 않아요. "
            next_action = '구분자 뒤 조각을 화면의 지원 명령 목록과 비교해보세요.'
        else:
            detail = '이 입력은 호스트 하나 또는 호스트와 추가 명령 하나라는 모형의 지원 범위에 맞지 않아요. '
            next_action = '입력을 example.com 하나로 줄여 기본 구조부터 관찰해보세요.'
        why += '모형의 지원 범위 밖이라는 뜻이며 실제 셸의 문법 오류나 명령 존재 여부를 단정하지 않아요. '
        if not analysis:
            detail += '따라서 모의 출력은 없고 지원 범위 안내를 표시했어요. '
    what += detail
    if analysis:
        what += '지금은 실행 전 분석이며 모의 출력을 만들지 않았어요.'
    focus_start = raw.index(';') if status == 'blocked' else separator.start() if separator else 0
    focus_end = focus_start + 1 if status == 'blocked' else separator.end() if separator else len(raw)
    trace['lens'] = _lens(status, '호스트 값과 명령 경계를 구분하세요',
                         what, why, next_action, raw,
                         focus_start, focus_end, 'commands')
    _graph(trace, [('input', '호스트 입력', raw, 'input'),
                   ('policy', '교육용 필터', ('; 발견: 처리 차단' if status == 'blocked' else '; 없음: 필터 통과') if medium else '필터 없음', 'blocked' if status == 'blocked' else 'passed'),
                   ('command', '가상 명령 경계', separator.group() if separator else '호스트 하나' if valid_host else '지원 범위 확인 필요', status),
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
    goal = '/lab의 이름·소유자·권한이 포함된 긴 목록' if medium else '/lab의 항목 이름만 나열한 목록'
    comparison, detail = 'unmodeled', '이 입력은 퀴즈가 설명하는 명령 조합의 지원 범위 밖이에요. 따옴표·연결 기호·다른 명령의 의미는 여기서 해석하지 않아요.'
    next_action = ('명령 이름, 긴 목록 옵션, 대상 경로라는 세 조각이 있는지 살펴보세요.' if medium else
                   'ls만 입력하고 이름 목록이 나오는지 확인해보세요.')
    start, end = 0, len(raw)
    if correct:
        comparison = 'matched'
        detail = ('명령 ls, 긴 목록 옵션 -l, 대상 경로 /lab이 이 순서로 있어 Normal의 목표와 일치해요. '
                  '그래서 report.txt와 readme.txt의 권한·소유자·경로를 간략히 적은 가상 목록을 표시했어요. '
                  '첫 줄의 mentor는 report.txt의 소유자이고, 둘째 줄의 student는 readme.txt의 소유자예요.' if medium else
                  'ls는 항목 이름을 나열하는 명령이에요. 이 퀴즈의 현재 가상 폴더는 /lab이므로 ls만 쓰거나 /lab을 붙인 답을 받아요. '
                  '이름만 보는 Easy 목표와 일치해서 report.txt와 readme.txt 두 이름을 표시했어요.')
        next_action = ('가상 출력 첫 줄에서 권한 -rw-------, 소유자 mentor, 경로 /lab/report.txt를 구분해보세요.' if medium else
                       'ls와 ls /lab을 한 번씩 입력하고 같은 두 이름이 나오는지 비교해보세요.')
    elif not tokens:
        comparison, detail = 'empty', '입력이 비어 있어 비교할 명령 조각이 없어요.'
        next_action = '먼저 명령 이름 ls 한 조각을 넣어보세요.'
    elif tokens[0] == 'ls':
        # Explain only small, explicit shapes; never infer general shell syntax.
        path = r'/[A-Za-z0-9_./-]*'
        known_shape = (tokens in (['ls'], ['ls', '-l'])
                       or len(tokens) == 2 and re.fullmatch(path, tokens[1])
                       or len(tokens) == 3 and (tokens[1] == '-l' and re.fullmatch(path, tokens[2])
                                                or re.fullmatch(path, tokens[1]) and tokens[2] == '-l'))
        if known_shape:
            comparison = 'goal_mismatch'
            if medium and '-l' not in tokens:
                detail = 'ls는 이름을 나열하지만, Normal의 긴 목록 목표에는 -l 옵션과 명시적인 /lab 경로가 필요해요. 현재 입력에는 -l이 없어요.'
                match = next(re.finditer(r'\S+', raw))
                start = end = match.end()
                next_action = '명령 이름 ls 바로 뒤에 긴 목록 옵션 -l이 있는지 확인해보세요.'
            elif medium and tokens == ['ls', '-l']:
                detail = '긴 목록 옵션 -l은 있지만, 이 퀴즈가 요구하는 대상 경로 /lab이 명시되지 않았어요.'
                next_action = '옵션 다음에 대상 경로 /lab을 적었는지 확인해보세요.'
            elif medium and tokens == ['ls', '/lab', '-l']:
                detail = '필요한 조각은 있지만 이 퀴즈의 답은 명령 이름 → 옵션 → 경로 순서로 비교해요. 현재 순서는 그 답과 달라요.'
                next_action = '긴 목록 옵션과 대상 경로의 순서만 바꿔 비교해보세요.'
            elif any(token.startswith('/') and token != '/lab' for token in tokens[1:]):
                target = next(token for token in tokens[1:] if token.startswith('/') and token != '/lab')
                detail = f'대상으로 적은 {target!r}는 퀴즈 목표의 /lab과 달라요. 그 경로가 실제로 존재하는지는 검사하지 않았어요.'
                next_action = '입력한 경로와 퀴즈 목표의 /lab을 비교해보세요.'
            else:
                detail = '이름만 보는 Easy 목표와 달리 -l은 권한·소유자도 포함한 긴 목록을 뜻해요. 이 퀴즈의 Easy 답은 ls 또는 ls /lab과 비교해요.'
                next_action = 'Easy에서 -l을 뺀 입력과 현재 입력을 비교해보세요.'
    labels = dict(matched='목표 일치', empty='입력 없음', goal_mismatch='목표 조건 다름', unmodeled='해석 지원 범위 밖')
    stderr = '' if correct else f'퀴즈 안내: {detail}'
    trace['quiz'] = dict(kind='token_exercise', goal='long_listing' if medium else 'list_directory',
                         tokens=tokens, comparison='pending' if analysis else comparison,
                         comparison_label='채점 전' if analysis else labels[comparison], goal_description=goal)
    what = f'내 명령 입력은 {raw!r}입니다. 퀴즈는 공백으로 나눈 {tokens!r}를 명령 조각(토큰)으로 읽어요. 이번 목표는 {goal}이에요. '
    what += '지금은 실행 전 분석이라 아직 채점하지 않았고 가상 목록도 만들지 않았어요.' if analysis else detail
    if not analysis and not correct:
        what += ' 가상 목록 대신 표준 오류 영역에 퀴즈 안내를 표시했어요.'
    why = ('ls는 목록을 보는 명령, -l은 권한과 소유자까지 보는 긴 목록 옵션, /lab은 대상 폴더 경로예요. '
           '이 연습은 실제 셸 실행이나 파일 조회 없이 공백으로 나눈 조각과 순서를 정해진 답과 비교합니다. '
           '퀴즈 답과 다르다는 것이 실제 Linux의 오류나 존재하지 않는 명령이라는 뜻은 아니에요. '
           'Normal 출력도 실제 ls의 모든 열을 재현한 것이 아니라 권한·소유자·경로만 남긴 간략한 가상 예시예요.')
    if analysis and correct:
        next_action = '직접 실행한 뒤 가상 목록의 항목과 이번 목표를 비교해보세요.'
    trace['lens'] = _lens('quiz_pending' if analysis else status, '입력 조각과 Linux 퀴즈 목표를 비교해요',
                         what, why, next_action, raw, start, end, lesson='linux')
    trace['terminal'] = _terminal(raw, 'student', '' if analysis else stdout, '' if analysis else stderr, 'quiz')
    _graph(trace, [('input', '입력 토큰', ' | '.join(tokens), 'input'),
                   ('goal', '퀴즈 목표', goal, 'goal'),
                   ('quiz', '명령어 퀴즈 채점', trace['quiz']['comparison_label'], status)], analysis)
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
