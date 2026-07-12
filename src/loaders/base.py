"""Base types for document loaders."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoadedDocument:
    source_url: str
    title: str
    content: str
    doc_type: str  # markdown | html | text
    raw_path: Path | None = None
    last_updated: str | None = None
    metadata: dict = field(default_factory=dict)
