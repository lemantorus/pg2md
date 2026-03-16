"""
Pg2Md — HTML to Markdown converter with Requests or Playwright backend.

Usage:
    from pg2md import Pg2MdRequests, Pg2MdPlaywright

    # Requests
    pg = Pg2MdRequests(with_image=False, with_link=False)
    md = pg.run("https://example.com", proxy="http://user:pass@host:port")

    # Playwright
    pg = Pg2MdPlaywright()
    md = pg.run("https://example.com")
    pg.close()
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from requests import Session
from playwright.sync_api import sync_playwright, Browser

from .html_to_md import HtmlToMarkdown


class Pg2Md(ABC):
    """Base class for HTML to Markdown conversion."""

    def __init__(self, with_image: bool = False, with_link: bool = False):
        self._converter = HtmlToMarkdown(
            with_image=with_image,
            with_link=with_link,
        )

    @abstractmethod
    def fetch(
        self,
        url: str,
        proxy: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        user_agent: Optional[str] = None,
        timeout: int = 30,
    ) -> str:
        """Fetch HTML from URL."""
        ...

    def convert(self, html: str) -> str:
        """Convert HTML to Markdown."""
        return self._converter.convert(html)

    def run(
        self,
        url: str,
        proxy: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        user_agent: Optional[str] = None,
        timeout: int = 30,
    ) -> str:
        """Fetch URL and convert to Markdown."""
        html = self.fetch(url, proxy, headers, cookies, user_agent, timeout)
        return self.convert(html)

    def save(
        self,
        filepath: str,
        url: str,
        proxy: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        user_agent: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """Fetch, convert and save to file."""
        md = self.run(url, proxy, headers, cookies, user_agent, timeout)
        Path(filepath).write_text(md, encoding="utf-8")

    def close(self):
        """Close resources. Override in subclasses if needed."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class Pg2MdRequests(Pg2Md):
    """Requests-based implementation."""

    def fetch(
        self,
        url: str,
        proxy: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        user_agent: Optional[str] = None,
        timeout: int = 30,
    ) -> str:
        session = Session()

        final_headers = dict(headers) if headers else {}
        if user_agent:
            final_headers["User-Agent"] = user_agent

        proxies = None
        if proxy:
            proxy_url = self._normalize_proxy(proxy)
            proxies = {"http": proxy_url, "https": proxy_url}

        resp = session.get(
            url,
            proxies=proxies,
            headers=final_headers if final_headers else None,
            cookies=cookies,
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.text

    def _normalize_proxy(self, proxy: str) -> str:
        """Normalize proxy to http://user:pass@host:port format."""
        if proxy.startswith("http://") or proxy.startswith("https://"):
            return proxy

        parts = proxy.split(":")
        if len(parts) == 4:
            host, port, user, password = parts
            return f"http://{user}:{password}@{host}:{port}"

        return f"http://{proxy}"


class Pg2MdPlaywright(Pg2Md):
    """Playwright-based implementation with browser reuse."""

    _shared_playwright = None
    _shared_browsers: dict = {}

    def __init__(
        self,
        browser: Optional[Browser] = None,
        headless: bool = True,
        with_image: bool = False,
        with_link: bool = False,
    ):
        super().__init__(with_image, with_link)
        self._browser = browser
        self._headless = headless
        self._owns_browser = browser is None

    @classmethod
    def _get_playwright(cls):
        if cls._shared_playwright is None:
            cls._shared_playwright = sync_playwright().start()
        return cls._shared_playwright

    @property
    def browser(self) -> Browser:
        """Get or create browser instance."""
        if self._browser is None:
            key = ("chromium", self._headless)
            if key not in self._shared_browsers:
                pw = self._get_playwright()
                self._shared_browsers[key] = pw.chromium.launch(headless=self._headless)
            self._browser = self._shared_browsers[key]
        return self._browser

    def fetch(
        self,
        url: str,
        proxy: Optional[str] = None,
        headers: Optional[dict] = None,
        cookies: Optional[dict] = None,
        user_agent: Optional[str] = None,
        timeout: int = 30,
    ) -> str:
        context_opts = {}

        if proxy:
            context_opts["proxy"] = self._parse_proxy(proxy)
        if user_agent:
            context_opts["user_agent"] = user_agent

        context = self.browser.new_context(**context_opts)

        if headers:
            context.set_extra_http_headers(headers)
        if cookies:
            parsed_url = urlparse(url)
            domain = parsed_url.hostname
            formatted_cookies = [
                {"name": k, "value": v, "domain": domain} for k, v in cookies.items()
            ]
            context.add_cookies(formatted_cookies)

        page = context.new_page()
        page.goto(url, timeout=timeout * 1000)
        html = page.content()

        page.close()
        context.close()

        return html

    def _parse_proxy(self, proxy: str) -> dict:
        """Parse proxy string to Playwright format."""
        if proxy.startswith("http://") or proxy.startswith("https://"):
            parsed = urlparse(proxy)
            result = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"}
            if parsed.username and parsed.password:
                result["username"] = parsed.username
                result["password"] = parsed.password
            return result

        parts = proxy.split(":")
        if len(parts) == 4:
            host, port, user, password = parts
            return {
                "server": f"http://{host}:{port}",
                "username": user,
                "password": password,
            }
        elif len(parts) == 2:
            host, port = parts
            return {"server": f"http://{host}:{port}"}

        return {"server": f"http://{proxy}"}

    def close(self):
        """Close browser if owned by this instance."""
        if self._owns_browser:
            key = ("chromium", self._headless)
            if key in self._shared_browsers:
                self._shared_browsers[key].close()
                del self._shared_browsers[key]
            self._browser = None

    @classmethod
    def close_all(cls):
        """Close all shared browsers and playwright."""
        for browser in cls._shared_browsers.values():
            browser.close()
        cls._shared_browsers.clear()
        if cls._shared_playwright:
            cls._shared_playwright.stop()
            cls._shared_playwright = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
