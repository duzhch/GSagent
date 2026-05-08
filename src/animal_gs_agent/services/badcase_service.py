"""Badcase memory query and preventive-action generation service."""

from __future__ import annotations

import re

from animal_gs_agent.schemas.badcase import BadcaseAdvice, BadcaseRecord, SimilarBadcaseMatch
from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.jobs import JobStatusResponse
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult

_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_]+")
_RISK_ACTION_MAP = {
    "population_structure_outliers": "review outlier samples and use stratified split",
    "population_relatedness_high": "review related pairs and avoid leakage across splits",
    "qc_missingness_high": "tighten missingness filters before model trials",
}


def _tokens_from_text(text: str) -> set[str]:
    return {item.lower() for item in _TOKEN_PATTERN.findall(text)}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    union = left.union(right)
    if not union:
        return 0.0
    return len(left.intersection(right)) / len(union)


def _recommendations_from_profile(dataset_profile: DatasetProfile) -> list[str]:
    diagnostics = dataset_profile.phenotype_diagnostics
    if diagnostics is None:
        return []
    return diagnostics.recommendations


def build_badcase_record(job: JobStatusResponse) -> BadcaseRecord:
    recommendations = _recommendations_from_profile(job.dataset_profile)
    summary = (
        f"job={job.job_id} trait={job.trait_name} "
        f"risk_tags={','.join(job.dataset_profile.risk_tags) or 'none'} "
        f"recommendations={','.join(recommendations) or 'none'}"
    )
    return BadcaseRecord(
        job_id=job.job_id,
        trait_name=job.trait_name,
        population_description=job.task_understanding.population_description,
        risk_tags=job.dataset_profile.risk_tags,
        recommendations=recommendations,
        status=job.status,
        summary=summary,
    )


def _task_signature(task_understanding: TaskUnderstandingResult, dataset_profile: DatasetProfile) -> set[str]:
    chunks = [
        task_understanding.trait_name,
        task_understanding.population_description,
        " ".join(task_understanding.candidate_fixed_effects),
        " ".join(dataset_profile.risk_tags),
        " ".join(_recommendations_from_profile(dataset_profile)),
    ]
    return _tokens_from_text(" ".join(chunks))


def _record_signature(record: BadcaseRecord) -> set[str]:
    chunks = [
        record.trait_name,
        record.population_description,
        " ".join(record.risk_tags),
        " ".join(record.recommendations),
    ]
    return _tokens_from_text(" ".join(chunks))


def _composite_similarity(
    task_understanding: TaskUnderstandingResult,
    dataset_profile: DatasetProfile,
    record: BadcaseRecord,
) -> float:
    score = 0.0
    if task_understanding.trait_name.strip().lower() == record.trait_name.strip().lower():
        score += 0.5
    if task_understanding.population_description.strip().lower() == record.population_description.strip().lower():
        score += 0.2

    context_similarity = _jaccard(_task_signature(task_understanding, dataset_profile), _record_signature(record))
    score += 0.3 * context_similarity
    return min(1.0, score)


def _build_preventive_actions(similar_cases: list[SimilarBadcaseMatch]) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()

    for case in similar_cases:
        for risk_tag in case.record.risk_tags:
            mapped = _RISK_ACTION_MAP.get(risk_tag)
            if mapped and mapped not in seen:
                seen.add(mapped)
                actions.append(mapped)
        for recommendation in case.record.recommendations:
            if recommendation not in seen:
                seen.add(recommendation)
                actions.append(recommendation)
    return actions


def build_badcase_advice(
    *,
    task_understanding: TaskUnderstandingResult,
    dataset_profile: DatasetProfile,
    historical_jobs: list[JobStatusResponse],
    similarity_threshold: float = 0.50,
    top_k: int = 3,
) -> BadcaseAdvice:
    ranked: list[SimilarBadcaseMatch] = []
    for job in historical_jobs:
        if job.status not in {"completed", "failed"}:
            continue
        record = build_badcase_record(job)
        similarity = _composite_similarity(task_understanding, dataset_profile, record)
        if similarity < similarity_threshold:
            continue
        ranked.append(SimilarBadcaseMatch(record=record, similarity=round(similarity, 4)))

    ranked.sort(key=lambda item: item.similarity, reverse=True)
    top_matches = ranked[: max(1, top_k)]
    high_similarity_hit = len(top_matches) > 0
    preventive_actions = _build_preventive_actions(top_matches) if high_similarity_hit else []

    return BadcaseAdvice(
        queried=True,
        high_similarity_hit=high_similarity_hit,
        similar_cases=top_matches,
        preventive_actions=preventive_actions,
    )
