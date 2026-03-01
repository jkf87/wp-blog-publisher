# 구텐베르크 블록 레퍼런스

워드프레스 구텐베르크 에디터의 블록 HTML 구조 레퍼런스.
마크다운을 워드프레스 콘텐츠로 변환할 때 이 형식을 따른다.

---

## 공통 규칙

모든 블록은 아래 구조를 따른다:

```html
<!-- wp:block-name {"key":"value"} -->
<html-element>콘텐츠</html-element>
<!-- /wp:block-name -->
```

- 속성이 없으면 `{}` 생략 가능: `<!-- wp:paragraph -->`
- 블록 사이는 빈 줄 2개로 구분
- 블록 내 HTML은 인라인 스타일 미사용 (클래스만 사용)

---

## 블록별 구조

### Paragraph (문단)

```html
<!-- wp:paragraph -->
<p>일반 텍스트. <strong>볼드</strong>, <em>이탤릭</em>, <code>코드</code>, <a href="https://url">링크</a> 가능.</p>
<!-- /wp:paragraph -->
```

### Heading (제목)

```html
<!-- wp:heading -->
<h2 class="wp-block-heading">H2 제목 (기본)</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">H3 제목</h3>
<!-- /wp:heading -->

<!-- wp:heading {"level":4} -->
<h4 class="wp-block-heading">H4 제목</h4>
<!-- /wp:heading -->
```

H1은 사용하지 않는다 (포스트 title로 처리).

### Image (이미지)

**캡션 없이:**
```html
<!-- wp:image {"sizeSlug":"large","linkDestination":"none"} -->
<figure class="wp-block-image size-large">
  <img src="https://example.com/image.jpg" alt="SEO 최적화된 대체 텍스트"/>
</figure>
<!-- /wp:image -->
```

**캡션 포함:**
```html
<!-- wp:image {"sizeSlug":"large","linkDestination":"none"} -->
<figure class="wp-block-image size-large">
  <img src="https://example.com/image.jpg" alt="SEO 최적화된 대체 텍스트"/>
  <figcaption class="wp-element-caption">Figure 1: 캡션 텍스트 (출처: 저자명)</figcaption>
</figure>
<!-- /wp:image -->
```

### Table (표)

**반드시 `<figure class="wp-block-table">` 래퍼를 포함해야 한다. 누락 시 렌더링 실패.**

```html
<!-- wp:table -->
<figure class="wp-block-table"><table>
  <thead>
    <tr><th>헤더1</th><th>헤더2</th><th>헤더3</th></tr>
  </thead>
  <tbody>
    <tr><td>데이터1</td><td>데이터2</td><td>데이터3</td></tr>
    <tr><td>데이터4</td><td>데이터5</td><td>데이터6</td></tr>
  </tbody>
</table></figure>
<!-- /wp:table -->
```

**스트라이프 스타일:**
```html
<!-- wp:table {"hasFixedLayout":true,"className":"is-style-stripes"} -->
```

### List (목록)

**비순서 목록:**
```html
<!-- wp:list -->
<ul class="wp-block-list"><li>항목 1</li><li>항목 2</li><li>항목 3</li></ul>
<!-- /wp:list -->
```

**순서 목록:**
```html
<!-- wp:list {"ordered":true} -->
<ol class="wp-block-list"><li>첫째</li><li>둘째</li><li>셋째</li></ol>
<!-- /wp:list -->
```

### Quote (인용)

```html
<!-- wp:quote -->
<blockquote class="wp-block-quote"><p>인용 텍스트.</p></blockquote>
<!-- /wp:quote -->
```

**출처 포함:**
```html
<!-- wp:quote -->
<blockquote class="wp-block-quote">
  <p>인용 텍스트.</p>
  <cite>출처</cite>
</blockquote>
<!-- /wp:quote -->
```

### Separator (구분선)

```html
<!-- wp:separator -->
<hr class="wp-block-separator has-alpha-channel-opacity"/>
<!-- /wp:separator -->
```

### Code Block (코드)

```html
<!-- wp:code -->
<pre class="wp-block-code"><code>코드 내용</code></pre>
<!-- /wp:code -->
```

**언어 지정:**
```html
<!-- wp:code {"language":"python"} -->
<pre class="wp-block-code"><code lang="python">def hello():
    print("Hello")</code></pre>
<!-- /wp:code -->
```

### Columns (컬럼 레이아웃)

```html
<!-- wp:columns -->
<div class="wp-block-columns">
  <!-- wp:column -->
  <div class="wp-block-column">
    <!-- wp:paragraph -->
    <p>왼쪽 컬럼</p>
    <!-- /wp:paragraph -->
  </div>
  <!-- /wp:column -->
  <!-- wp:column -->
  <div class="wp-block-column">
    <!-- wp:paragraph -->
    <p>오른쪽 컬럼</p>
    <!-- /wp:paragraph -->
  </div>
  <!-- /wp:column -->
</div>
<!-- /wp:columns -->
```

### Button (버튼)

```html
<!-- wp:buttons -->
<div class="wp-block-buttons">
  <!-- wp:button -->
  <div class="wp-block-button">
    <a class="wp-block-button__link wp-element-button" href="https://url">버튼 텍스트</a>
  </div>
  <!-- /wp:button -->
</div>
<!-- /wp:buttons -->
```

---

## 인라인 HTML 변환

| 마크다운 | HTML | 비고 |
|----------|------|------|
| `**bold**` | `<strong>bold</strong>` | |
| `*italic*` | `<em>italic</em>` | |
| `` `code` `` | `<code>code</code>` | |
| `[text](url)` | `<a href="url">text</a>` | |
| `~~삭제~~` | `<s>삭제</s>` | |

---

## 주의사항

1. **표의 `<figure>` 래퍼**: 반드시 `<figure class="wp-block-table">` 로 감싼다
2. **이미지의 `<figure>` 래퍼**: 반드시 `<figure class="wp-block-image">` 로 감싼다
3. **H1 미사용**: 포스트 title이 H1 역할. 본문은 H2부터 시작
4. **블록 간 구분**: `\n\n` 두 줄로 구분
5. **HTML 엔티티**: `<` `>` `&`는 텍스트 내에서 이스케이프 불필요 (구텐베르크가 처리)
6. **SEO 메타 블록**: 게시 콘텐츠에 포함하지 않음 (API 필드로 분리)
