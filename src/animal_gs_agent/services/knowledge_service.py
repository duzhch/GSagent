"""Knowledge connector, retrieval, and citation formatting service."""

from __future__ import annotations

from pathlib import Path
import re

from animal_gs_agent.schemas.jobs import JobStatusResponse
from animal_gs_agent.schemas.knowledge import (
    KnowledgeDocument,
    RecommendationCitation,
    RetrievedEvidence,
)

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")
_POSITIVE_MARKERS = ("recommended", "should use", "best practice", "prefer")
_NEGATIVE_MARKERS = ("not recommended", "avoid", "contraindicated", "do not")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_PATTERN.findall(text)}


def _score(query_tokens: set[str], doc_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens.intersection(doc_tokens))
    return overlap / len(query_tokens)


def _build_snippet(content: str, query_tokens: set[str]) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    for line in lines:
        lowered = line.lower()
        if any(token in lowered for token in query_tokens):
            return line[:220]
    if not lines:
        return ""
    return lines[0][:220]


def _read_paths(paths: list[str]) -> list[str]:
    contents: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            contents.append(text)
    return contents


def build_knowledge_documents(
    *,
    history_jobs: list[JobStatusResponse],
    sop_paths: list[str],
    literature_paths: list[str],
) -> list[KnowledgeDocument]:
    docs: list[KnowledgeDocument] = []

    for job in history_jobs:
        if job.workflow_summary is None:
            continue
        recs = []
        if job.dataset_profile.phenotype_diagnostics is not None:
            recs = job.dataset_profile.phenotype_diagnostics.recommendations
        summary = (
            f"Historical job {job.job_id} on trait {job.trait_name}. "
            f"Risk tags: {', '.join(job.dataset_profile.risk_tags) or 'none'}. "
            f"Recommendations: {', '.join(recs) or 'none'}."
        )
        docs.append(
            KnowledgeDocument(
                source_id=f"history:{job.job_id}",
                source_type="historical_task",
                title=f"Job {job.job_id}",
                content=summary,
            )
        )

    for index, raw_path in enumerate(sop_paths, start=1):
        contents = _read_paths([raw_path])
        if not contents:
            continue
        docs.append(
            KnowledgeDocument(
                source_id=f"sop:{index}",
                source_type="sop",
                title=Path(raw_path).name,
                content=contents[0],
            )
        )

    for index, raw_path in enumerate(literature_paths, start=1):
        contents = _read_paths([raw_path])
        if not contents:
            continue
        docs.append(
            KnowledgeDocument(
                source_id=f"literature:{index}",
                source_type="literature",
                title=Path(raw_path).name,
                content=contents[0],
            )
        )

    return docs


def retrieve_knowledge_evidence(
    *,
    query: str,
    documents: list[KnowledgeDocument],
    top_k: int,
) -> list[RetrievedEvidence]:
    if top_k <= 0:
        return []
    query_tokens = _tokenize(query)
    ranked: list[tuple[float, KnowledgeDocument]] = []
    for doc in documents:
        score = _score(query_tokens, _tokenize(doc.content))
        ranked.append((score, doc))
    ranked.sort(key=lambda item: (item[0], item[1].source_id), reverse=True)

    evidence: list[RetrievedEvidence] = []
    for score, doc in ranked[:top_k]:
        snippet = _build_snippet(doc.content, query_tokens)
        if not snippet:
            continue
        evidence.append(
            RetrievedEvidence(
                source_id=doc.source_id,
                source_type=doc.source_type,
                title=doc.title,
                snippet=snippet,
                score=round(score, 4),
            )
        )
    return evidence


def _detect_conflict(evidence: list[RetrievedEvidence]) -> tuple[bool, str | None]:
    has_positive = any(any(marker in item.snippet.lower() for marker in _POSITIVE_MARKERS) for item in evidence)
    has_negative = any(any(marker in item.snippet.lower() for marker in _NEGATIVE_MARKERS) for item in evidence)
    if has_positive and has_negative:
        return True, "evidence_conflict_detected: positive and negative guidance both present"
    return False, None


def build_recommendation_citations(
    *,
    recommendations: list[str],
    documents: list[KnowledgeDocument],
    top_k_per_recommendation: int,
) -> list[RecommendationCitation]:
    citations: list[RecommendationCitation] = []
    for recommendation in recommendations:
        evidence = retrieve_knowledge_evidence(
            query=recommendation,
            documents=documents,
            top_k=top_k_per_recommendation,
        )
        if not evidence:
            raise ValueError(f"no evidence found for recommendation: {recommendation}")
        conflict, note = _detect_conflict(evidence)
        citations.append(
            RecommendationCitation(
                recommendation=recommendation,
                evidence=evidence,
                conflict=conflict,
                conflict_note=note,
            )
        )
    return citations
