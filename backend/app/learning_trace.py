"""Execution evidence for the beginner workspace; never a generic SQL/HTML parser.

The existing lab oracles and flow schema stay intact. SQL results are obtained
from SQLite. Condition explanations are emitted only for the small grammar
matched below; arbitrary SQL receives actual query/error/rows, not a guessed tree.
"""
import re
import sqlite3
from types import SimpleNamespace

from app.labs import idor, reflected_xss as xss, sql_injection as sql
from app.labs.practice_extensions import get_extension_trace


def lens(key, title, what, why, next_action, start=0, end=0, lesson='strings'):
    return dict(id=key, title=title, what=what, why=why, next=next_action,
                focus=dict(start=start, end=end), lesson=lesson)


def leaf(key, text, values, group='logic'):
    return dict(id=key, text=text, values=values, group=group)


def branch(key, op, children):
    values = [all(c['values'][i] for c in children) if op == 'AND'
              else any(c['values'][i] for c in children)
              for i in range(len(sql._SEED_USERS))]
    return dict(id=key, op=op, children=children, values=values)


def sql_tree(query, raw):
    name = leaf('name', f"username = '{raw}'", [u[1] == raw for u in sql._SEED_USERS], 'name')
    password = leaf('password', "password = 'this_is_definitely_wrong'", [False, False], 'password')
    if "'" not in raw:
        return branch('root', 'AND', [name, password])
    pattern = (r"username = '([^']*)'\s*(OR|AND)\s*"
               r"('[^']*'\s*=\s*'[^']*'|[0-9]+\s*=\s*[0-9]+)\s*"
               r"(?:(--[^\r\n]*)|AND password = 'this_is_definitely_wrong')")
    match = re.fullmatch(pattern, query.split('WHERE ', 1)[1], re.I)
    if not match:
        return None
    name['text'] = f"username = '{match[1]}'"
    name['values'] = [u[1] == match[1] for u in sql._SEED_USERS]
    with sqlite3.connect(':memory:') as conn:
        constant = bool(conn.execute('SELECT ' + match[3]).fetchone()[0])
    condition = leaf('comparison', match[3], [constant, constant])
    op = match[2].upper()
    if match[4]:
        return branch('root', op, [name, condition])
    if op == 'OR':
        return branch('root', 'OR', [name, branch('password_group', 'AND', [condition, password])])
    return branch('root', 'AND', [name, condition, password])


