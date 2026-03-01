---
name: wp-blog-publisher
version: 2.0.0
description: 소스 문서(옵시디언/마크다운)를 SEO·AEO 최적화 블로그 포스트로 변환하고, 구텐베르크 블록으로 워드프레스에 자동 게시하는 End-to-End 스킬
tags: [wordpress, seo, aeo, blog, gutenberg, publishing, obsidian]
author: conanssam
license: MIT
triggers: ["블로그 올려", "워드프레스 게시", "블로그 포스트 작성", "wp publish", "blog post"]
user-invocable: true
category: content-publishing
---

# WP Blog Publisher — SEO/AEO 최적화 블로그 자동 게시

소스 문서 하나를 입력받아 **SEO·AEO 최적화 블로그 포스트**로 변환하고, 구텐베르크 블록 형식으로 **워드프레스에 자동 게시**하는 End-to-End 스킬입니다.

## 이 스킬이 하는 일

```
소스 문서 → SEO 분석 → 콘텐츠 작성 → 이미지 매핑 → 구텐베르크 변환 → WP 게시 → 검증
(옵시디언/MD)   (메타 설계)  (타깃 독자용)   (원본 보존)    (블록 변환)     (REST API)   (렌더링 확인)
```

## 사용 시점

| Best Fit | Not a Fit |
|----------|-----------|
| 옵시디언 노트를 블로그 글로 변환 | 워드프레스 테마/플러그인 개발 |
| 기술 문서를 비전공자용 글로 재작성 | 이커머스 상품 페이지 |
| SEO/AEO 최적화가 필요한 콘텐츠 | 랜딩 페이지/세일즈 카피 |
| 이미지가 포함된 원본을 그대로 활용 | 멀티사이트 대량 게시 |

## 사용법

```
사용자: "이 옵시디언 노트를 블로그에 올려줘 [파일 경로]"
사용자: "이 마크다운을 워드프레스에 게시해줘 [URL]"
사용자: "[주제]에 대한 블로그 글을 써서 워드프레스에 올려줘"
```

**필수 입력:**
- 소스 문서 경로 (옵시디언 .md 또는 마크다운 파일)
- 워드프레스 접속 정보: URL, 계정명, Application Password
  - `scripts/.env` 파일에 미리 설정하면 매번 입력하지 않아도 됨 (권장)
  - `.env.example` 복사 후 편집: `cp scripts/.env.example scripts/.env`

**선택 입력 (미입력 시 자동 결정):**
- 타깃 독자 (기본: 블로그 초보자)
- 포스트 유형 (기본: How-To Guide)
- 게시 상태 (기본: publish, 옵션: draft)

---

## 워크플로우 (7단계)

### Step 1. 소스 분석

소스 문서를 읽고 다음을 추출한다:

- **핵심 주제**: 문서의 메인 토픽과 서브 토픽
- **이미지 목록**: 모든 `![alt](url)` 패턴의 이미지 URL과 캡션
- **구조 파악**: 헤딩 계층, 목록, 표, 코드 블록 등
- **원본 출처**: 저자, 날짜, 원본 링크

```
분석 결과 예시:
- 주제: 오픈소스 LLM 10종 비교
- 이미지: 37개 (Substack CDN URL)
- 구조: H2 x 12, H3 x 10, 표 x 5, 코드블록 x 3
- 출처: Sebastian Raschka, 2026-02-28
```

### Step 2. SEO 메타 설계

아래 메타 정보를 블로그 포스트 상단에 테이블로 작성한다:

```markdown
**SEO 메타 정보**

| 항목 | 내용 |
|------|------|
| **Title (H1)** | [60자 이내, Primary Keyword 포함] |
| **Meta Description** | [155자 이내, CTA 포함] |
| **URL Slug** | `[keyword-based-slug]` (불용어 제거, 하이픈 연결) |
| **Schema Markup** | `Article` (BlogPosting) + `FAQPage` |
| **Primary Keyword** | [메인 키워드] |
| **Secondary Keywords** | [2-4개 보조 키워드] |
| **Tags** | [5-10개, 쉼표 구분] |
| **Category** | [카테고리명] |
| **Word Count Target** | 1500-2000단어 |
| **Post Type** | [How-To Guide / Listicle / Tutorial / Review] |
```

**SEO 메타 규칙:**

| 항목 | 규칙 |
|------|------|
| Title | 60자 이내. Primary Keyword를 앞쪽에 배치 |
| Meta Description | 155자 이내. 키워드 + 독자 혜택 + CTA 포함 |
| URL Slug | 영문 소문자, 하이픈 연결, 불용어(the/a/and) 제거 |
| Schema | Article(BlogPosting) 필수. FAQ 있으면 FAQPage 추가 |

