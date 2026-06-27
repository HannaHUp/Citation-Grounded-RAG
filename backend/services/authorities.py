import math
import re
from dataclasses import dataclass
from pathlib import Path

from backend.services.authority_ingest import CORPUS_PATH, AuthorityRecord, load_corpus


@dataclass
class RetrievedAuthority:
    authority_id: str
    title: str
    source_type: str
    summary: str
    relevance: int
    quote: str
    url: str
    source_text: str
    raw_score: float
    verified: bool


_PROFILE_TERMS = {
    "contract_antitrust": "acquisition merger competition monopoly antitrust",
    "contract_risk": "contract risk obligation competition merger",
    "complaint_claims": "claim plaintiff defendant fiduciary contract venue jurisdiction nonprofit damages",
}

FINDING_MIN_SCORE = 0.04
SOURCE_TYPE_ORDER = ("case", "statute", "secondary")


def retrieve_authorities(
    document_text: str,
    profile_id: str,
    limit: int = 5,
    finding: str | None = None,
    quote: str | None = None,
) -> list[RetrievedAuthority]:
    records = load_corpus(Path(CORPUS_PATH))
    if not records:
        return []

    is_finding_lookup = bool(finding or quote)
    if is_finding_lookup:
        query_parts = [finding or "", quote or ""]
    else:
        query_parts = [document_text, _PROFILE_TERMS.get(profile_id, "")]
    query = " ".join(part for part in query_parts if part)
    scores = _cosine_scores(query, [_retrieval_text(record) for record in records])
    ranked = sorted(zip(records, scores), key=lambda item: (-item[1], item[0].title))
    if is_finding_lookup:
        ranked = [item for item in ranked if item[1] >= FINDING_MIN_SCORE]
        ranked = _prefer_source_type_coverage(ranked, limit)

    return [_to_retrieved(record, score) for record, score in ranked[:limit]]


def authority_response(authorities: list[RetrievedAuthority]) -> list[dict]:
    return [
        {
            "authority_id": authority.authority_id,
            "title": authority.title,
            "source_type": authority.source_type,
            "summary": authority.summary,
            "relevance": authority.relevance,
            "quote": authority.quote,
            "verified": authority.verified,
            "url": authority.url,
        }
        for authority in authorities
    ]


def _to_retrieved(record: AuthorityRecord, score: float) -> RetrievedAuthority:
    quote = record.quote_seed
    verified = quote in record.source_text
    bounded = max(0.0, min(1.0, score))
    return RetrievedAuthority(
        authority_id=record.authority_id,
        title=record.title,
        source_type=record.source_type,
        summary=record.summary_seed,
        relevance=round(bounded * 100),
        quote=quote,
        url=record.url,
        source_text=record.source_text,
        raw_score=bounded,
        verified=verified,
    )


def _retrieval_text(record: AuthorityRecord) -> str:
    return " ".join([record.title, record.summary_seed, record.quote_seed, record.source_text])


def _prefer_source_type_coverage(
    ranked: list[tuple[AuthorityRecord, float]],
    limit: int,
) -> list[tuple[AuthorityRecord, float]]:
    selected: list[tuple[AuthorityRecord, float]] = []
    selected_ids: set[str] = set()

    for source_type in SOURCE_TYPE_ORDER:
        for record, score in ranked:
            if record.source_type == source_type and record.authority_id not in selected_ids:
                selected.append((record, score))
                selected_ids.add(record.authority_id)
                break

    for record, score in ranked:
        if len(selected) >= limit:
            break
        if record.authority_id in selected_ids:
            continue
        selected.append((record, score))
        selected_ids.add(record.authority_id)

    return sorted(selected, key=lambda item: (-item[1], item[0].title))


def _cosine_scores(query: str, documents: list[str]) -> list[float]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(
            [query, *documents]
        )
        return [float(score) for score in cosine_similarity(matrix[0:1], matrix[1:]).ravel()]
    except ImportError:
        return _fallback_tfidf_cosine(query, documents)


def _fallback_tfidf_cosine(query: str, documents: list[str]) -> list[float]:
    all_docs = [query, *documents]
    tokenized = [_tokens(text) for text in all_docs]
    doc_freq: dict[str, int] = {}
    for tokens in tokenized:
        for token in set(tokens):
            doc_freq[token] = doc_freq.get(token, 0) + 1

    vectors = [_tfidf_vector(tokens, doc_freq, len(all_docs)) for tokens in tokenized]
    query_vector = vectors[0]
    return [_cosine(query_vector, vector) for vector in vectors[1:]]


def _tokens(text: str) -> list[str]:
    stop = {"the", "and", "that", "with", "from", "shall", "this", "which", "into"}
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", text.lower())
        if token not in stop
    ]


def _tfidf_vector(tokens: list[str], doc_freq: dict[str, int], doc_count: int) -> dict[str, float]:
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return {
        token: count * (math.log((1 + doc_count) / (1 + doc_freq[token])) + 1)
        for token, count in counts.items()
    }


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    numerator = sum(weight * right.get(token, 0.0) for token, weight in left.items())
    left_norm = math.sqrt(sum(weight * weight for weight in left.values()))
    right_norm = math.sqrt(sum(weight * weight for weight in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