def sql_lens(raw, filtered, error, success):
    quote = raw.find("'")
    missing = re.match(r"^[^']*'\s*(?='[^']*'\s*=)", raw)
    if success:
        return lens('success', '조회 조건이 달라졌어요', '실제 SQLite 조회에서 계정 행이 반환됐습니다.',
                    '주석은 모든 성공 입력에 필수인 것은 아닙니다. 아래 조건과 반환된 행을 함께 확인하세요.',
                    '비교하는 값을 바꾸면 어느 계정이 남을지 예상하고 다시 실행해보세요.', max(0, quote), len(raw), 'operators')
    if filtered != raw:
        why = '서버는 바뀐 값으로 SQL을 만듭니다. 필터로 글자가 지워지는 것과 문법이 맞거나 계정이 조회되는 것은 서로 다른 사실이에요.'
        if error:
            why = ('OR가 있던 두 비교 사이의 연결이 사라져, 이번 SQL은 문법 검사를 통과하지 못했어요.'
                   if re.match(r"^[^']*'\s+'[^']*'\s*=", filtered)
                   else '바뀐 값으로 조립한 SQL이 문법 검사를 통과하지 못했어요. 정확한 구문은 결과 창의 오류와 함께 확인해야 해요.')
        return lens('filter_changed', '서버를 지나며 입력이 바뀌었어요',
                    f"내 입력 {raw!r}에서 서버가 대문자 OR를 지웠어요. 실제 SQL의 따옴표 안에는 {filtered!r}가 들어갔어요.",
                    why,
                    '입력창의 원본과 바로 아래 필터 적용값에서 OR가 있던 자리를 비교해보세요.', 0, len(filtered), 'filters')
    if missing and raw[quote:quote + 2] != "''":
        return lens('missing_operator', '두 조건 사이의 연결을 확인하세요',
                    '이름 비교 뒤에 또 다른 비교식이 이어지지만, 연결 연산자가 보이지 않습니다.',
                    'AND는 양쪽 모두 참, OR는 어느 한쪽이 참일 때 전체 조건을 참으로 만듭니다.',
                    '닫힌 이름 조건 뒤, 다음 비교식 앞에 어떤 관계가 필요한지 생각해보세요.', quote + 1, quote + 1, 'operators')
    if error:
        return lens('syntax_error', 'SQL 문장이 완성되지 않았어요',
                    'SQLite가 아래 문장을 해석하지 못해 조회가 중단됐습니다.',
                    '따옴표를 추가하면 뒤에 붙는 고정 따옴표와의 짝도 함께 달라집니다. 오류 메시지와 실제 문장을 대조하세요.',
                    '문자열의 끝과, 그 뒤 조건이 시작하는 경계를 확인해보세요.', max(0, quote), min(max(0, quote) + 1, len(filtered)), 'strings')
    if quote >= 0 and raw[quote:quote + 2] == "''":
        # Keep the known missing-connector lesson separate from ordinary names.
        if re.fullmatch(r"[^']*''[^']*'\s*=\s*'[^']*'\s*(?:--[^\r\n]*)?", raw):
            return lens('escaped_quote', '연속된 따옴표가 문자로 읽혔어요',
                        "SQLite에서 문자열 안의 작은따옴표 두 개('')는 따옴표 문자 하나를 뜻합니다. 여기서는 이름 문자열을 닫지 못했어요.",
                        '따라서 이름 비교와 새 조건이 연결된 상태가 아닙니다. 문법 오류가 없어도 의도한 조건이 만들어진 것은 아니에요.',
                        '강조한 두 따옴표 사이에 OR를 넣으면 앞 따옴표는 이름 문자열을 닫고, 뒤 따옴표는 다음 문자열을 엽니다. OR가 두 비교 조건을 연결하도록 바꿔보세요.',
                        quote, quote + 2, 'operators')
        if re.fullmatch(r"(?:[^']|'')*", raw):
            return lens('escaped_quote', '이름에 따옴표 문자가 포함돼요',
                        "SQLite에서 문자열 안의 작은따옴표 두 개('')는 이름에 포함된 따옴표 문자 하나로 읽힙니다.",
                        '따옴표가 있다고 항상 새 조건이 되는 것은 아니에요. 문법이 맞는 이름 입력과 계정이 조회되는지는 서로 다른 사실입니다.',
                        '조립된 SQL의 이름 값과 admin·guest의 이름을 비교하고, 고정된 비밀번호 조건도 함께 확인해보세요.',
                        quote, quote + 2, 'strings')
    if quote < 0:
        names = ', '.join(user[1] for user in sql._SEED_USERS)
        matching = any(user[1] == filtered for user in sql._SEED_USERS)
        return lens('string_value', '지금 입력은 이름이라는 값이에요',
                    f"입력한 '{filtered}'을 서버가 SQL의 따옴표 안에 넣고, 교육용 계정 {names}의 이름과 각각 비교했어요. "
                    + ('같은 이름은 있지만 ' if matching else '어느 이름과도 같지 않고 ')
                    + '미리 채운 비밀번호도 틀려서 반환된 계정이 없어요. 문법 오류나 이름을 잘못 입력한 공격이라는 뜻은 아닙니다.',
                    '이 조회는 이름과 비밀번호를 AND로 연결해 둘 다 맞아야 해요. 작은따옴표 안의 글자는 사용자 이름이지 조건 연산자가 아닙니다.',
                    '문장에서 해당 위치 보기로 결과 창을 열고, 관찰할 계정을 admin에서 guest로 바꿔 이름 비교를 확인해보세요.', 0, len(filtered), 'strings')
    return lens('inspect_result', '문장은 실행됐지만 반환된 행이 없어요',
                '문법 오류와 조회 결과가 없는 상황은 다릅니다. 이번에는 문장은 실행됐습니다.',
                '조건을 만족하는 계정이 없으면 로그인에 사용할 결과도 반환되지 않습니다.',
                '결과 창에서 실제 반환 행을 확인하세요. 이 입력의 세부 문법은 현재 Lens 설명 지원 범위 밖일 수 있습니다.', 0, len(filtered), 'operators')


