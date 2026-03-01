#!/usr/bin/env python3
"""
WP Blog Publisher — SEO/AEO 최적화 블로그 자동 게시 스크립트

사용법:
    # .env 파일 사용 (권장)
    python3 publish.py <blog_post.md>
    python3 publish.py <blog_post.md> --draft

    # 인자 직접 지정 (.env보다 우선)
    python3 publish.py <blog_post.md> --url https://example.com --user admin --password "app password"

    # 레거시 호환 (위치 인자)
    python3 publish.py <blog_post.md> <wp_url> <username> <password> [--draft]

.env 설정:
    아래 순서로 .env 파일을 탐색하며 처음 발견된 파일을 로드:
      1) scripts/.env  (스크립트와 같은 디렉토리)
      2) <cwd>/.env    (명령 실행 디렉토리)
      3) <skill-root>/.env  (스킬 루트 디렉토리)

    WP_URL=https://example.com
    WP_USER=username
    WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
    WP_POST_STATUS=publish

인증:
    1순위: Application Password (Basic Auth) 자동 시도
    2순위: Cookie + Nonce (Basic Auth 실패 시 자동 전환)
"""

import requests, json, re, sys, os, argparse
from base64 import b64encode
from pathlib import Path
from html import escape as html_escape
from urllib.parse import urlparse, quote as url_quote


# ===================================================================
# OUTPUT HELPERS
# ===================================================================

# ANSI 색상 코드 (터미널 지원 여부 자동 감지)
_USE_COLOR = sys.stdout.isatty()

def _c(code, text):
    return f'\033[{code}m{text}\033[0m' if _USE_COLOR else text

def ok(msg):
    """초록색 성공 메시지"""
    print(_c('32', f'   [OK] {msg}'))

def warn(msg):
    """노란색 경고 메시지"""
    print(_c('33', f' [WARN] {msg}'))

def err_exit(msg) -> 'None':  # noqa: never returns
    """빨간색 에러 메시지 출력 후 종료"""
    print(_c('31', f'[ERROR] {msg}'), file=sys.stderr)
    sys.exit(1)
    raise SystemExit(1)  # for type checker reachability

def step(n, msg):
    """단계 헤더 출력"""
    print(_c('36', f'\n{n}. {msg}'))


# ===================================================================
# ENV
# ===================================================================

def load_dotenv():
    """scripts/.env 파일에서 환경 변수 로드 (python-dotenv 없이 동작)"""
    env_paths = [
        Path(__file__).parent / '.env',          # scripts/.env
        Path.cwd() / '.env',                      # 현재 디렉토리/.env
        Path(__file__).parent.parent / '.env',    # 스킬 루트/.env
    ]

    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    # partition('=')을 사용하여 값에 = 가 포함된 경우도 처리
                    key, _, value = line.partition('=')
                    key = key.strip()
                    # 따옴표 제거 시 내부 값 보호 (예: password="a=b=c" → a=b=c)
                    value = value.strip()
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    if key and key not in os.environ:
                        os.environ[key] = value
            return str(env_path)
    return None


# ===================================================================
# AUTH
# ===================================================================

def try_basic_auth(wp_url, username, password):
    """Application Password (Basic Auth) 시도"""
    session = requests.Session()
    token = b64encode(f'{username}:{password}'.encode()).decode()
    session.headers.update({'Authorization': f'Basic {token}'})

    try:
        r = session.get(f'{wp_url}/wp-json/wp/v2/users/me', timeout=15)
    except requests.exceptions.Timeout:
        warn('Basic Auth 요청 시간 초과 (15s)')
        return None, None
    except requests.exceptions.ConnectionError as e:
        warn(f'Basic Auth 연결 실패: {e}')
        return None, None
    if r.status_code == 200:
        return session, r.json()

    # --- 실패 원인 진단 ---
    if r.status_code == 401:
        try:
            body = r.json()
            code = body.get('code', '')
        except ValueError:
            code = ''
        if code == 'rest_not_logged_in':
            warn('401 rest_not_logged_in — Authorization 헤더가 PHP에 전달되지 않고 있습니다')
            warn('  → Railway Apache 환경이라면 Custom Start Command가 필요합니다:')
            warn('    Settings → Custom Start Command에 auth-header 설정 추가')
            warn('    (자세한 명령은 references/railway-wp-setup.md 참조)')
        elif code == 'incorrect_password' or 'incorrect' in code:
            warn('401 — 비밀번호가 올바르지 않습니다')
            warn('  → Application Password를 사용하고 있는지 확인하세요 (로그인 비밀번호 아님!)')
            warn('  → wp-admin → 사용자 → 프로필 → Application Passwords에서 새로 발급')
        else:
            warn(f'401 — 인증 실패 (code: {code})')
            warn('  → Application Password가 유효한지 확인하세요')
    return None, None