### Step 3. 콘텐츠 작성

소스 문서를 타깃 독자에 맞게 재작성한다.

#### 글쓰기 톤 & 스타일

```
- 문체: 존댓말 (합니다/입니다체)
- 톤: 친근하지만 전문적
- 비유: 전문 용어마다 일상 비유 1개 이상
- 문장 길이: 20-30자 (짧게)
- 단락 길이: 3-5문장
```

#### 필수 구조

```markdown
# [H1 제목 - Primary Keyword 포함]

[도입부: 공감형 질문 또는 흥미 유발 → 글의 약속 → 핵심 가치 제시]
[첫 100단어 내에 Primary Keyword 포함 필수]

[인트로 이미지 - 원본에서 가장 종합적인 그림]

---

## [H2 - 키워드 포함] 개념 설명 섹션
[전문 용어를 비전공자가 이해할 수 있게 풀어서 설명]

> **비전공자를 위한 용어 설명:** [핵심 용어 간단 설명]

---

## [H2 - 키워드 포함] 본론 섹션
[각 항목을 ### H3로 구분]
[항목마다: 핵심 스펙 → 특징 설명 → 왜 중요한지]
[관련 이미지 배치]

---

## [H2 - 키워드 포함] 실용 가이드 섹션
[추천 표 또는 체크포인트 목록]
[선택 기준 이미지]

---

## [H2 - 키워드 포함] 트렌드/결론 섹션
[3개 핵심 요약]
[CTA: 다음 행동 제안]

---

## 자주 묻는 질문 (FAQ)
[Q&A 3개 이상 — AEO 트리거]

---

## About the Author
[저자 소개 2-3문장. E-E-A-T 신호]
```

#### 키워드 배치 규칙

| 위치 | 규칙 |
|------|------|
| H1 제목 | Primary Keyword 반드시 포함 |
| 첫 100단어 | Primary Keyword 1회 이상 |
| H2 헤딩 | 2개 이상의 H2에 키워드 포함 |
| 본문 | 키워드 밀도 1-2% (자연스럽게) |
| Meta Description | Primary Keyword 포함 |
| URL Slug | Primary Keyword 기반 |
| 이미지 Alt Text | 키워드 + 설명 조합 |

#### AEO (Answer Engine Optimization) 규칙

AI 검색엔진(ChatGPT, Perplexity, Google AI Overview)에 최적화한다:

```
1. FAQ 섹션 필수 (3개 이상 Q&A)
   - Q는 **Q:** 로 볼드 처리
   - A는 첫 문장에 직접 답변 (2-3줄로 완결)
   - 자연어 질문형 ("~할 수 있나요?", "~의 차이가 뭔가요?")

2. 정의형 문장 포함
   - "[주제]란 ~하는 것입니다" 패턴
   - 글 초반에 배치 (AI 크롤러가 우선 인덱싱)

3. 구조화된 비교 표
   - | 항목 | 옵션A | 옵션B | 형태
   - 수치/스펙 비교에 적극 활용

4. E-E-A-T 신호
   - About the Author 섹션 필수
   - 원본 출처 링크 포함
   - 전문적 분석 + 실용적 조언 균형
```

### Step 4. 이미지 매핑

**핵심 원칙: 원본 이미지를 절대 버리지 않는다.**

```
규칙 1: 소스 문서의 모든 이미지 URL을 수집한다
규칙 2: 블로그 글의 각 섹션에 가장 관련 있는 이미지를 매핑한다
규칙 3: [이미지: 설명] 플레이스홀더를 절대 사용하지 않는다
규칙 4: 모든 이미지에 한국어 SEO alt text를 작성한다
규칙 5: 이미지 아래에 *Figure N: 캡션 (출처: 원본 저자)* 형식의 캡션을 단다
```

**이미지 매핑 전략:**

| 블로그 위치 | 이미지 선택 기준 |
|-------------|------------------|
| 인트로 (H1 아래) | 전체를 한눈에 보여주는 종합 차트/인포그래픽 |
| 각 항목 섹션 (H3) | 해당 항목의 아키텍처 다이어그램 또는 벤치마크 차트 |
| 비교/추천 섹션 | 비교 표 또는 종합 순위 차트 |
| 결론 | 트렌드 요약 차트 (있는 경우) |

**Alt Text 작성 공식:**

