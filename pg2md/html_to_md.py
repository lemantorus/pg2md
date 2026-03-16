"""
HtmlToMarkdown — standalone HTML to Markdown converter.

No browser dependencies, just HTML -> Markdown conversion.

Dependencies:
    pip install html-to-markdown beautifulsoup4

Usage:
    converter = HtmlToMarkdown(with_image=False, with_link=False)
    markdown = converter.convert(html_string)
"""

import re
from typing import Optional

from bs4 import BeautifulSoup
from html_to_markdown import convert, ConversionOptions, PreprocessingOptions


class HtmlToMarkdown:
    """
    Converts HTML to clean Markdown.

    Steps:
        1. Clean HTML (remove scripts, styles, optional images/links)
        2. Convert to Markdown via html-to-markdown
        3. Clean final Markdown (remove base64, excess newlines)

    Args:
        with_image: Include images in output. Default False.
        with_link: Include links (href). Default True.
                   False — links are replaced with their text.
        heading_style: "atx" (#) or "setext" (underline). Default "atx".
        strong_em_symbol: "*" or "_". Default "*".
        bullets: Bullet character. Default "*".
        escape_asterisks: Escape asterisks in text. Default False.
        preprocessing_preset: "aggressive", "moderate", or "conservative". Default "aggressive".
        remove_navigation: Remove navigation elements. Default True.
        remove_forms: Remove form elements. Default True.
    """

    STRIP_TAGS = [
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "video",
        "audio",
        "iframe",
        "object",
        "embed",
        "head",
    ]

    _BASE64_LINE = re.compile(r"^[A-Za-z0-9+/=]{40,}\s*$", re.MULTILINE)
    _BINARY_GARBAGE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
    _EXCESS_NEWLINES = re.compile(r"\n{3,}")
    _MD_IMAGE = re.compile(r"!\[.*?\]\(.*?\)")

    def __init__(
        self,
        with_image: bool = False,
        with_link: bool = True,
        heading_style: str = "atx",
        strong_em_symbol: str = "*",
        bullets: str = "*",
        escape_asterisks: bool = False,
        preprocessing_preset: str = "aggressive",
        remove_navigation: bool = True,
        remove_forms: bool = True,
    ):
        self.with_image = with_image
        self.with_link = with_link
        self.heading_style = heading_style
        self.strong_em_symbol = strong_em_symbol
        self.bullets = bullets
        self.escape_asterisks = escape_asterisks
        self.preprocessing_preset = preprocessing_preset
        self.remove_navigation = remove_navigation
        self.remove_forms = remove_forms

    def convert(self, html: str) -> str:
        """
        Convert HTML to clean Markdown.

        Args:
            html: HTML string

        Returns:
            Clean Markdown string
        """
        clean_html = self._clean_html(html)
        markdown = self._html_to_markdown_lib(clean_html)
        markdown = self._clean_markdown(markdown)
        return markdown

    def _clean_html(self, html: str) -> str:
        """Remove unwanted tags and attributes from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        for tag in self.STRIP_TAGS:
            for el in soup.find_all(tag):
                el.decompose()

        if not self.with_image:
            for el in soup.find_all("img"):
                el.decompose()
        else:
            for el in soup.find_all("img"):
                src = el.get("src", "")
                if isinstance(src, str) and (src.startswith("data:") or src.startswith("blob:")):
                    el.decompose()

        if not self.with_link:
            for el in soup.find_all("a"):
                el.replace_with(el.get_text())
        else:
            for el in soup.find_all("a"):
                href = el.get("href", "")
                if isinstance(href, str) and (href.startswith("data:") or href.startswith("blob:")):
                    el["href"] = ""

        for el in soup.find_all(True):
            for attr in ("src", "href", "srcset", "poster", "background"):
                val = el.get(attr, "")
                if isinstance(val, str) and (val.startswith("data:") or val.startswith("blob:")):
                    del el[attr]

        return str(soup)

    def _html_to_markdown_lib(self, html: str) -> str:
        """Convert HTML to Markdown using html-to-markdown library."""
        options = ConversionOptions(
            heading_style=self.heading_style,
            strong_em_symbol=self.strong_em_symbol,
            bullets=self.bullets,
            escape_asterisks=self.escape_asterisks,
        )
        preprocessing = PreprocessingOptions(
            enabled=True,
            preset=self.preprocessing_preset,
            remove_navigation=self.remove_navigation,
            remove_forms=self.remove_forms,
        )
        return convert(html, options, preprocessing)

    def _clean_markdown(self, text: str) -> str:
        """Final cleanup of Markdown text."""
        text = self._BINARY_GARBAGE.sub("", text)
        text = self._BASE64_LINE.sub("", text)

        if not self.with_image:
            text = self._MD_IMAGE.sub("", text)

        text = self._EXCESS_NEWLINES.sub("\n\n", text)

        return text.strip()


if __name__ == "__main__":
    import sys

    html = sys.stdin.read() if not sys.argv[1:] else open(sys.argv[1]).read()

    converter = HtmlToMarkdown(with_image=False, with_link=False)
    print(converter.convert(html))