def sql_row_stories(tree, rows):
    """Explain only the small condition tree already checked against SQLite."""
    def leaves(node):
        return [node] if 'op' not in node else [leaf for child in node['children'] for leaf in leaves(child)]

    conditions = {node['id']: node for node in leaves(tree)}
    name = conditions['name']
    name_value = name['text'][len("username = '"):-1]
    stories = []
    for index, user in enumerate(sql._SEED_USERS):
        truth = lambda value: '참' if value else '거짓'
        story = (f"지금 선택한 계정은 '{user[1]}'입니다. 이름 조건에 넣은 값은 '{name_value}'입니다. "
                 f"두 이름을 비교한 결과는 {truth(name['values'][index])}입니다. ")
        if 'comparison' in conditions:
            comparison = conditions['comparison']
            story += f"추가 비교 {comparison['text']}은 {truth(comparison['values'][index])}이에요. "
        if 'password' in conditions:
            story += '미리 넣은 비밀번호는 이 계정의 비밀번호와 달라서 거짓이에요. '
            if 'comparison' in conditions and tree['op'] == 'OR':
                story += '추가 비교와 비밀번호 조건은 AND로 먼저 묶여요. '
        else:
            story += '뒤의 비밀번호 조건은 주석으로 제외됐어요. '
        story += ('OR는 어느 한쪽이 참이면 전체가 참이에요. ' if tree['op'] == 'OR'
                  else 'AND는 연결된 비교가 모두 참이어야 전체가 참이에요. ')
        story += f"이 계정의 전체 조건은 {truth(tree['values'][index])}이고, "
        story += '실제 조회에 이 행이 반환됐어요.' if user in rows else '실제 조회에 이 행은 반환되지 않아요.'
        stories.append(dict(username_matches=name['values'][index], explanation=story))
    return stories


def suffix_is_commented(prefix, value):
    """Track SQLite quote and line-comment boundaries, without parsing SQL."""
    text = prefix + value
    mode, index = '', 0
    while index < len(text):
        char = text[index]
        following = text[index:index + 2]
        if mode == 'comment':
            if char in '\r\n':
                mode = ''
        elif mode == 'block':
            if following == '*/':
                mode = ''
                index += 1
        elif mode:
            terminator = ']' if mode == '[' else mode
            if char == terminator:
                if mode != '[' and following == terminator * 2:
                    index += 1
                else:
                    mode = ''
        elif following == '--':
            mode = 'comment'
            index += 1
        elif following == '/*':
            mode = 'block'
            index += 1
        elif char in "'\"`[":
            mode = char
        index += 1
    return mode == 'comment'