```
[주제/대상] + [무엇을 보여주는지] + [핵심 정보]
예: "GLM-5 아키텍처와 벤치마크 성능 비교"
예: "Qwen3.5와 Qwen3-Next 하이브리드 어텐션 구조 다이어그램"
```

**마크다운 형식:**

```markdown
![한국어 SEO alt text](https://원본이미지URL)
*Figure N: 한국어 캡션 설명 (출처: 원본 저자명)*
```

### Step 5. 구텐베르크 변환

마크다운을 워드프레스 구텐베르크 블록 형식으로 변환한다.

**변환 매핑표:**

| 마크다운 | 구텐베르크 블록 | 주의사항 |
|----------|----------------|----------|
| `## 제목` | `wp:heading` | `<h2 class="wp-block-heading">` |
| `### 제목` | `wp:heading {"level":3}` | `<h3 class="wp-block-heading">` |
| 일반 텍스트 | `wp:paragraph` | `<p>` 태그로 감싼다 |
| `**볼드**` | `<strong>` | 인라인 변환 |
| `*이탤릭*` | `<em>` | 인라인 변환 |
| `` `코드` `` | `<code>` | 인라인 변환 |
| `~~취소선~~` | `<s>` | 인라인 변환 |
| `[텍스트](URL)` | `<a href="URL">` | 인라인 변환 |
| `![alt](url)` | `wp:image` | **`<figure>` 래퍼 필수** |
| `\| 표 \|` | `wp:table` | **`<figure class="wp-block-table">` 래퍼 필수** |
| `- 항목` | `wp:list` | `<ul class="wp-block-list">` |
| `1. 항목` | `wp:list {"ordered":true}` | `<ol class="wp-block-list">` |
| `> 인용` | `wp:quote` | `<blockquote class="wp-block-quote">` |
| ` ```코드블록``` ` | `wp:code` | `<pre class="wp-block-code"><code>` |
| `---` | `wp:separator` | `<hr class="wp-block-separator"/>` |

**블록 구조 (모든 블록의 공통 패턴):**

```html
<!-- wp:block-name {"attribute":"value"} -->
<html-element class="wp-block-name">콘텐츠</html-element>
<!-- /wp:block-name -->
```

**이미지 블록 (캡션 포함):**

```html
<!-- wp:image {"sizeSlug":"large","linkDestination":"none"} -->
<figure class="wp-block-image size-large">
  <img src="https://이미지URL" alt="SEO alt text"/>
  <figcaption class="wp-element-caption">Figure N: 캡션 (출처: 저자)</figcaption>
</figure>
<!-- /wp:image -->
```

**표 블록 (figure 래퍼 누락 시 렌더링 실패):**

```html
<!-- wp:table -->
<figure class="wp-block-table"><table>
  <thead><tr><th>헤더1</th><th>헤더2</th></tr></thead>
  <tbody><tr><td>데이터1</td><td>데이터2</td></tr></tbody>
</table></figure>
<!-- /wp:table -->
```

**변환 시 제외 항목:**
- SEO 메타 테이블 → 포스트 메타데이터로 분리
- H1 제목 → 포스트 title 필드로 분리
- HTML 주석 (체크리스트 등) → 제거
- `<!-- 내부 링크 제안 -->` 주석 → 제거

### Step 6. 워드프레스 게시

#### 인증 방식 (우선순위)

```
1순위: Application Password (Basic Auth)
       Authorization: Basic base64(user:app_password)

2순위: Cookie + Nonce (Application Password 불가 시)
       1) POST /wp-login.php 로 로그인
       2) GET /wp-admin/post-new.php 에서 wpApiSettings.nonce 추출
       3) X-WP-Nonce 헤더로 REST API 호출

3순위: JWT Token
       Authorization: Bearer {jwt_token}
```

#### Cookie + Nonce 인증 (Railway 등 리버스 프록시 환경)

일부 호스팅(Railway, Heroku 등)에서 `Authorization` 헤더가 차단되는 경우 Cookie + Nonce 방식으로 우회한다. `scripts/publish.py`가 Basic Auth 실패 시 자동으로 이 방식으로 전환한다.

> 인증 우회 코드 전문은 `scripts/publish.py`의 `try_cookie_auth()` 함수 참조.

#### REST API 게시

`scripts/publish.py`가 카테고리/태그 생성·조회, 포스트 생성을 순서대로 처리한다. 게시 데이터 구조:

```
title    → SEO 메타의 Title (H1)
content  → 구텐베르크 블록 HTML
status   → publish | draft
categories → [cat_id]
tags     → [tag_id, ...]
excerpt  → Meta Description
slug     → URL Slug
```

