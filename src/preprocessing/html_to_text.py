"""HTML to text / markdown conversion with code block preservation."""

from __future__ import annotations

import re

from src.loaders.base import LoadedDocument


class HtmlToTextConverter:
    """Convert HTML documents to plain text while preserving structure hints."""

    CODE_BLOCK_PATTERN = re.compile(r"<pre[^>]*><code[^>]*>(.*?)</code></pre>", re.DOTALL | re.IGNORECASE)
    HEADER_PATTERN = re.compile(r"<h([1-6])[^>]*>(.*?)</h\1>", re.DOTALL | re.IGNORECASE)

    def convert(self, document: LoadedDocument) -> LoadedDocument:
        if document.doc_type != "html":
            return document

        text = document.content
        text = self._preserve_code_blocks(text)
        text = self._convert_headers(text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return LoadedDocument(
            source_url=document.source_url,
            title=document.title,
            content=text,
            doc_type="text",
            raw_path=document.raw_path,
            last_updated=document.last_updated,
            metadata=document.metadata,
        )

    def _preserve_code_blocks(self, html: str) -> str:
        def replacer(match: re.Match[str]) -> str:
            code = match.group(1)
            code = re.sub(r"<[^>]+>", "", code)
            return f"\n```\n{code.strip()}\n```\n"

        return self.CODE_BLOCK_PATTERN.sub(replacer, html)

    def _convert_headers(self, html: str) -> str:
        def replacer(match: re.Match[str]) -> str:
            level = int(match.group(1))
            text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            return f"\n{'#' * level} {text}\n"

        return self.HEADER_PATTERN.sub(replacer, html)
