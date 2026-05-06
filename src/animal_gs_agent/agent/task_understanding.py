"""Task understanding pipeline with model and fallback parsing."""

import re

from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult


def _rule_based_understanding(user_message: str) -> TaskUnderstandingResult:
    message = user_message.lower()
    request_scope = "supported_gs" if "genomic selection" in message or "gs" in message else "unsupported"

    trait_match = re.search(r"trait\s+([a-zA-Z_][a-zA-Z0-9_]*)", user_message)
    trait_name = trait_match.group(1) if trait_match else None

    fixed_effects: list[str] = []
    for candidate in ("sex", "batch", "herd", "year", "season", "parity"):
        if candidate in message:
            fixed_effects.append(candidate)

    return TaskUnderstandingResult(
        request_scope=request_scope,
        trait_name=trait_name,
        user_goal="rank candidates for genomic selection" if request_scope == "supported_gs" else None,
        candidate_fixed_effects=fixed_effects,
        population_description=None,
        missing_inputs=[],
        confidence=0.4 if request_scope == "supported_gs" else 0.2,
        clarification_needed=False,
    )


def understand_task(user_message: str, llm_client) -> TaskUnderstandingResult:
    system_prompt = "You are a genomic selection request parser. Return strict JSON only."
    try:
        payload = llm_client.request_json(system_prompt=system_prompt, user_prompt=user_message)
        return TaskUnderstandingResult.model_validate(payload)
    except Exception:
        return _rule_based_understanding(user_message)
