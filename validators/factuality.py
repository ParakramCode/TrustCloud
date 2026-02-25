"""
TrustCloud AI — Factual Density Validator
Measures factual grounding via named entities, numbers, dates, and proper nouns.
"""

import re
import spacy
from validators.base import BaseValidator, ValidatorOutput

# Loaded once at module level
_nlp = spacy.load("en_core_web_sm")


class FactualDensityValidator(BaseValidator):

    @property
    def name(self) -> str:
        return "factual_density"

    @property
    def version(self) -> str:
        return "v1.0"

    @property
    def default_weight(self) -> float:
        return 0.10

    def run(self, text: str) -> ValidatorOutput:
        doc = _nlp(text)

        entity_count = len(doc.ents)
        number_count = len(re.findall(r"\d+", text))
        date_entities = [ent for ent in doc.ents if ent.label_ in ("DATE", "TIME")]
        proper_nouns = [t for t in doc if t.pos_ == "PROPN"]

        token_count = max(len(doc), 1)

        factual_score = (
            (entity_count * 0.3) +
            (number_count * 0.2) +
            (len(date_entities) * 0.2) +
            (len(proper_nouns) * 0.3)
        )

        normalized = factual_score / token_count
        score = round(min(normalized * 10, 1.0), 3)

        explanation = (
            f"Found {entity_count} named entities, {number_count} numeric references, "
            f"{len(date_entities)} date/time entities, {len(proper_nouns)} proper nouns "
            f"across {token_count} tokens. Normalized density: {normalized:.3f}."
        )

        return ValidatorOutput(score=score, explanation=explanation)