def sql_trace(raw, medium, analysis=False):
    filtered = sql._strip_uppercase_or(raw) if medium else raw
    query = sql.compose_query(filtered)
    conn = sql._seed_db()
    error, rows = '', []
    try:
        if analysis:
            # Compile only: EXPLAIN returns bytecode, not login rows.
            conn.execute('EXPLAIN ' + query).fetchall()
        else:
            rows = conn.execute(query).fetchall()
    except sqlite3.Error as exc:
        error = str(exc)
    finally:
        conn.close()
    tree = None if error or analysis else sql_tree(query, filtered)
    ranges = dict(input=dict(start=0, end=len(filtered)))
    if tree:
        quote = filtered.find("'")
        ranges['name'] = dict(start=0, end=quote if quote >= 0 else len(filtered))
        if quote >= 0:
            comment = filtered.find('--', quote + 1)
            ranges['logic'] = dict(start=quote + 1, end=comment if comment >= 0 else len(filtered))
            if comment >= 0:
                ranges['comment'] = dict(start=comment, end=len(filtered))
    trace = dict(
        category='sql_injection', raw_input=raw, effective_input=filtered,
        composition=dict(prefix=sql.QUERY_PREFIX, value=filtered, suffix=sql.QUERY_SUFFIX, full=query, ranges=ranges,
                         suffix_commented=suffix_is_commented(sql.QUERY_PREFIX, filtered)),
        execution=dict(status='syntax_error' if error else 'matched' if rows else 'empty',
                       error=error, count=len(rows), label='SQLite 실제 조회'),
        lens=sql_lens(raw, filtered, error, bool(rows)), condition_tree=tree,
        table=dict(columns=['id', 'username', 'password'], rows=[dict(cells=list(u), matched=u in rows) for u in sql._SEED_USERS]),
        code=sql._CODE_SNIPPET_MEDIUM if medium else sql._CODE_SNIPPET_EASY,
        interpretation_limited=tree is None,
    )
    if tree:
        trace['row_explanations'] = sql_row_stories(tree, rows)
        if rows:
            trace['lens']['what'] = (f"내 입력 {raw!r}이 SQL의 이름 자리에 들어가 조회 조건을 바꿨어요. "
                                    + (f"필터 후 실제 사용한 값은 {filtered!r}이에요. " if filtered != raw else '')
                                    + f"실제 조회에서 {len(rows)}개 계정이 반환됐어요.")
            trace['lens']['why'] = ('OR는 이름 비교가 거짓인 계정도 다른 비교가 참이면 포함할 수 있어요. '
                                    if tree['op'] == 'OR' else 'AND는 이름 비교와 추가 비교가 모두 참인 계정을 포함해요. ')
            trace['lens']['why'] += '결과 창에서 선택한 계정의 비교값과 실제 반환 여부를 연결해 읽어보세요.'
            trace['lens']['next'] = '결과 창의 관찰할 계정을 guest로 바꾸고, 이름 비교와 전체 조건의 참·거짓을 비교해보세요.'
    elif rows:
        trace['lens']['why'] = '반환된 행은 실제 조회 결과예요. 이 식의 세부 해석은 현재 설명 지원 범위 밖이라 원인을 단정하지 않아요.'
        trace['lens']['next'] = '결과 창에서 실제 반환된 계정부터 확인해보세요.'
    if analysis:
        trace['phase'] = 'analysis'
        trace['execution'] = None
        trace['table'] = None
        hint = trace['lens']
        if hint['id'] == 'inspect_result':
            trace['lens'] = lens('ready_to_try', '이 문장은 어떤 결과를 만들까요?',
                                 '문장을 조립하고 SQLite 문법 검사를 마쳤습니다. 계정 조회는 아직 실행하지 않았어요.',
                                 '문법이 맞는 것과 원하는 조건이 되는 것은 다릅니다. 결과를 먼저 예상해보세요.',
                                 '실행하기를 누르면 실제 조회 결과와 조건 관계를 확인할 수 있어요.',
                                 0, len(filtered), 'operators')
        elif hint['id'] == 'string_value':
            hint['what'] = f"내 입력 {raw!r}이 고정 따옴표 안에서 사용자 이름 값으로 들어갑니다. 아직 계정 조회 전이에요."
        elif hint['id'] == 'filter_changed':
            hint['what'] += ' 아직 계정 조회 전의 문장 분석이에요.'
        elif hint['id'] == 'syntax_error':
            hint['what'] = '조립한 문장이 SQLite의 문법 검사를 통과하지 못했습니다. 실제 조회 전의 분석입니다.'
    return trace


