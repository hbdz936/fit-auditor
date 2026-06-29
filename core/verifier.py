import re
from functools import lru_cache

from sentence_transformers import SentenceTransformer, util

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#\-]{2,}")
_STOPWORDS = {
    "with", "and", "the", "for", "are", "able", "years", "experience",
    "strong", "good", "knowledge", "skills", "ability", "working",
}

SIMILARITY_THRESHOLD = 0.45  # tuned against the golden set in tests/test_verifier.py


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    # Loaded once per process; CPU inference, no network call, no per-request cost.
    return SentenceTransformer("all-MiniLM-L6-v2")


def _keywords(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text)} - _STOPWORDS


def _semantic_similarity(requirement: str, cited_text: str) -> float:
    if not cited_text.strip():
        return 0.0
    embeddings = _model().encode([requirement, cited_text], convert_to_tensor=True)
    return float(util.cos_sim(embeddings[0], embeddings[1]))


def verify_verdict(verdict: dict, line_map: dict[str, str]) -> dict:
    """Re-checks every citation the model made. The model is never trusted
    at its word. Two independent signals are checked:
      1. keyword overlap (cheap, catches exact-term matches and obvious junk)
      2. semantic similarity via local embeddings (catches legitimate
         paraphrases that share no literal words, e.g. "led a team" vs
         "mentoring junior engineers")
    A citation is verified if EITHER signal clears its bar. If neither does,
    the verdict is downgraded to UNVERIFIED regardless of the model's stated
    confidence.
    """
    status = verdict.get("status")
    evidence_ids = verdict.get("evidence_line_ids", [])

    if status == "GAP":
        verdict["verification_note"] = None
        return verdict

    if not evidence_ids:
        verdict["status"] = "UNVERIFIED"
        verdict["verification_note"] = "Model claimed a match but cited no evidence line."
        return verdict

    cited_text = " ".join(line_map.get(lid, "") for lid in evidence_ids)
    requirement = verdict.get("requirement", "")

    has_keyword_overlap = bool(_keywords(requirement) & _keywords(cited_text))
    similarity = _semantic_similarity(requirement, cited_text)
    is_semantically_close = similarity >= SIMILARITY_THRESHOLD

    verdict["similarity_score"] = round(similarity, 3)

    if not has_keyword_overlap and not is_semantically_close:
        verdict["status"] = "UNVERIFIED"
        verdict["verification_note"] = (
            f"Cited line(s) share no keywords and low semantic similarity "
            f"({similarity:.2f}) with the requirement — likely a hallucinated "
            f"or loosely-related citation."
        )
    else:
        verdict["verification_note"] = None

    return verdict