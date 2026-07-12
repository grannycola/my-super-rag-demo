"""Shared chunk data model."""

import hashlib
from dataclasses import dataclass, field


@dataclass
class DocumentChunk:
    chunk_id: str
    text: str
    source_url: str
    title: str
    section: str
    heading_path: list[str]
    doc_type: str
    last_updated: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source_url": self.source_url,
            "title": self.title,
            "section": self.section,
            "heading_path": self.heading_path,
            "doc_type": self.doc_type,
            "last_updated": self.last_updated,
            **self.metadata,
        }


def make_chunk_id(source_url: str, index: int) -> str:
    digest = hashlib.sha256(f"{source_url}:{index}".encode()).hexdigest()[:12]
    return f"chunk_{digest}"
