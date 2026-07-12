"""LangChain documentation loader via llms.txt and markdown URLs."""

from __future__ import annotations

import re
from pathlib import Path

import requests

from src.config import Config, get_config
from src.loaders.base import LoadedDocument

LLMS_TXT_URL = "https://docs.langchain.com/llms.txt"

DEFAULT_KEYWORDS = [
    "rag",
    "retrieval",
    "retriever",
    "vector",
    "embedding",
    "text-splitter",
    "text_splitter",
    "document-loader",
    "document_loaders",
    "prompt",
    "chat",
    "agent",
    "tool",
    "output-parser",
    "langsmith",
    "evaluation",
]


class LangChainDocsLoader:
    """Fetch LangChain docs from llms.txt sitemap."""

    def __init__(self, config: Config | None = None, keywords: list[str] | None = None) -> None:
        self.config = config or get_config()
        self.keywords = keywords or DEFAULT_KEYWORDS

    def discover_urls(self) -> list[str]:
        response = requests.get(LLMS_TXT_URL, timeout=30)
        response.raise_for_status()
        urls = re.findall(r"https://docs\.langchain\.com/[^\)\s]+\.md", response.text)
        return sorted({url for url in urls if self._is_relevant(url)})

    def load(self, urls: list[str] | None = None) -> list[LoadedDocument]:
        urls = urls or self.discover_urls()
        self.config.raw_data_dir.mkdir(parents=True, exist_ok=True)
        documents: list[LoadedDocument] = []

        for url in urls:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            title = self._extract_title(content, url)
            safe_name = url.rstrip("/").split("/")[-1]
            raw_path = self.config.raw_data_dir / "langchain" / safe_name
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(content, encoding="utf-8")

            documents.append(
                LoadedDocument(
                    source_url=url,
                    title=title,
                    content=content,
                    doc_type="markdown",
                    raw_path=raw_path,
                )
            )

        return documents

    def _is_relevant(self, url: str) -> bool:
        lower_url = url.lower()
        return any(keyword in lower_url for keyword in self.keywords)

    @staticmethod
    def _extract_title(content: str, url: str) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return url.rstrip("/").split("/")[-1].replace(".md", "").replace("-", " ").title()
