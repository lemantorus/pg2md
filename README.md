# pg2md

**HTML to Markdown converter** with Requests or Playwright backend.

Convert any webpage to clean Markdown. Choose between fast `requests` or full browser `playwright` for JavaScript-rendered pages.

## Features

- **Two backends**: `Pg2MdRequests` (fast) or `Pg2MdPlaywright` (JS support)
- **Browser reuse**: Playwright instances share a single browser
- **Proxy support**: HTTP/HTTPS proxies with authentication
- **Custom headers & cookies**: Full control over requests
- **Clean output**: Optional removal of images and links
- **Context manager**: Auto-cleanup with `with` statement

## Installation

```bash
pip install pg2md

# For Playwright backend:
pip install pg2md[playwright]
playwright install chromium
```

## Quick Start

```python
from pg2md import Pg2MdRequests, Pg2MdPlaywright

# Simple usage with Requests
pg = Pg2MdRequests()
markdown = pg.run("https://example.com")
print(markdown)

# Playwright for JS-heavy sites
pg = Pg2MdPlaywright()
markdown = pg.run("https://spa-example.com")
pg.close()
```

## Usage

### Basic Conversion

```python
from pg2md import Pg2MdRequests

pg = Pg2MdRequests(with_image=False, with_link=False)
md = pg.run("https://news.ycombinator.com")
```

### With Proxy

```python
from pg2md import Pg2MdRequests, Pg2MdPlaywright

# Format: http://user:password@host:port
# Or: host:port:user:password
proxy = "http://user:pass@proxy.example.com:8080"

# Requests
pg = Pg2MdRequests()
md = pg.run("https://example.com", proxy=proxy)

# Playwright
pg = Pg2MdPlaywright()
md = pg.run("https://example.com", proxy=proxy)
pg.close()
```

### Custom Headers & User-Agent

```python
from pg2md import Pg2MdRequests

pg = Pg2MdRequests()
md = pg.run(
    "https://api.example.com/data",
    headers={
        "X-API-Key": "secret123",
        "Accept": "application/json",
    },
    user_agent="MyBot/1.0",
)
```

### With Cookies

```python
from pg2md import Pg2MdRequests

pg = Pg2MdRequests()
md = pg.run(
    "https://example.com/dashboard",
    cookies={
        "session": "abc123",
        "auth_token": "xyz789",
    },
)
```

### Save to File

```python
from pg2md import Pg2MdRequests

pg = Pg2MdRequests()
pg.save("output.md", "https://example.com")

# With options
pg.save(
    "article.md",
    "https://blog.example.com/post",
    proxy="http://user:pass@host:port",
    user_agent="MyBot/1.0",
)
```

### Context Manager

```python
from pg2md import Pg2MdPlaywright

with Pg2MdPlaywright() as pg:
    md1 = pg.run("https://site1.com")
    md2 = pg.run("https://site2.com")
    # Browser closed automatically
```

### Multiple Instances

```python
from pg2md import Pg2MdPlaywright

# Both share the same browser (efficient)
pg1 = Pg2MdPlaywright()
pg2 = Pg2MdPlaywright()

md1 = pg1.run("https://site1.com")
md2 = pg2.run("https://site2.com")

Pg2MdPlaywright.close_all()  # Close shared browser
```

## API Reference

### Pg2MdRequests

```python
Pg2MdRequests(with_image=False, with_link=False)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `with_image` | bool | False | Include images in output |
| `with_link` | bool | False | Include links in output |

### Pg2MdPlaywright

```python
Pg2MdPlaywright(
    browser=None,       # Custom Browser instance
    headless=True,      # Headless mode
    with_image=False,
    with_link=False,
)
```

### Methods

#### `run(url, proxy=None, headers=None, cookies=None, user_agent=None, timeout=30)`

Fetch URL and convert to Markdown.

Returns: `str` (Markdown)

#### `fetch(url, proxy=None, headers=None, cookies=None, user_agent=None, timeout=30)`

Fetch HTML only.

Returns: `str` (HTML)

#### `convert(html)`

Convert HTML to Markdown.

Returns: `str` (Markdown)

#### `save(filepath, url, **kwargs)`

Fetch, convert, and save to file.

#### `close()`

Close browser (Playwright only).

#### `close_all()` (classmethod, Playwright only)

Close all shared browsers.

## When to Use Which Backend?

| Use Requests | Use Playwright |
|--------------|----------------|
| Static HTML pages | SPA / JavaScript apps |
| Speed matters | Need rendered content |
| Simple scraping | Bypass anti-bot (sometimes) |
| Low memory | Modern web apps |

## Examples

### Scrape Multiple URLs

```python
from pg2md import Pg2MdRequests

urls = [
    "https://blog.example.com/post1",
    "https://blog.example.com/post2",
    "https://blog.example.com/post3",
]

pg = Pg2MdRequests(with_image=False, with_link=False)

for i, url in enumerate(urls):
    pg.save(f"post_{i+1}.md", url)
    print(f"Saved: {url}")
```

### Batch with Proxies

```python
from pg2md import Pg2MdRequests

urls = ["https://site1.com", "https://site2.com", "https://site3.com"]
proxies = [
    "http://user1:pass1@proxy1:8080",
    "http://user2:pass2@proxy2:8080",
]

pg = Pg2MdRequests()

for i, url in enumerate(urls):
    proxy = proxies[i % len(proxies)]
    md = pg.run(url, proxy=proxy)
    print(f"[{i+1}] {len(md)} chars")
```

### Extract Article Content

```python
from pg2md import Pg2MdPlaywright

with Pg2MdPlaywright() as pg:
    md = pg.run(
        "https://medium.com/some-article",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    )
    
    # Save clean text
    with open("article.md", "w") as f:
        f.write(md)
```

## License

MIT
