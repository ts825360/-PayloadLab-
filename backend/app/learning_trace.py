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
        return lens('filter_changed', '서버를 지나며 입력이 바뀌었어요', 'Normal의 기존 필터가 정확히 대문자 OR를 제거했습니다.',
                    '입력창의 원본과 서버에 전달된 값이 다르면, 조립되는 문장도 달라집니다.',
                    '필터 전후의 차이를 먼저 비교해보세요.', 0, len(filtered), 'filters')
    if quote >= 0 and raw[quote:quote + 2] == "''":
        return lens('escaped_quote', '연속된 따옴표가 문자로 읽혔어요',
                    "SQLite에서 문자열 안의 작은따옴표 두 개('')는 따옴표 문자 하나를 뜻합니다. 여기서는 이름 문자열을 닫지 못했어요.",
                    '따라서 이름 비교와 새 조건이 연결된 상태가 아닙니다. 문법 오류가 없어도 의도한 조건이 만들어진 것은 아니에요.',
                    '강조한 두 따옴표 사이에 OR를 넣으면 앞 따옴표는 이름 문자열을 닫고, 뒤 따옴표는 다음 문자열을 엽니다. OR가 두 비교 조건을 연결하도록 바꿔보세요.',
                    quote, quote + 2, 'operators')
    if missing:
        return lens('missing_operator', '두 조건 사이의 연결을 확인하세요',
                    '이름 비교 뒤에 또 다른 비교식이 이어지지만, 연결 연산자가 보이지 않습니다.',
                    'AND는 양쪽 모두 참, OR는 어느 한쪽이 참일 때 전체 조건을 참으로 만듭니다.',
                    '닫힌 이름 조건 뒤, 다음 비교식 앞에 어떤 관계가 필요한지 생각해보세요.', quote + 1, quote + 1, 'operators')
    if quote < 0:
        names = ', '.join(user[1] for user in sql._SEED_USERS)
        matching = any(user[1] == filtered for user in sql._SEED_USERS)
        return lens('string_value', '지금 입력은 이름이라는 값이에요',
                    f"입력한 '{filtered}'을 교육용 계정 {names}의 이름과 각각 비교했어요. "
                    + ('같은 이름은 있지만 ' if matching else '어느 이름과도 같지 않고 ')
                    + '미리 채운 비밀번호도 틀려서 반환된 계정이 없어요. 이름을 잘못 입력한 공격이라는 뜻은 아닙니다.',
                    '이 조회는 이름과 비밀번호를 AND로 연결해 둘 다 맞아야 해요. 작은따옴표 안의 글자는 사용자 이름이지 조건 연산자가 아닙니다.',
                    '오른쪽 계정 행을 눌러 내 입력과 그 계정의 이름 비교를 확인하고, 입력을 감싼 따옴표를 찾아보세요.', 0, len(filtered), 'strings')
    if error:
        return lens('syntax_error', 'SQL 문장이 완성되지 않았어요',
                    'SQLite가 아래 문장을 해석하지 못해 조회가 중단됐습니다.',
                    '따옴표를 추가하면 뒤에 붙는 고정 따옴표와의 짝도 함께 달라집니다. 오류 메시지와 실제 문장을 대조하세요.',
                    '문자열의 끝과, 그 뒤 조건이 시작하는 경계를 확인해보세요.', quote, min(quote + 1, len(filtered)), 'strings')
    return lens('inspect_result', '문장은 실행됐지만 반환된 행이 없어요',
                '문법 오류와 조회 결과가 없는 상황은 다릅니다. 이번에는 문장은 실행됐습니다.',
                '조건을 만족하는 계정이 없으면 로그인에 사용할 결과도 반환되지 않습니다.',
                '아래 결과를 확인하세요. 이 입력의 세부 문법은 현재 Lens 설명 범위 밖일 수 있습니다.', 0, len(filtered), 'operators')


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
    if not analysis and "'" not in filtered:
        trace['row_explanations'] = [dict(
            username_matches=u[1] == filtered,
            explanation=f"내 입력 '{filtered}'과 이 계정 이름 '{u[1]}'은 "
                        + ('같아요.' if u[1] == filtered else '달라요.')
                        + ' 비밀번호는 미리 틀린 값으로 채워 두었어요. AND는 두 비교가 모두 참이어야 하므로 이 행은 반환되지 않아요.'
        ) for u in sql._SEED_USERS]
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
            hint['what'] = '입력이 고정 따옴표 안에서 사용자 이름이라는 값으로 들어갑니다.'
        elif hint['id'] == 'syntax_error':
            hint['what'] = '조립한 문장이 SQLite의 문법 검사를 통과하지 못했습니다. 실제 조회 전의 분석입니다.'
    return trace


