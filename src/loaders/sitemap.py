"""Generic sitemap / URL list loader."""

from __future__ import annotations

from pathlib import Path

import requests

from src.config import Config, get_config
from src.loaders.base import LoadedDocument


class SitemapLoader:
    """Load documents from a plain-text URL list or sitemap file."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()

    def load_from_file(self, path: Path) -> list[LoadedDocument]:
        urls = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return self.load(urls)

    def load(self, urls: list[str]) -> list[LoadedDocument]:
        documents: list[LoadedDocument] = []
        self.config.raw_data_dir.mkdir(parents=True, exist_ok=True)

        for url in urls:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            doc_type = "markdown" if url.endswith(".md") else "html"
            safe_name = url.rstrip("/").split("/")[-1] or "index"
            raw_path = self.config.raw_data_dir / safe_name
            raw_path.write_text(content, encoding="utf-8")

            documents.append(
                LoadedDocument(
                    source_url=url,
                    title=safe_name,
                    content=content,
                    doc_type=doc_type,
                    raw_path=raw_path,
                )
            )

        return documents
