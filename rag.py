from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    text: str
    filename: str
    page: int


class PDFStore:
    def __init__(self, source_dir: Path) -> None:
        self.source_dir = source_dir
        self.chunks: list[Chunk] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix: Any = None

    def ingest(self) -> dict[str, int]:
        chunks: list[Chunk] = []
        for pdf_path in sorted(path for path in self.source_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"):
            try:
                reader = PdfReader(str(pdf_path))
            except Exception:
                continue
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                for part in self._chunk(text):
                    chunks.append(Chunk(part, pdf_path.name, page_number))
        self.chunks = chunks
        if chunks:
            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            self.matrix = self.vectorizer.fit_transform([chunk.text for chunk in chunks])
        else:
            self.vectorizer = None
            self.matrix = None
        return {"documents": len({chunk.filename for chunk in chunks}), "chunks": len(chunks)}

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not self.chunks or self.vectorizer is None:
            return []
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        results = []
        for index in scores.argsort()[::-1]:
            score = float(scores[index])
            if score <= 0:
                continue
            chunk = self.chunks[index]
            results.append({"text": chunk.text, "filename": chunk.filename, "page": chunk.page, "score": round(score, 4)})
            if len(results) == limit:
                break
        return results

    @staticmethod
    def _chunk(text: str, words_per_chunk: int = 180, overlap: int = 35) -> list[str]:
        words = re.findall(r"\S+", text)
        if not words:
            return []
        chunks = []
        step = words_per_chunk - overlap
        for start in range(0, len(words), step):
            part = " ".join(words[start : start + words_per_chunk]).strip()
            if len(part) >= 80:
                chunks.append(part)
            if start + words_per_chunk >= len(words):
                break
        return chunks


def answer_with_context(results: list[dict[str, Any]]) -> str:
    if not results:
        return "I couldn't find relevant passages in the indexed PDFs. Try a more specific question or add another document."
    return " ".join(re.split(r"(?<=[.!?])\s+", result["text"])[0] for result in results[:3])