def try_cookie_auth(wp_url, username, password):
    """Cookie + Nonce 인증 (리버스 프록시 환경용)"""
    session = requests.Session()

    try:
        # 1) 로그인 페이지 접근
        session.get(f'{wp_url}/wp-login.php', timeout=15)
        session.cookies.set('wordpress_test_cookie', 'WP%20Cookie%20check')

        # 2) 로그인 POST
        # allow_redirects=False 로 302 vs 200 구분하여 로그인 실패 감지
        r = session.post(f'{wp_url}/wp-login.php', data={
            'log': username,
            'pwd': password,
            'wp-submit': 'Log In',
            'redirect_to': f'{wp_url}/wp-admin/',
            'testcookie': '1'
        }, allow_redirects=False, timeout=15)

        # 로그인 성공 시 302 리다이렉트, 실패 시 200(로그인 폼 재표시)
        if r.status_code == 200:
            warn('Cookie auth 로그인 실패 (자격증명 거부됨)')
            warn('  → Cookie 인증에는 워드프레스 "로그인 비밀번호"가 필요합니다')
            warn('  → Application Password로는 Cookie 로그인이 불가능합니다')
            warn('  → Basic Auth가 되면 Cookie 인증은 필요 없습니다 (Railway Start Command 확인)')
            return None, None
        # 리다이렉트를 따라가서 세션 쿠키 확보
        if r.status_code in (301, 302):
            session.get(r.headers.get('Location', f'{wp_url}/wp-admin/'), timeout=15)

        # 3) REST API Nonce 추출
        page = session.get(f'{wp_url}/wp-admin/post-new.php', timeout=15)
        m = re.search(r'var\s+wpApiSettings\s*=\s*({.+?})\s*;', page.text, re.DOTALL)
        if not m:
            warn('wp-admin 페이지에서 wpApiSettings를 찾을 수 없음')
            return None, None

        try:
            settings = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            warn(f'wpApiSettings JSON 파싱 실패: {e}')
            return None, None

        nonce = settings.get('nonce')
        if not nonce:
            warn('wpApiSettings에 nonce 필드가 없음')
            return None, None

        session.headers.update({'X-WP-Nonce': nonce})

        # 4) 인증 확인
        r = session.get(f'{wp_url}/wp-json/wp/v2/users/me', timeout=15)
        if r.status_code == 200:
            return session, r.json()
        return None, None

    except requests.exceptions.Timeout:
        warn('Cookie Auth 요청 시간 초과 (15s)')
        return None, None
    except requests.exceptions.ConnectionError as e:
        warn(f'Cookie Auth 연결 실패: {e}')
        return None, None


def authenticate(wp_url, username, password):
    """인증 시도 (Basic → Cookie 순서)"""
    step(3, 'Authenticating...')

    # Basic Auth 시도
    session, user = try_basic_auth(wp_url, username, password)
    if session:
        ok(f'Method: Application Password (Basic Auth)')
        ok(f'User: {user["name"]} (ID: {user["id"]})')
        return session

    # Cookie + Nonce 시도
    warn('Basic Auth 실패 — Cookie + Nonce 시도 중...')
    session, user = try_cookie_auth(wp_url, username, password)
    if session:
        ok(f'Method: Cookie + Nonce')
        ok(f'User: {user["name"]} (ID: {user["id"]})')
        return session

    err_exit(
        '모든 인증 방법 실패.\n'
        '  아래를 순서대로 확인하세요:\n'
        '  1) WP_URL이 정확한지 (브라우저에서 접속 확인)\n'
        '  2) Railway Custom Start Command가 적용되었는지 (Apache Authorization 헤더 전달 필요)\n'
        '  3) Application Password가 유효한지 (wp-admin → 사용자 → 프로필에서 새로 발급)\n'
        '  4) WP_USER가 워드프레스 "계정명"인지 (Application Password 라벨이 아님)\n'
        '  진단 실행: python3 publish.py --diagnose --url <WP_URL> --user <USER> --password <PASS>'
    )


