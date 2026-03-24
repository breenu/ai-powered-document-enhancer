"""Paraphrasing module using a T5 model.

Generates multiple paraphrase suggestions for given text passages,
intended for rewriting plagiarism-flagged content.
"""

import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class ParaphraseResult:
    original: str
    suggestions: List[str] = field(default_factory=list)
    selected: str = ""


class Paraphraser:
    """Generates paraphrase suggestions using a T5 paraphrase model."""

    def __init__(self, model_name: str = "Vamsi/T5_Paraphrase_Paws"):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        if self._model is None:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            logger.info("Loading paraphrase model: %s", self.model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

    def paraphrase(self, text: str, num_suggestions: int = 3,
                   max_length: int = 256) -> ParaphraseResult:
        self._load_model()

        input_text = f"paraphrase: {text} </s>"
        encoding = self._tokenizer(
            input_text, return_tensors="pt", max_length=max_length,
            padding="max_length", truncation=True,
        )

        outputs = self._model.generate(
            input_ids=encoding["input_ids"],
            attention_mask=encoding["attention_mask"],
            max_length=max_length,
            num_beams=num_suggestions + 2,
            num_return_sequences=num_suggestions,
            temperature=1.5,
            do_sample=False,
            early_stopping=True,
        )

        suggestions: List[str] = []
        seen: set = set()
        for output in outputs:
            decoded = self._tokenizer.decode(output, skip_special_tokens=True)
            normalized = decoded.strip()
            if normalized and normalized.lower() != text.strip().lower():
                if normalized not in seen:
                    suggestions.append(normalized)
                    seen.add(normalized)

        return ParaphraseResult(
            original=text,
            suggestions=suggestions,
            selected=suggestions[0] if suggestions else text,
        )

    def paraphrase_flagged(self, flagged_passages: List[dict],
                           num_suggestions: int = 3) -> List[ParaphraseResult]:
        results: List[ParaphraseResult] = []
        for passage in flagged_passages:
            sentence = passage.get("sentence", "")
            if sentence:
                result = self.paraphrase(
                    sentence, num_suggestions=num_suggestions,
                )
                results.append(result)
                logger.info(
                    "Paraphrased flagged passage: %.50s...", sentence,
                )
        return results
