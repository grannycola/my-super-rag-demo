"""Document cleaning: deduplication, whitespace normalization."""

from __future__ import annotations

import hashlib
import re

from src.loaders.base import LoadedDocument
from src.preprocessing.html_to_text import HtmlToTextConverter


class DocumentCleaner:
    """Clean and normalize raw documents before chunking."""

    def __init__(self) -> None:
        self.html_converter = HtmlToTextConverter()

    def clean(self, documents: list[LoadedDocument]) -> list[LoadedDocument]:
        cleaned: list[LoadedDocument] = []
        seen_hashes: set[str] = set()

        for doc in documents:
            if doc.doc_type == "html":
                doc = self.html_converter.convert(doc)

            text = self._normalize_whitespace(doc.content)
            content_hash = hashlib.sha256(text.encode()).hexdigest()
            if content_hash in seen_hashes:
                continue
            seen_hashes.add(content_hash)

            cleaned.append(
                LoadedDocument(
                    source_url=doc.source_url,
                    title=doc.title,
                    content=text,
                    doc_type=doc.doc_type if doc.doc_type != "html" else "text",
                    raw_path=doc.raw_path,
                    last_updated=doc.last_updated,
                    metadata=doc.metadata,
                )
            )

        return cleaned

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
