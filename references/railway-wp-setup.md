# Railway 워드프레스 설치 후 REST API 셋업 가이드

## 개요

Railway에서 WordPress 프리셋을 배포한 뒤, REST API로 글을 발행하기까지 필요한 단계를 정리합니다.
**Apache MPM 충돌 오류**, **Authorization 헤더 전달 문제** 등 실전에서 겪는 이슈와 해결법을 포함합니다.

---

## Step 1. Railway에서 워드프레스 배포

1. [Railway](https://railway.app/) 로그인
2. **New Project** → **Deploy a Template** → **WordPress** 선택
3. 배포 완료 대기 (2~3분)
4. 생성된 도메인 확인: `https://내이름.up.railway.app`

---

## Step 2. Apache MPM 충돌 오류 해결

**프리셋 배포 직후 사이트 접속이 안 되면 이 단계가 필요합니다.**

### 증상

Railway 배포 로그에 아래 오류가 반복되며 컨테이너가 재시작 루프에 빠짐:

```
AH00534: apache2: Configuration error: More than one MPM loaded.
```

- MySQL은 정상 기동됨 (`ready for connections`)
- Apache만 죽어서 워드프레스에 접속 불가

### 원인

Railway 워드프레스 프리셋의 Docker 이미지(`wordpress:php8.x-apache`)가 Apache MPM 모듈을 여러 개(`mpm_prefork` + `mpm_event`) 포함한 채 빌드됩니다. Apache는 MPM을 **하나만** 사용할 수 있어서 충돌이 발생합니다.

### 해결: Custom Start Command

Railway → 해당 워드프레스 서비스 → **Settings** → **Custom Start Command**에 아래 한 줄을 입력합니다:

```bash
bash -c "a2dismod mpm_event mpm_worker || true; a2enmod mpm_prefork rewrite || true; printf '%s\n' 'SetEnvIfNoCase Authorization \"^(.*)\" HTTP_AUTHORIZATION=$1' > /etc/apache2/conf-available/auth-header.conf; a2enconf auth-header || true; docker-entrypoint.sh apache2-foreground"
```

**이 한 줄이 하는 일:**

| 부분 | 역할 |
|------|------|
| `a2dismod mpm_event mpm_worker` | 충돌하는 MPM 모듈 비활성화 |
| `a2enmod mpm_prefork rewrite` | 안정적인 MPM + URL 리라이트 활성화 |
| `SetEnvIfNoCase Authorization...` | Authorization 헤더를 PHP로 전달 (Step 5 문제 예방) |
| `docker-entrypoint.sh apache2-foreground` | 워드프레스 정상 기동 |

**저장 → 재배포** 후 배포 로그에서 `AH00534` 오류가 사라지면 성공입니다.

> **이 명령어는 MPM 충돌과 Authorization 헤더 문제를 동시에 해결합니다.**
> Step 2에서 이것을 적용하면 Step 5가 필요 없을 수 있습니다.

---

## Step 3. 워드프레스 초기 설정

배포된 도메인에 접속하면 워드프레스 설치 마법사가 나옵니다.

1. `https://내이름.up.railway.app/wp-admin/install.php` 접속
2. 언어 선택 → 사이트 제목, 관리자 계정(username/password) 설정
3. 설치 완료

> **중요:** 이때 만드는 계정이 **Administrator** 역할입니다. 이 계정 정보를 반드시 기록해 두세요.

---

## Step 4. Application Password 발급 (핵심)

REST API로 글을 쓰려면 **Application Password**가 필요합니다.
**워드프레스 로그인 비밀번호로는 API 인증이 안 됩니다.**

### 로그인 비밀번호 vs Application Password

```
로그인 비밀번호:  wp-admin 접속용 (브라우저 로그인)
                 → REST API Basic Auth에 사용 불가

Application Password:  REST API 전용 비밀번호
                       → 프로필에서 별도 발급
                       → 형식: xxxx xxxx xxxx xxxx xxxx xxxx
```

### 발급 방법

1. **관리자 페이지** → **사용자** → **프로필** (또는 API용 계정 클릭)
2. 페이지 아래쪽으로 스크롤 → **Application Passwords** 섹션
3. **새 애플리케이션 비밀번호 이름** 칸에 용도 입력 (예: `telegram-bot`, `claude`, `api`)
4. **새 애플리케이션 비밀번호 추가** 클릭
5. 생성된 비밀번호 복사 (예: `xxxx xxxx xxxx xxxx xxxx xxxx`)

> **주의:** 이 비밀번호는 **한 번만** 표시됩니다. 반드시 복사해서 저장하세요.

### 이름과 비밀번호의 관계

| 항목 | 예시 | 용도 |
|------|------|------|
| **이름** | `telegram-bot` | 라벨 (구분용, **인증에 사용 안 됨**) |
| **비밀번호** | `xxxx xxxx xxxx xxxx xxxx xxxx` | API 인증 시 비밀번호로 사용 |
| **Username** | `your-wp-username` | API 인증 시 아이디 (**워드프레스 계정명**) |

> **자주 하는 실수:** Application Password 생성 시 입력하는 "이름"(예: `api`)을 인증 아이디로 착각하는 경우가 많습니다. **이름은 라벨일 뿐이고, 인증 아이디는 항상 워드프레스 계정명입니다.**

인증 형식:
```
username: 워드프레스 계정명 (예: your-wp-username)
password: 발급받은 Application Password (예: xxxx xxxx xxxx xxxx xxxx xxxx)
```

---

## Step 5. API 테스트

터미널에서 아래 명령어로 인증이 되는지 확인합니다:

```bash
curl -u "내계정:xxxx xxxx xxxx xxxx xxxx xxxx" \
  https://내이름.up.railway.app/wp-json/wp/v2/users/me
```

### 성공 시 (200)

```json
{"id":1,"name":"내계정","roles":["administrator"]}
```

→ **완료!** 바로 API로 글을 쓸 수 있습니다.

### 실패 시 (401)

```json
{"code":"rest_not_logged_in","message":"현재 로그인 상태가 아닙니다."}
```

→ **Step 6으로 이동** (Apache 헤더 문제)

---

## Step 6. (401 발생 시만) Apache Authorization 헤더 문제 해결

Step 2에서 Custom Start Command를 적용했다면 이미 해결되어 있을 수 있습니다. 그래도 401이 나오면 아래 방법을 시도합니다.

### 원인

Apache가 `Authorization` 헤더를 PHP에 전달하지 않아, WordPress가 인증 정보를 읽지 못합니다.

```
Before (기본):
  클라이언트 → [Authorization: Basic xxx] → Apache → (헤더 삭제) → PHP → WordPress: "로그인 안 됨" 401

After (수정 후):
  클라이언트 → [Authorization: Basic xxx] → Apache → [HTTP_AUTHORIZATION=Basic xxx] → PHP → WordPress: "인증 성공" 200
```

### 방법 A: Custom Start Command (가장 쉬움)

Step 2의 명령어가 이미 Authorization 헤더 전달을 포함하고 있습니다. 적용하지 않았다면 Step 2를 참고하세요.

### 방법 B: 플러그인 설치

**Administrator 계정 필요**

1. 아래 코드를 `fix-rest-auth.php`로 저장:

```php
<?php
/**
 * Plugin Name: Fix REST API Auth Header
 * Description: Apache 환경에서 Authorization 헤더가 PHP에 전달되지 않는 문제를 수정합니다.
 * Version: 1.0.0
 */

if (!function_exists('fix_rest_api_auth_header')) {
    function fix_rest_api_auth_header() {
        if (!empty($_SERVER['HTTP_AUTHORIZATION'])) {
            return;
        }

        if (!empty($_SERVER['REDIRECT_HTTP_AUTHORIZATION'])) {
            $_SERVER['HTTP_AUTHORIZATION'] = $_SERVER['REDIRECT_HTTP_AUTHORIZATION'];
            return;
        }

        if (function_exists('getallheaders')) {
            foreach (getallheaders() as $key => $value) {
                if (strtolower($key) === 'authorization') {
                    $_SERVER['HTTP_AUTHORIZATION'] = $value;
                    return;
                }
            }
        }

        if (function_exists('apache_request_headers')) {
            foreach (apache_request_headers() as $key => $value) {
                if (strtolower($key) === 'authorization') {
                    $_SERVER['HTTP_AUTHORIZATION'] = $value;
                    return;
                }
            }
        }
    }

    fix_rest_api_auth_header();
}
```

2. ZIP으로 압축: `zip fix-rest-auth.zip fix-rest-auth.php`
3. 관리자 → **플러그인** → **새로 추가** → **플러그인 업로드** → ZIP 선택 → 설치 → **활성화**

> **UI 주의:** 플러그인 목록에서 "비활성화" 링크가 보이면 = 현재 **활성 상태**입니다.
> "활성화" 링크가 보이면 = 현재 **비활성 상태**이므로 클릭해서 활성화하세요.

4. Step 5의 curl 명령어로 다시 테스트

### 방법 C: Cookie + Nonce 인증 사용

Start Command 수정이나 플러그인 설치가 모두 불가능한 경우, 코드에서 Cookie + Nonce 방식으로 우회할 수 있습니다. `wp-blog-publisher-skill/scripts/publish.py`에 이 방식이 구현되어 있습니다.

---

## 최종 체크리스트

```
[ ] 1. Railway 워드프레스 배포 완료
[ ] 2. 사이트 접속 가능 (MPM 오류 없음)
[ ] 3. 관리자 계정으로 로그인 가능
[ ] 4. Application Password 발급 완료
[ ] 5. curl로 /wp-json/wp/v2/users/me 인증 성공 (200)
[ ] 6. (선택) Editor 등 별도 계정 생성 시 해당 계정에도 App Password 발급
```

---

## 자주 하는 실수

| 실수 | 원인 | 해결 |
|------|------|------|
| 사이트 자체가 안 뜸 (재시작 루프) | Apache MPM 모듈 중복 로드 | Step 2의 Custom Start Command 적용 |
| 로그인 비밀번호로 API 호출 | Application Password가 아님 | 프로필에서 App Password 별도 발급 |
| App Password 이름을 아이디로 사용 | 이름은 라벨일 뿐 | 아이디는 워드프레스 계정명 |
| Basic Auth로 401 발생 | Apache가 Authorization 헤더 차단 | Start Command에 SetEnvIfNoCase 추가 또는 플러그인 설치 |
| 플러그인 "비활성화" 클릭 | 이미 활성 상태인데 끔 | "비활성화" 보이면 = 이미 켜져 있음 |
| App Password 분실 | 한 번만 표시됨 | 새로 발급 (이전 것은 삭제) |
| Editor 계정으로 플러그인 설치 | 권한 부족 | Administrator 계정 필요 |

---

## 글 발행 예시

인증이 완료되면 아래처럼 API로 글을 쓸 수 있습니다:

```bash
curl -u "내계정:xxxx xxxx xxxx xxxx xxxx xxxx" \
  -X POST https://내이름.up.railway.app/wp-json/wp/v2/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "첫 번째 API 글",
    "content": "<!-- wp:paragraph -->\n<p>REST API로 작성한 글입니다.</p>\n<!-- /wp:paragraph -->",
    "status": "draft"
  }'
```

Python 스크립트로 마크다운 파일을 자동 변환·발행하려면:

```bash
python3 wp-blog-publisher-skill/scripts/publish.py \
  blog-post.md \
  https://내이름.up.railway.app \
  내계정 \
  "xxxx xxxx xxxx xxxx xxxx xxxx" \
  --draft
```

---

## 트러블슈팅 의사결정 트리

```
사이트 접속 불가?
  ├─ 배포 로그에 "More than one MPM loaded" → Step 2 (Custom Start Command)
  └─ 다른 오류 → Railway 배포 로그 확인

사이트는 뜨지만 API 인증 실패 (401)?
  ├─ Application Password를 발급했나?
  │   ├─ 안 했다 → Step 4 (발급)
  │   └─ 했다 → 로그인 비밀번호를 쓰고 있진 않은지 확인
  │       ├─ 로그인 비밀번호 사용 중 → App Password로 교체
  │       └─ App Password 맞는데도 401 → Step 6 (Apache 헤더 문제)
  │           ├─ Start Command 수정 가능 → 방법 A
  │           ├─ Administrator 계정 있음 → 방법 B (플러그인)
  │           └─ 둘 다 불가 → 방법 C (Cookie + Nonce)
  └─ 403 에러?
      ├─ rest_forbidden → 사용자 역할 확인 (Editor 이상 필요)
      └─ rest_cookie_invalid_nonce → Nonce 재추출
```
