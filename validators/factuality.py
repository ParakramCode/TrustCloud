import spacy
import re

nlp = spacy.load("en_core_web_sm")

def check_factual_density(text: str) -> float:
    """
    Returns factual density score [0,1]
    """

    doc = nlp(text)

    # Named entities
    entity_count = len(doc.ents)

    # Numbers
    number_count = len(re.findall(r"\d+", text))

    # Dates
    date_entities = len([ent for ent in doc.ents if ent.label_ in ["DATE", "TIME"]])

    # Proper nouns
    proper_nouns = len([t for t in doc if t.pos_ == "PROPN"])

    # Total tokens
    token_count = max(len(doc), 1)

    factual_score = (
        (entity_count * 0.3) +
        (number_count * 0.2) +
        (date_entities * 0.2) +
        (proper_nouns * 0.3)
    )

    normalized = factual_score / token_count

    return round(min(normalized * 10, 1.0), 3)