def xss_trace(raw, medium, result, analysis=False):
    value = xss._strip_lowercase_script_open(raw) if medium else raw
    changed = value != raw
    recognized = result.success
    insertion = f"내 검색어는 {raw!r}입니다. 서버는 이 값을 <p> 본문 안에 넣어 HTML을 만들어요. "
    if changed:
        hint = lens('filter_changed', 'HTML에 들어가기 전에 값이 바뀌었어요',
                    f"내 검색어는 {raw!r}입니다. 서버가 소문자 <script를 먼저 지운 값은 {value!r}입니다. 이 값을 <p> 본문에 넣어 응답 HTML을 만들어요.",
                    '필터는 글자를 지울 뿐 HTML이나 자바스크립트 실행 여부를 검증하지 않아요. 바뀐 값으로 태그 인식 규칙을 확인해야 해요.',
                    '결과 창의 조립 HTML에서 원본에 있던 <script가 어떻게 바뀌었는지 한 곳을 찾아보세요.', 0, len(value), 'html')
    elif not xss._SCRIPT_OPEN.search(value):
        hint = lens('html_text', '이 입력은 HTML의 본문에 들어가요',
                    insertion + '이 입력은 교육용 script 태그 규칙에 맞지 않아요. 일반 검색어를 잘못 쓴 공격이라는 뜻은 아닙니다.',
                    'HTML 표시 변화와 자바스크립트 실행은 다릅니다. 이 규칙의 미인식만으로 다른 형태의 코드 실행이나 안전 여부를 단정하지 않아요.',
                    '결과 창에서 조립 HTML의 <p> 사이에 내 입력이 들어간 자리를 찾아보세요.', 0, len(value), 'html')
    else:
        hint = lens('recognized' if recognized else 'open_tag', '태그와 브라우저 실행을 구분해보세요',
                    insertion + ('교육용 규칙이 시작·닫는 script 태그 형태를 인식했어요.'
                                 if xss._SCRIPT_CLOSE.search(value) else '교육용 규칙이 찾는 닫는 </script> 형태는 아직 없어요.'),
                    '태그 형태 인식은 실제 브라우저 실행의 증거가 아니에요. 태그 내용·문법·브라우저 정책에 따라 동작이 달라지고, 미지원 형태는 이 규칙으로 판정하지 않아요.',
                    '결과 창에서 태그 안의 내용을 확인한 뒤, 원하면 브라우저 결과 열기로 실제 표시를 따로 관찰하세요.', 0, len(value), 'html')
    if analysis:
        hint['what'] += ' 아직 응답 HTML을 실행 전인 입력 분석이에요.'
    return dict(category='reflected_xss', raw_input=raw, effective_input=value,
                composition=dict(prefix="<p>'", value=value, suffix="'에 대한 검색 결과입니다</p>", full=xss._render_search_page(value)),
                execution=dict(status='recognized' if recognized else 'unrecognized', count=0, error='', label='교육용 태그 규칙'),
                lens=hint, condition_tree=None, table=None, browser_execution_verified=False,
                code=xss._CODE_SNIPPET_MEDIUM if medium else xss._CODE_SNIPPET_EASY)