### Step 7. 검증

게시 후 반드시 확인한다:

```
1. URL 접근 → HTTP 200 확인
2. 제목 정상 표시
3. 이미지 로딩 확인 (깨진 이미지 없는지)
4. 표(table) 정상 렌더링
5. H2/H3 헤딩 구조 확인
6. FAQ 섹션 정상 표시
7. 링크 클릭 가능 확인
```

---

## 사전 게시 체크리스트 (11항목)

게시 전 반드시 모든 항목을 확인한다:

```
[ ] 1. H1 제목에 Primary Keyword 포함
[ ] 2. 첫 100단어 내에 Primary Keyword 포함
[ ] 3. H2 헤딩 2개 이상에 키워드 포함
[ ] 4. Meta Description 155자 이내
[ ] 5. URL Slug: 키워드 기반, 불용어 제거
[ ] 6. 내부 링크 1개 이상 제안 위치 표시
[ ] 7. 외부 링크 1개 이상 (원본 출처 등)
[ ] 8. 모든 이미지에 SEO alt text 포함
[ ] 9. 1200단어 이상
[ ] 10. AEO 트리거 3개 이상 (FAQ Q&A 형식)
[ ] 11. Schema Markup 타입 지정 (Article + FAQPage)
```

---

## 설정

### .env 파일 (권장)

`scripts/.env.example`을 복사하여 `scripts/.env`로 사용한다:

```bash
cp scripts/.env.example scripts/.env
# .env 편집 후 사용
```

```bash
# scripts/.env
WP_URL=https://your-site.up.railway.app
WP_USER=your-wp-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
WP_POST_STATUS=publish
```

**.env 설정 시 인자 없이 실행 가능:**

```bash
# .env가 있으면 파일 경로만 지정
python3 scripts/publish.py blog-post.md

# --draft로 임시저장
python3 scripts/publish.py blog-post.md --draft
```

**인자 우선순위:** 명령줄 옵션 `--url` > 위치 인자 > 환경 변수 (.env)

| 환경 변수 | 설명 | 필수 |
|-----------|------|------|
| `WP_URL` | 워드프레스 사이트 URL | 필수 |
| `WP_USER` | 워드프레스 계정명 | 필수 |
| `WP_APP_PASSWORD` | Application Password (**로그인 비밀번호 아님**) | 필수 |
| `WP_POST_STATUS` | `publish` 또는 `draft` | 선택 (기본: publish) |

> **.env 파일은 절대 Git에 커밋하지 않는다.** `scripts/.gitignore`에 `.env`가 이미 등록되어 있다.

### 사용자에게 물어볼 것

| 질문 | 필수 | 기본값 |
|------|------|--------|
| 워드프레스 사이트 URL | 필수 | - |
| 사용자명 | 필수 | - |
| Application Password | 필수 | - |
| 타깃 독자 | 선택 | 블로그 초보자 |
| 포스트 유형 | 선택 | How-To Guide |
| 게시 상태 (publish/draft) | 선택 | publish |

---

## 포스트 유형별 구조 가이드

### How-To Guide

```
H1: [주제] 완벽 가이드
├── H2: [주제]란? 왜 지금 주목해야 할까
├── H2: [주제] 핵심 비교/분석
│   ├── H3: 항목 1
│   ├── H3: 항목 2
│   └── H3: 항목 N
├── H2: 나에게 맞는 [주제] 선택 방법
├── H2: [주제] 트렌드/향후 방향
├── H2: 결론 (3개 핵심 요약)
├── H2: 자주 묻는 질문 (FAQ)
└── H2: About the Author
```

### Listicle

```
H1: [연도/시기] [주제] N선 추천
├── H2: 선정 기준
├── H2: [주제] N선 상세 리뷰
│   ├── H3: 1위. [항목명] - [한줄 특징]
│   ├── H3: 2위. [항목명] - [한줄 특징]
│   └── H3: N위. [항목명] - [한줄 특징]
├── H2: 비교 표
├── H2: 결론
├── H2: FAQ
└── H2: About the Author
```

### Tutorial

```
H1: [목표] 하는 방법: 단계별 튜토리얼
├── H2: 시작 전 준비물
├── H2: Step 1. [첫 번째 단계]
├── H2: Step 2. [두 번째 단계]
├── H2: Step N. [마지막 단계]
├── H2: 문제 해결 (트러블슈팅)
├── H2: 결론
├── H2: FAQ
└── H2: About the Author
```

---

## 인라인 마크다운 → HTML 변환 규칙