def diagnose(wp_url, username, password):
    """WordPress 연결 및 인증 상태를 진단합니다."""
    print(_c('36', '\n=== WP Blog Publisher 진단 모드 ===\n'))
    issues = []

    # 1) 사이트 접속 확인
    step(1, f'사이트 접속 테스트: {wp_url}')
    try:
        r = requests.get(wp_url, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            ok(f'사이트 접속 성공 (HTTP {r.status_code})')
        else:
            warn(f'HTTP {r.status_code} — 사이트가 정상적으로 응답하지 않습니다')
            issues.append('사이트 접속 문제')
    except requests.exceptions.ConnectionError:
        warn('연결 실패 — URL이 정확한지, 서비스가 실행 중인지 확인하세요')
        issues.append('사이트 접속 불가')
    except requests.exceptions.Timeout:
        warn('응답 시간 초과 (15s)')
        issues.append('사이트 응답 시간 초과')

    # 2) REST API 엔드포인트 확인
    step(2, 'REST API 엔드포인트 확인')
    try:
        r = requests.get(f'{wp_url}/wp-json/', timeout=15)
        if r.status_code == 200:
            ok('REST API 엔드포인트 정상')
            try:
                info = r.json()
                ok(f'사이트 이름: {info.get("name", "N/A")}')
            except ValueError:
                warn('REST API가 JSON이 아닌 응답 반환')
        elif r.status_code == 404:
            warn('REST API 비활성 또는 Permalink 설정 필요')
            warn('  → 관리자 → 설정 → 고유주소에서 "글 이름" 등으로 변경')
            issues.append('REST API 비활성')
        else:
            warn(f'REST API 응답: HTTP {r.status_code}')
    except Exception as e:
        warn(f'REST API 접근 실패: {e}')
        issues.append('REST API 접근 실패')

    # 3) Authorization 헤더 전달 확인 (Basic Auth)
    step(3, 'Basic Auth (Application Password) 테스트')
    token = b64encode(f'{username}:{password}'.encode()).decode()
    try:
        r = requests.get(
            f'{wp_url}/wp-json/wp/v2/users/me',
            headers={'Authorization': f'Basic {token}'},
            timeout=15
        )
        if r.status_code == 200:
            user = r.json()
            ok(f'Basic Auth 성공! 사용자: {user.get("name")} (ID: {user.get("id")})')
            ok('→ 이 자격증명으로 publish.py 정상 실행 가능합니다')
        elif r.status_code == 401:
            try:
                body = r.json()
                code = body.get('code', '')
                message = body.get('message', '')
            except ValueError:
                code, message = '', r.text[:200]

            warn(f'Basic Auth 실패 — HTTP 401 (code: {code})')

            if code == 'rest_not_logged_in':
                warn('  원인: Apache가 Authorization 헤더를 PHP로 전달하지 않고 있습니다')
                warn('  해결: Railway → Settings → Custom Start Command에 다음 명령 입력:')
                print()
                print('  bash -c "a2dismod mpm_event mpm_worker || true; '
                      'a2enmod mpm_prefork rewrite || true; '
                      'printf \'%s\\n\' \'SetEnvIfNoCase Authorization \"^(.*)\" HTTP_AUTHORIZATION=$1\' '
                      '> /etc/apache2/conf-available/auth-header.conf; '
                      'a2enconf auth-header || true; docker-entrypoint.sh apache2-foreground"')
                print()
                issues.append('Apache Authorization 헤더 미전달 → Custom Start Command 필요')
            elif 'incorrect' in code:
                warn('  원인: 비밀번호가 틀립니다')
                warn('  확인: Application Password를 사용하고 있는지 (로그인 비밀번호 아님)')
                warn('  발급: wp-admin → 사용자 → 프로필 → Application Passwords')
                issues.append('Application Password 불일치')
            else:
                warn(f'  응답: {message}')
                issues.append(f'Basic Auth 인증 실패: {code}')
        else:
            warn(f'예상치 못한 응답: HTTP {r.status_code}')
    except Exception as e:
        warn(f'Basic Auth 요청 실패: {e}')
        issues.append('Basic Auth 요청 실패')

    # 4) Application Password 형식 확인
    step(4, 'Application Password 형식 확인')
    stripped = password.replace(' ', '')
    if len(stripped) == 24 and stripped.isalnum():
        ok(f'형식 정상 (24자 영숫자, 공백 포함 {len(password)}자)')
    else:
        warn(f'형식 의심: 길이 {len(stripped)}자 (공백 제외)')
        warn('  일반적인 Application Password: 24자 영숫자 (공백 포함 29자)')
        warn('  로그인 비밀번호를 사용하고 있다면 Application Password를 발급받으세요')
        issues.append('Application Password 형식 의심')

    # 결과 요약
    print(_c('36', '\n=== 진단 결과 ==='))
    if not issues:
        ok('모든 검사 통과! publish.py로 게시할 수 있습니다.')
    else:
        warn(f'발견된 문제 {len(issues)}건:')
        for i, issue in enumerate(issues, 1):
            print(f'  {i}. {issue}')
        print()
        print('  위 문제를 순서대로 해결한 뒤 다시 진단하세요:')
        print('  python3 publish.py --diagnose')

    sys.exit(0 if not issues else 1)


def api(session, wp_url, method, endpoint, **kwargs):
    """REST API 호출 래퍼.

    HTTP 에러 / 네트워크 오류 발생 시 에러 메시지를 출력하고 즉시 종료합니다.
    """
    url = f'{wp_url}/wp-json/wp/v2/{endpoint}'
    kwargs.setdefault('timeout', 30)
    try:
        r = getattr(session, method)(url, **kwargs)
    except requests.exceptions.Timeout:
        err_exit(f'요청 시간 초과 (30s): {method.upper()} {endpoint}')
        return {}  # unreachable, for type checker
    except requests.exceptions.ConnectionError as e:
        err_exit(f'네트워크 연결 실패: {e}\n  URL: {url}')
        return {}  # unreachable, for type checker

    # HTTP 에러 코드 처리 (4xx, 5xx)
    if r.status_code == 429:
        retry_after = r.headers.get('Retry-After', '60')
        err_exit(f'WordPress API 요청 제한 (Rate Limited). {retry_after}초 후 재시도하세요')
    if r.status_code >= 400:
        try:
            body = r.json()
            msg = body.get('message') or body.get('error') or json.dumps(body, ensure_ascii=False)
        except ValueError:
            msg = r.text[:300] or '(빈 응답)'
        err_exit(f'HTTP {r.status_code} {r.reason} — {method.upper()} {endpoint}\n  {msg}')

    try:
        return r.json()
    except ValueError:
        err_exit(f'API가 JSON이 아닌 응답을 반환했습니다 (HTTP {r.status_code}): {r.text[:200]}')


# ===================================================================
# MARKDOWN → GUTENBERG
# ===================================================================

def _safe_url(url):
    """URL이 http/https/mailto 스킴인지 검증하고, 아니면 '#'으로 대체한다."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https', 'mailto', ''):
            return '#'
    except Exception:
        return '#'
    return url


def inline_format(text):
    """인라인 마크다운 → HTML 변환 (XSS 방어 포함)"""
    # 링크 처리 — 링크 텍스트는 HTML 이스케이프, URL은 스킴 검증 후 속성 이스케이프
    def replace_link(m):
        link_text = html_escape(m.group(1))
        href = html_escape(_safe_url(m.group(2)), quote=True)
        return f'<a href="{href}">{link_text}</a>'

    text = re.sub(r'\*\*(.+?)\*\*', lambda m: f'<strong>{html_escape(m.group(1))}</strong>', text)
    text = re.sub(r'\*(.+?)\*', lambda m: f'<em>{html_escape(m.group(1))}</em>', text)
    text = re.sub(r'`([^`]+)`', lambda m: f'<code>{html_escape(m.group(1))}</code>', text)
    text = re.sub(r'~~(.+?)~~', lambda m: f'<s>{html_escape(m.group(1))}</s>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)
    return text


def md_to_gutenberg(md_text):
    """마크다운 → 구텐베르크 블록 변환"""
    blocks = []
    lines = md_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 빈 줄 스킵
        if not line:
            i += 1
            continue

        # HTML 주석 스킵
        if line.startswith('<!--'):
            while i < len(lines) and '-->' not in lines[i]:
                i += 1
            i += 1
            continue

        # 수평선
        if line == '---':
            blocks.append(
                '<!-- wp:separator -->\n'
                '<hr class="wp-block-separator has-alpha-channel-opacity"/>\n'
                '<!-- /wp:separator -->'
            )
            i += 1
            continue

        # H2
        if line.startswith('## '):
            text = inline_format(line[3:].strip())
            blocks.append(
                f'<!-- wp:heading -->\n'
                f'<h2 class="wp-block-heading">{text}</h2>\n'
                f'<!-- /wp:heading -->'
            )
            i += 1
            continue

        # H3
        if line.startswith('### '):
            text = inline_format(line[4:].strip())
            blocks.append(
                f'<!-- wp:heading {{"level":3}} -->\n'
                f'<h3 class="wp-block-heading">{text}</h3>\n'
                f'<!-- /wp:heading -->'
            )
            i += 1
            continue

        # 이미지
        img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)$', line)
        if img_match:
            alt = html_escape(img_match.group(1), quote=True)
            src = html_escape(_safe_url(img_match.group(2)), quote=True)
            caption = ''
            if i + 1 < len(lines) and lines[i + 1].strip().startswith('*') and lines[i + 1].strip().endswith('*'):
                caption = lines[i + 1].strip()[1:-1]
                i += 1

            fig = f'<img src="{src}" alt="{alt}"/>'
            if caption:
                fig += f'<figcaption class="wp-element-caption">{inline_format(caption)}</figcaption>'

            blocks.append(
                f'<!-- wp:image {{"sizeSlug":"large","linkDestination":"none"}} -->\n'
                f'<figure class="wp-block-image size-large">{fig}</figure>\n'
                f'<!-- /wp:image -->'
            )
            i += 1
            continue

        # 인용문
        if line.startswith('> '):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith('> '):
                quote_lines.append(inline_format(lines[i].strip()[2:]))
                i += 1
            quote_text = '</p>\n<p>'.join(quote_lines)
            blocks.append(
                f'<!-- wp:quote -->\n'
                f'<blockquote class="wp-block-quote"><p>{quote_text}</p></blockquote>\n'
                f'<!-- /wp:quote -->'
            )
            continue

        # 표
        if line.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[\s\-:|]+\|$', lines[i + 1].strip()):
            headers = [c.strip() for c in line.strip('|').split('|')]
            i += 2

            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [inline_format(c.strip()) for c in lines[i].strip().strip('|').split('|')]
                rows.append(cells)
                i += 1

            thead = '<tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr>'
            tbody = ''.join(
                '<tr>' + ''.join(f'<td>{c}</td>' for c in row) + '</tr>'
                for row in rows
            )
            blocks.append(
                f'<!-- wp:table -->\n'
                f'<figure class="wp-block-table"><table>'
                f'<thead>{thead}</thead>'
                f'<tbody>{tbody}</tbody>'
                f'</table></figure>\n'
                f'<!-- /wp:table -->'
            )
            continue

        # 비순서 목록
        if line.startswith('- '):
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append(inline_format(lines[i].strip()[2:]))
                i += 1
            list_items = ''.join(f'<li>{item}</li>' for item in items)
            blocks.append(
                f'<!-- wp:list -->\n'
                f'<ul class="wp-block-list">{list_items}</ul>\n'
                f'<!-- /wp:list -->'
            )
            continue

        # 순서 목록
        if re.match(r'^\d+\.\s', line):
            items = []
            while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                items.append(inline_format(re.sub(r'^\d+\.\s', '', lines[i].strip())))
                i += 1
            list_items = ''.join(f'<li>{item}</li>' for item in items)
            blocks.append(
                f'<!-- wp:list {{"ordered":true}} -->\n'
                f'<ol class="wp-block-list">{list_items}</ol>\n'
                f'<!-- /wp:list -->'
            )
            continue

        # 일반 문단
        text = inline_format(line)
        while i + 1 < len(lines) and lines[i + 1].strip() and \
                not lines[i + 1].strip().startswith('#') and \
                not lines[i + 1].strip().startswith('|') and \
                not lines[i + 1].strip().startswith('-') and \
                not lines[i + 1].strip().startswith('>') and \
                not lines[i + 1].strip().startswith('!') and \
                not lines[i + 1].strip() == '---' and \
                not lines[i + 1].strip().startswith('<!--') and \
                not re.match(r'^\d+\.\s', lines[i + 1].strip()) and \
                not re.match(r'^!\[', lines[i + 1].strip()):
            i += 1
            text += ' ' + inline_format(lines[i].strip())

        blocks.append(f'<!-- wp:paragraph -->\n<p>{text}</p>\n<!-- /wp:paragraph -->')
        i += 1

    return '\n\n'.join(blocks)


# ===================================================================
# BLOG POST PARSER
# ===================================================================

def parse_blog_post(filepath):
    """블로그 포스트 마크다운 파싱 → SEO 메타 + 본문 분리"""
    content = ''
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        err_exit(f'파일을 찾을 수 없습니다: {filepath}')
    except PermissionError:
        err_exit(f'파일 읽기 권한이 없습니다: {filepath}')

    meta = {}

    # SEO 메타 추출 (한국어/유니코드 포함, 공백 변형, 따옴표 없는 슬러그 허용)
    # 패턴: | **Key** | value | — 셀 내 공백이 가변적일 수 있으므로 \s* 사용
    for key, pattern in {
        'title':    r'\|\s*\*\*Title\s*\(H1\)\*\*\s*\|\s*(.+?)\s*\|',
        'excerpt':  r'\|\s*\*\*Meta\s*Description\*\*\s*\|\s*(.+?)\s*\|',
        'slug':     r'\|\s*\*\*URL\s*Slug\*\*\s*\|\s*`?([^`|\n]+?)`?\s*\|',
        'category': r'\|\s*\*\*Category\*\*\s*\|\s*(.+?)\s*\|',
    }.items():
        m = re.search(pattern, content, re.UNICODE)
        if m:
            meta[key] = m.group(1).strip()

    tags_match = re.search(r'\|\s*\*\*Tags\*\*\s*\|\s*(.+?)\s*\|', content, re.UNICODE)
    if tags_match:
        meta['tags'] = [t.strip() for t in tags_match.group(1).split(',') if t.strip()]

    # 본문 추출 (H1부터 시작, H1은 제거)
    # H1이 없을 경우에도 안전하게 전체 content를 본문으로 사용
    body_match = re.search(r'^(# .+)$', content, re.MULTILINE)
    if body_match:
        body = content[body_match.start():]
        body = re.sub(r'<!--[\s\S]*?-->', '', body)
        # H1 한 줄만 제거 (연속 빈 줄도 함께 정리)
        body = re.sub(r'^# [^\n]*\n+', '', body).strip()
    else:
        # H1 없는 문서: HTML 주석만 제거하고 그대로 반환
        body = re.sub(r'<!--[\s\S]*?-->', '', content).strip()

    return meta, body


# ===================================================================
# MAIN
# ===================================================================

def main():
    # .env 로드
    env_file = load_dotenv()

    parser = argparse.ArgumentParser(
        description='WP Blog Publisher — .env 또는 인자로 실행',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='환경 변수 (scripts/.env 파일): WP_URL, WP_USER, WP_APP_PASSWORD, WP_POST_STATUS'
    )
    parser.add_argument('post_file', nargs='?', default=None, help='Blog post markdown file path')
    parser.add_argument('wp_url', nargs='?', default=None, help='WordPress site URL (또는 WP_URL 환경 변수)')
    parser.add_argument('username', nargs='?', default=None, help='WordPress username (또는 WP_USER 환경 변수)')
    parser.add_argument('password', nargs='?', default=None, help='Application password (또는 WP_APP_PASSWORD 환경 변수)')
    parser.add_argument('--url', dest='opt_url', help='WordPress site URL')
    parser.add_argument('--user', dest='opt_user', help='WordPress username')
    parser.add_argument('--password', '-p', dest='opt_password', help='Application password')
    parser.add_argument('--draft', action='store_true', help='Create as draft instead of publishing')
    parser.add_argument('--diagnose', action='store_true', help='Run connection & auth diagnostics (no post needed)')
    args = parser.parse_args()

    # 우선순위: 명령줄 옵션 > 위치 인자 > 환경 변수
    wp_url = (args.opt_url or args.wp_url or os.environ.get('WP_URL', '')).rstrip('/')
    username = args.opt_user or args.username or os.environ.get('WP_USER', '')
    password = args.opt_password or args.password or os.environ.get('WP_APP_PASSWORD', '')
    status = 'draft' if args.draft else os.environ.get('WP_POST_STATUS', 'publish')

    # 진단 모드
    if args.diagnose:
        if not wp_url or not username or not password:
            missing = []
            if not wp_url: missing.append('WP_URL (--url)')
            if not username: missing.append('WP_USER (--user)')
            if not password: missing.append('WP_APP_PASSWORD (--password)')
            err_exit(f'진단에 필요한 값 누락: {", ".join(missing)}')
        diagnose(wp_url, username, password)

    if not wp_url or not username or not password:
        missing = []
        if not wp_url: missing.append('WP_URL')
        if not username: missing.append('WP_USER')
        if not password: missing.append('WP_APP_PASSWORD')
        print(f'ERROR: 필수 설정 누락: {", ".join(missing)}')
        print(f'  .env 파일 또는 명령줄 인자로 지정하세요.')
        print(f'  cp scripts/.env.example scripts/.env  # 템플릿 복사 후 편집')
        sys.exit(1)

    # post_file 필수 확인 (진단 모드가 아닐 때)
    if not args.post_file:
        err_exit('블로그 포스트 파일 경로가 필요합니다.\n'
                 '  사용법: python3 publish.py <blog_post.md>\n'
                 '  진단:   python3 publish.py --diagnose')

    if env_file:
        print(f'0. Loaded config from {env_file}')

    # 1) 파싱
    print('1. Parsing blog post...')
    meta, body = parse_blog_post(args.post_file)
    print(f'   Title: {meta.get("title", "N/A")}')
    print(f'   Slug: {meta.get("slug", "N/A")}')
    print(f'   Tags: {meta.get("tags", [])}')

    # 2) 구텐베르크 변환
    print('\n2. Converting to Gutenberg blocks...')
    gutenberg = md_to_gutenberg(body)
    block_count = gutenberg.count('<!-- wp:')
    print(f'   Generated {block_count} blocks')

    # 3) 인증
    session = authenticate(wp_url, username, password)

    # 4) 카테고리
    print('\n4. Creating category...')
    cat_name = meta.get('category', '미분류')
    cats = api(session, wp_url, 'get', 'categories?search=' + url_quote(cat_name))
    if cats:
        cat_id = cats[0]['id']
        print(f'   Found: {cats[0]["name"]} (ID: {cat_id})')
    else:
        new_cat = api(session, wp_url, 'post', 'categories', json={'name': cat_name})
        cat_id = new_cat['id']
        print(f'   Created: {cat_name} (ID: {cat_id})')

    # 5) 태그
    print('\n5. Creating tags...')
    tag_ids = []
    for tag_name in meta.get('tags', []):
        existing = api(session, wp_url, 'get', 'tags?search=' + url_quote(tag_name))
        found = [t for t in existing if t['name'].lower() == tag_name.lower()]
        if found:
            tag_ids.append(found[0]['id'])
            print(f'   Found: {tag_name} (ID: {found[0]["id"]})')
        else:
            new_tag = api(session, wp_url, 'post', 'tags', json={'name': tag_name})
            tag_ids.append(new_tag['id'])
            print(f'   Created: {tag_name} (ID: {new_tag["id"]})')

    # 6) 게시
    print(f'\n6. {"Publishing" if status == "publish" else "Creating draft"}...')
    post_data = {
        'title': meta.get('title', ''),
        'content': gutenberg,
        'status': status,
        'categories': [cat_id],
        'tags': tag_ids,
        'excerpt': meta.get('excerpt', ''),
        'slug': meta.get('slug', ''),
    }

    result = api(session, wp_url, 'post', 'posts', json=post_data)

    if 'id' in result:
        print(f'   Post ID: {result["id"]}')
        print(f'   Status: {result["status"]}')
        print(f'   URL: {result["link"]}')
        print(f'\n=== {"PUBLISHED" if status == "publish" else "DRAFT CREATED"} ===')
        print(f'{result["link"]}')
    else:
        print(f'   ERROR: {json.dumps(result, ensure_ascii=False, indent=2)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