def xss_trace(raw, medium, result):
    value = xss._strip_lowercase_script_open(raw) if medium else raw
    changed = value != raw
    recognized = result.success
    if changed:
        hint = lens('filter_changed', 'HTML에 들어가기 전에 값이 바뀌었어요', '소문자 <script가 필터에서 제거됐습니다.',
                    '필터 이후 문자열이 브라우저로 전달됩니다. 태그의 원본과 전달된 값을 비교해야 합니다.',
                    '아래 HTML에서 남아 있는 태그를 확인해보세요.', 0, len(value), 'html')
    elif not xss._SCRIPT_OPEN.search(value):
        hint = lens('html_text', '이 입력은 HTML의 본문에 들어가요', '검색어가 이스케이프 없이 <p> 안에 삽입됩니다.',
                    'HTML은 꺾쇠로 감싼 태그와 일반 글자를 구분합니다. 태그를 만들면 브라우저의 해석이 달라질 수 있습니다.',
                    '먼저 <b>hello</b> 같은 표시 태그로 본문이 어떻게 달라지는지 관찰해보세요.', 0, len(value), 'html')
    else:
        hint = lens('recognized' if recognized else 'open_tag', '태그와 브라우저 실행을 구분해보세요',
                    '기존 랩 규칙이 script 태그의 형태를 확인합니다. 실제 자바스크립트 실행 여부까지 검증하지는 않습니다.',
                    '태그가 있어도 내용이 비어 있거나 자바스크립트가 잘못되면 기대한 동작은 일어나지 않을 수 있습니다.',
                    'HTML과 태그 내용을 확인한 뒤, 원할 때 브라우저 결과를 직접 열어 관찰하세요.', 0, len(value), 'html')
    return dict(category='reflected_xss', raw_input=raw, effective_input=value,
                composition=dict(prefix="<p>'", value=value, suffix="'에 대한 검색 결과입니다</p>", full=xss._render_search_page(value)),
                execution=dict(status='recognized' if recognized else 'unrecognized', count=0, error='', label='교육용 태그 규칙'),
                lens=hint, condition_tree=None, table=None, browser_execution_verified=False,
                code=xss._CODE_SNIPPET_MEDIUM if medium else xss._CODE_SNIPPET_EASY)


def idor_trace(payload, medium, result):
    oid = payload.get('requested_id')
    if not isinstance(oid, int) or isinstance(oid, bool):
        return None
    order = idor._ORDERS.get(oid)
    owner = order['owner_id'] if order else None
    allowed = bool(order) and (not medium or payload.get('claimed_user_id') == owner)
    status = 'missing' if not order else 'exposed' if result.success else 'own' if allowed else 'blocked'
    title = '요청 대상과 소유자는 서로 다른 정보예요'
    what = '현재 사용자는 1042입니다. 주문번호를 바꾸면 조회하는 대상이 달라집니다.'
    why = '번호를 안다는 사실은 열람 권한이 있다는 뜻이 아닙니다. 서버는 실제 로그인 사용자와 주문 소유자를 대조해야 합니다.'
    next_action = '주문 1042와 1043을 비교하고, 소유자와 현재 사용자가 같은지 확인해보세요.'
    if medium:
        why = 'Normal은 서버 세션 대신 요청의 claimed_user_id를 믿습니다. 이 값도 입력자가 바꿀 수 있다는 점을 살펴보세요.'
    if not order:
        what = '요청한 주문이 없어 소유자와 결과를 확인할 수 없습니다.'
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
        data = xss_trace(payload.get('query', ''), medium, result)
    elif lab_id.startswith('idor'):
        data = idor_trace(payload, medium, result)
        if data:
            data['relations'].pop('allowed', None)
    if data is None:
        return dict(phase='analysis', execution=None, table=None, condition_tree=None,
                    lens=lens('invalid_input', '입력 형태를 확인해주세요',
                              '이 실습에서 읽을 수 없는 값입니다.', '문자열 또는 주문번호 형식을 확인해주세요.',
                              '입력칸에 값을 다시 작성해보세요.'))
    data.update(phase='analysis', execution=None, table=None, condition_tree=None)
    return data
