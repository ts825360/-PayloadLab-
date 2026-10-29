import pytest

from app.routes.labs import analyze_lab, attempt_lab


def run(url, normal=False):
    return attempt_lab('ssrf-medium' if normal else 'ssrf-easy', {'target_url': url}).learning_trace


@pytest.mark.parametrize('url,host', [
    ('https://example.com/news', 'example.com'),
    ('http://127.0.0.1/admin', '127.0.0.1'),
    ('http://localhost/admin', 'localhost'),
    ('http://[::1]/admin', '::1'),
])
def test_ssrf_story_connects_the_actual_input_host_and_dummy_response(url, host):
    data = run(url)
    assert url in data['lens']['what'] and host in data['lens']['what']
    assert '가상' in data['lens']['what']
    assert 'DNS' in data['lens']['why'] and 'HTTP' in data['lens']['why']
    assert data['network']['requested'] is False
    assert data['network']['dns_resolved'] is False
    assert '결과 창' in data['lens']['next']


def test_ssrf_normal_block_is_a_string_policy_decision_not_a_connection_error():
    data = run('http://127.0.0.1/admin', normal=True)
    assert data['execution']['status'] == 'blocked'
    assert 'preview.lab.invalid' in data['lens']['what']
    assert '없어서' in data['lens']['what']
    assert '연결 실패' in data['lens']['why']
    assert not data['execution']['stdout']


def test_ssrf_normal_userinfo_is_not_mistaken_for_the_destination():
    url = 'http://preview.lab.invalid@127.0.0.1/admin'
    data = run(url, normal=True)
    assert data['execution']['status'] == 'fetched'
    assert '127.0.0.1' in data['lens']['what']
    assert '@ 앞' in data['lens']['why']
    assert '사용자 정보' in data['lens']['why']
    assert '문자열' in data['lens']['why']
    assert '실제' in data['lens']['why']


def test_ssrf_normal_trusted_word_in_a_path_gets_a_path_explanation():
    data = run('http://127.0.0.1/preview.lab.invalid', normal=True)
    assert data['execution']['status'] == 'fetched'
    assert '경로' in data['lens']['why']
    assert '@ 앞' not in data['lens']['why']


@pytest.mark.parametrize('url,raw_host', [
    ('http://127.0.0.1/path/127.0.0.1', '127.0.0.1'),
    ('http://LOCALHOST/admin', 'LOCALHOST'),
    ('http://[::1]/path/::1', '::1'),
])
def test_ssrf_focus_points_to_the_host_in_the_address_not_a_repeated_path(url, raw_host):
    data = run(url)
    focus = data['lens']['focus']
    assert url[focus['start']:focus['end']] == raw_host
    assert focus['start'] < url.index('/path') if '/path' in url else focus['start'] == len('http://')


@pytest.mark.parametrize('url', ['not a url', 'file:///etc/passwd', 'https://x:bad', ''])
def test_ssrf_unsupported_input_is_not_called_a_failed_real_request(url):
    data = run(url)
    assert data['execution']['status'] == 'unsupported'
    assert '지원' in data['lens']['what']
    assert '연결' in data['lens']['why']
    assert 'HTTP/HTTPS' in data['lens']['next']


def test_ssrf_analysis_describes_the_parsed_host_without_a_response_claim():
    data = analyze_lab('ssrf-medium', {'target_url': 'http://preview.lab.invalid@127.0.0.1/admin'})
    assert data['execution'] is None
    assert data['phase'] == 'analysis'
    assert '127.0.0.1' in data['lens']['what']
    assert '실행 전' in data['lens']['what']
    assert '응답을 표시했' not in data['lens']['what']


def test_ssrf_non_loopback_is_not_claimed_to_be_a_verified_public_destination():
    data = run('http://10.0.0.1/admin')
    assert data['network']['internal'] is False
    assert '루프백' in data['lens']['why']
    assert '공개 여부' in data['lens']['why']


@pytest.mark.parametrize('url', ['http://10.0.0.1/', 'http://169.254.169.254/', 'https://example.com/'])
def test_ssrf_dummy_output_does_not_claim_a_verified_public_destination(url):
    data = run(url)
    assert '공개' not in data['execution']['stdout']
    assert '일반 목적지' in data['execution']['stdout']


@pytest.mark.parametrize('url', ['not a url', 'http://localhost:bad'])
def test_ssrf_unsupported_graph_is_not_presented_as_a_policy_block(url):
    data = run(url)
    nodes = {node['id']: node for node in data['simulation']['nodes']}
    assert nodes['policy']['value'] == '지원 형식 밖'
    assert nodes['destination']['value'] == '형식 확인 필요'
    assert nodes['destination']['state'] == 'unsupported'


def test_ssrf_multiple_at_signs_explain_the_final_boundary():
    data = run('http://preview.lab.invalid@x@127.0.0.1/admin', normal=True)
    assert data['network']['hostname'] == '127.0.0.1'
    assert '마지막 @' in data['lens']['why']


def test_ssrf_trusted_path_is_explained_even_with_unrelated_userinfo():
    data = run('http://user@127.0.0.1/preview.lab.invalid', normal=True)
    assert '사용자 정보' in data['lens']['why']
    assert '경로' in data['lens']['why']


@pytest.mark.parametrize('char', ['\x00', '\x7f'])
def test_ssrf_does_not_present_control_character_urls_as_supported(char):
    data = run('http://127.0.0.1/' + char)
    assert data['execution']['status'] == 'unsupported'
    assert data['network']['requested'] is False


def test_ssrf_does_not_use_network_helpers(monkeypatch):
    import socket

    def unexpected(*args, **kwargs):
        raise AssertionError('educational SSRF must not use the network')

    monkeypatch.setattr(socket, 'getaddrinfo', unexpected)
    monkeypatch.setattr(socket, 'create_connection', unexpected)
    for url in ['https://example.com/', 'http://127.0.0.1/', 'http://preview.lab.invalid@127.0.0.1/']:
        assert run(url, normal=True)['network']['requested'] is False
