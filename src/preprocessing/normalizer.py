"""Header extraction and document normalization."""

from __future__ import annotations

import re

from src.loaders.base import LoadedDocument


class DocumentNormalizer:
    """Extract headers and enrich document metadata."""

    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def normalize(self, documents: list[LoadedDocument]) -> list[LoadedDocument]:
        normalized: list[LoadedDocument] = []

        for doc in documents:
            headers = self.extract_headers(doc.content)
            metadata = {**doc.metadata, "headers": headers, "header_count": len(headers)}
            normalized.append(
                LoadedDocument(
                    source_url=doc.source_url,
                    title=doc.title,
                    content=doc.content,
                    doc_type=doc.doc_type,
                    raw_path=doc.raw_path,
                    last_updated=doc.last_updated,
                    metadata=metadata,
                )
            )

        return normalized

    def extract_headers(self, content: str) -> list[dict]:
        headers: list[dict] = []
        for match in self.HEADER_PATTERN.finditer(content):
            level = len(match.group(1))
            headers.append({"level": level, "text": match.group(2).strip()})
        return headers