def idor_trace(payload, medium, result, analysis=False):
    oid = payload.get('requested_id')
    if not isinstance(oid, int) or isinstance(oid, bool):
        return None
    order = idor._ORDERS.get(oid)
    owner = order['owner_id'] if order else None
    allowed = bool(order) and (not medium or payload.get('claimed_user_id') == owner)
    status = 'missing' if not order else 'exposed' if result.success else 'own' if allowed else 'blocked'
    title = '요청 대상과 소유자는 서로 다른 정보예요'
    claim = payload.get('claimed_user_id')
    what = (f"내가 입력한 주문번호는 {oid}입니다. 서버가 이 번호로 더미 주문을 찾았어요. "
            f"교육용 현재 사용자 번호는 {idor._CURRENT_USER_ID}, 실제 소유자 번호는 {owner}입니다. ")
    if medium:
        what += f"요청 값은 claimed_user_id={claim if claim is not None else '없음'}입니다. "
        if claim is None:
            what += '소유자 주장 값을 전달하지 않아 주문 정보가 반환되지 않아요.'
        else:
            what += ('요청 값과 실제 소유자가 같으므로 주문 정보가 반환됐어요.' if allowed
                     else '요청 값과 실제 소유자가 달라서 주문 정보가 반환되지 않아요.')
    elif order:
        what += ('같은 사용자의 본인 주문 정보가 반환됐어요.' if owner == idor._CURRENT_USER_ID
                 else '소유자가 다른데도 주문 정보가 반환됐어요. 번호 조회 뒤에 소유권 검사가 빠져 있기 때문이에요.')
    why = '주문번호는 대상을 찾는 값일 뿐 열람 권한이 아닙니다. 실제 서비스는 서버가 확인한 사용자와 주문 소유자를 대조해야 해요. 이 랩의 현재 사용자는 고정된 더미 값이며 실제 인증 세션이 아닙니다.'
    next_action = '주문번호만 1042에서 1043으로 바꿔 실행하고, 결과 창의 현재 사용자와 소유자를 비교해보세요.'
    if medium:
        why += ' Normal은 실제 인증 대신 입력자가 바꿀 수 있는 claimed_user_id를 믿어요. 요청 값과 소유자가 같아도 정당한 권한 검사가 된 것은 아닙니다.'
        next_action = '주문번호 1043은 유지하고 claimed_user_id만 1과 2001로 바꿔, 결과 창의 비교와 반환 여부를 확인해보세요.'
    if not order:
        what = f"주문번호 {oid}로 더미 주문을 찾았지만 해당 주문이 없어서 반환할 정보도 없어요. 소유권 검사에서 차단된 경우와는 달라요."
        next_action = '주문번호를 존재하는 1042로 바꿔 결과 창에서 소유자를 확인해보세요.'
    if analysis:
        what = f"요청한 대상은 주문번호 {oid}입니다. 이 번호가 조회 주소의 대상 자리에 들어갑니다. 아직 주문 정보 반환 여부를 결정하는 조회 전 분석이에요."
        if medium:
            what += (f" claimed_user_id={claim} 역시 사용자가 전달하는 값이에요." if claim is not None
                     else ' 소유자 주장 값은 아직 입력하지 않았어요.')
    value = str(oid)
    suffix = f"?claimed_user_id={payload.get('claimed_user_id', '')}" if medium else ''
    return dict(category='idor', raw_input=value, effective_input=value,
                composition=dict(prefix='GET /orders/', value=value, suffix=suffix, full=f'GET /orders/{value}{suffix}'),
                execution=dict(status=status, count=1 if allowed else 0, error='', label='교육용 객체 조회'),
                lens=lens(status, title, what, why, next_action, 0, len(value), 'ownership'),
                condition_tree=None,
                relations=dict(current_user=idor._CURRENT_USER_ID, requested_id=oid, owner=owner,
                               claimed_user=payload.get('claimed_user_id'), medium=medium, allowed=allowed),
                table=dict(columns=['order_id', 'owner_id', 'item'], rows=[dict(cells=[k, v['owner_id'], v['item']], matched=allowed and k == oid) for k, v in idor._ORDERS.items()]),
                code=idor._CODE_SNIPPET_MEDIUM if medium else idor._CODE_SNIPPET_EASY)


def build_learning_trace(lab_id, payload, result):
    extension = get_extension_trace(lab_id, payload)
    if extension is not None:
        return extension
    medium = lab_id.endswith('-medium')
    if lab_id.startswith('sql-injection') and isinstance(payload.get('username', ''), str):
        return sql_trace(payload.get('username', ''), medium)
    if lab_id.startswith('reflected-xss') and isinstance(payload.get('query', ''), str):
        return xss_trace(payload.get('query', ''), medium, result)
    if lab_id.startswith('idor'):
        return idor_trace(payload, medium, result)
    return None


def build_input_analysis(lab_id, payload):
    extension = get_extension_trace(lab_id, payload, analysis=True)
    if extension is not None:
        return extension
    medium = lab_id.endswith('-medium')
    result = SimpleNamespace(success=False)
    data = None
    if lab_id.startswith('sql-injection') and isinstance(payload.get('username', ''), str):
        return sql_trace(payload.get('username', ''), medium, analysis=True)
    if lab_id.startswith('reflected-xss') and isinstance(payload.get('query', ''), str):
        data = xss_trace(payload.get('query', ''), medium, result, analysis=True)
    elif lab_id.startswith('idor'):
        data = idor_trace(payload, medium, result, analysis=True)
        if data:
            data['relations'].pop('allowed', None)
    if data is None:
        return dict(phase='analysis', execution=None, table=None, condition_tree=None,
                    lens=lens('invalid_input', '입력 형태를 확인해주세요',
                              '이 실습에서 읽을 수 없는 값입니다.', '문자열 또는 주문번호 형식을 확인해주세요.',
                              '입력칸에 값을 다시 작성해보세요.'))
    data.update(phase='analysis', execution=None, table=None, condition_tree=None)
    return data
