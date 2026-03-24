"""Plagiarism checking module using TF-IDF cosine similarity.

Provides local corpus-based similarity detection with per-sentence
flagging, plus a pluggable interface for external plagiarism APIs.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class ExternalPlagiarismAPI(Protocol):
    """Interface for pluggable external plagiarism checking services."""
    def check(self, text: str) -> Dict: ...


@dataclass
class SimilarityMatch:
    source_index: int
    source_label: str
    similarity_score: float
    matched_segments: List[str] = field(default_factory=list)


@dataclass
class PlagiarismResult:
    text: str
    overall_score: float = 0.0
    matches: List[SimilarityMatch] = field(default_factory=list)
    flagged_sentences: List[Dict] = field(default_factory=list)
    method: str = "local"


class PlagiarismChecker:
    """Checks for text similarity using TF-IDF cosine similarity."""

    def __init__(self, similarity_threshold: float = 0.7,
                 external_api: Optional[ExternalPlagiarismAPI] = None):
        self.similarity_threshold = similarity_threshold
        self.external_api = external_api
        self.vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 3),
        )
        self._corpus: List[str] = []
        self._corpus_labels: List[str] = []

    def add_to_corpus(self, text: str, label: str = "") -> None:
        self._corpus.append(text)
        self._corpus_labels.append(label or f"Document {len(self._corpus)}")

    def clear_corpus(self) -> None:
        self._corpus.clear()
        self._corpus_labels.clear()

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if len(s.strip().split()) >= 4]

    def check_local(self, text: str) -> PlagiarismResult:
        if not self._corpus:
            return PlagiarismResult(text=text, overall_score=0.0, method="local")

        all_texts = self._corpus + [text]
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        target_vector = tfidf_matrix[-1]
        corpus_vectors = tfidf_matrix[:-1]

        similarities = cosine_similarity(target_vector, corpus_vectors)[0]

        matches = []
        for i, score in enumerate(similarities):
            if score >= self.similarity_threshold:
                matches.append(SimilarityMatch(
                    source_index=i,
                    source_label=self._corpus_labels[i],
                    similarity_score=round(float(score) * 100, 2),
                ))

        flagged = self._find_flagged_sentences(text)
        overall = (
            round(float(np.max(similarities)) * 100, 2)
            if len(similarities) > 0
            else 0.0
        )

        logger.info(
            "Plagiarism check: %.1f%% max similarity across %d sources",
            overall, len(self._corpus),
        )

        return PlagiarismResult(
            text=text,
            overall_score=overall,
            matches=sorted(
                matches, key=lambda m: m.similarity_score, reverse=True,
            ),
            flagged_sentences=flagged,
            method="local",
        )

    def _find_flagged_sentences(self, text: str) -> List[Dict]:
        sentences = self._split_sentences(text)
        if not sentences or not self._corpus:
            return []

        flagged: List[Dict] = []
        for sentence in sentences:
            all_texts = self._corpus + [sentence]
            try:
                matrix = self.vectorizer.fit_transform(all_texts)
                sent_sim = cosine_similarity(matrix[-1], matrix[:-1])[0]
                max_sim = float(np.max(sent_sim))
                if max_sim >= self.similarity_threshold:
                    best_idx = int(np.argmax(sent_sim))
                    flagged.append({
                        "sentence": sentence,
                        "similarity": round(max_sim * 100, 2),
                        "matched_source": self._corpus_labels[best_idx],
                    })
            except ValueError:
                continue

        return flagged

    def check_external(self, text: str) -> PlagiarismResult:
        if self.external_api is None:
            raise RuntimeError("No external API configured")
        api_result = self.external_api.check(text)
        return PlagiarismResult(
            text=text,
            overall_score=api_result.get("score", 0.0),
            method="external",
        )

    def check(self, text: str, use_external: bool = False) -> PlagiarismResult:
        if use_external and self.external_api is not None:
            return self.check_external(text)
        return self.check_local(text)