```python
# 변환 순서 (순서 중요)
1. **bold**    → <strong>bold</strong>
2. *italic*    → <em>italic</em>
3. `code`      → <code>code</code>
4. ~~text~~    → <s>text</s>
5. [text](url) → <a href="url">text</a>
```

---

## Railway 워드프레스 환경 셋업

Railway WordPress 프리셋 배포 시 자주 발생하는 문제 요약. 전체 단계별 가이드는 `references/railway-wp-setup.md` 참조.

### 자주 겪는 2가지 문제

| 문제 | 증상 | 원인 |
|------|------|------|
| **Apache MPM 충돌** | 배포 로그 `AH00534: More than one MPM loaded.` 반복, 재시작 루프 | Docker 이미지에 MPM 모듈 2개 이상 포함 |
| **Authorization 헤더 차단** | Basic Auth 시 401 `rest_not_logged_in` | Apache가 `Authorization` 헤더를 PHP로 미전달 |

### 해결: Custom Start Command (두 문제 동시 해결)

Railway → 서비스 → Settings → **Custom Start Command**:

```bash
bash -c "a2dismod mpm_event mpm_worker || true; a2enmod mpm_prefork rewrite || true; printf '%s\n' 'SetEnvIfNoCase Authorization \"^(.*)\" HTTP_AUTHORIZATION=$1' > /etc/apache2/conf-available/auth-header.conf; a2enconf auth-header || true; docker-entrypoint.sh apache2-foreground"
```

### Application Password 발급 (필수)

REST API 인증에는 **Application Password**가 필요하다. 워드프레스 로그인 비밀번호는 사용 불가.

```
발급: 관리자 페이지 → 사용자 → 프로필 → Application Passwords 섹션
형식: xxxx xxxx xxxx xxxx xxxx xxxx (한 번만 표시됨)
```

> Application Password 이름(라벨)을 아이디로 착각하지 말 것. 인증 아이디는 항상 워드프레스 계정명.

### 인증 테스트

```bash
curl -u "계정명:xxxx xxxx xxxx xxxx xxxx xxxx" https://사이트/wp-json/wp/v2/users/me
# 200 → 성공 / 401 → Start Command 미적용 또는 App Password 미발급
```

> 플러그인 설치 방법, Cookie+Nonce 우회, 전체 트러블슈팅 트리는 `references/railway-wp-setup.md` 참조

---

## 에러 처리

| 에러 | 원인 | 해결 |
|------|------|------|
| 사이트 접속 불가 (재시작 루프) | Apache MPM 모듈 중복 로드 | Custom Start Command 적용 |
| 401 rest_not_logged_in | Authorization 헤더 차단 또는 App Password 미발급 | Start Command + App Password 발급 |
| 401 (로그인 비밀번호 사용) | Application Password가 아닌 로그인 비밀번호 사용 | 프로필에서 App Password 별도 발급 |
| 403 rest_cookie_invalid_nonce | Nonce 불일치 | `wpApiSettings.nonce`에서 재추출 |
| 403 rest_forbidden | 권한 부족 | 사용자 역할이 Editor 이상인지 확인 |
| 400 rest_invalid_param | 잘못된 파라미터 | 카테고리/태그 ID 유효성 확인 |
| 표 렌더링 실패 | `<figure>` 래퍼 누락 | `<figure class="wp-block-table">` 추가 |
| 이미지 깨짐 | 외부 URL 차단 | 이미지를 미디어 라이브러리에 업로드 후 URL 교체 |

---

## 보안 주의사항

```
1. 비밀번호를 코드/파일에 하드코딩하지 않는다
2. 환경 변수 또는 대화 중 일회성 입력으로 처리한다
3. Application Password 사용 시 최소 권한 원칙 적용
4. 게시 완료 후 세션 쿠키를 유지하지 않는다
5. .env 파일은 .gitignore에 반드시 추가한다
```

---

## 참고 문서

| 문서 | 위치 | 내용 |
|------|------|------|
| Railway 워드프레스 셋업 가이드 | `references/railway-wp-setup.md` | 배포~API 인증까지 전체 과정 + 트러블슈팅 |
| 구텐베르크 블록 레퍼런스 | `references/gutenberg-blocks.md` | 전체 블록 타입별 HTML 구조 |
| 게시 스크립트 | `scripts/publish.py` | Basic Auth + Cookie+Nonce 인증 자동 게시 |
| SEO/AEO 전체 컨텍스트 | `WORDPRESS-SEO-AEO-CONTEXT.md` | 126섹션, 112코드블록의 종합 레퍼런스 |
