"""Job request and response schemas."""

from typing import Literal

from pydantic import BaseModel, Field

from animal_gs_agent.schemas.dataset_profile import DatasetProfile
from animal_gs_agent.schemas.debug import DebugDiagnosis
from animal_gs_agent.schemas.audit_claim import AuditCheckResult, ClaimEvidenceItem
from animal_gs_agent.schemas.badcase import BadcaseAdvice
from animal_gs_agent.schemas.knowledge import RecommendationCitation
from animal_gs_agent.schemas.model_pool import ModelPoolPlan
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.schemas.trial_strategy import TrialPlanResult
from animal_gs_agent.schemas.validation_protocol import ValidationProtocolPlan


class JobSubmissionRequest(BaseModel):
    user_message: str
    trait_name: str
    phenotype_path: str
    genotype_path: str


class JobEscalationResolutionRequest(BaseModel):
    approver: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class JobQCOverrideRequest(BaseModel):
    approver: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class RankedCandidate(BaseModel):
    individual_id: str
    gebv: float
    rank: int


class WorkflowSummary(BaseModel):
    trait_name: str | None = None
    total_candidates: int
    top_candidates: list[RankedCandidate] = Field(default_factory=list)
    model_metrics: dict[str, str] = Field(default_factory=dict)
    source_files: list[str] = Field(default_factory=list)


class JobEvent(BaseModel):
    phase: Literal["queued", "running", "completed", "failed"]
    timestamp: str
    message: str
    error_code: str | None = None


class DecisionTraceNode(BaseModel):
    decision_id: str
    feature_id: str
    story_id: str | None = None
    agent_id: str
    action: str
    rationale: str
    status: Literal["success", "failed", "running"]
    duration_ms: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    input_summary: str | None = None
    output_summary: str | None = None
    counterfactual: str | None = None
    timestamp: str


class JobArtifact(BaseModel):
    relative_path: str
    size_bytes: int


class JobArtifactsResponse(BaseModel):
    job_id: str
    status: str
    artifact_count: int
    artifacts: list[JobArtifact] = Field(default_factory=list)


class FallbackPlan(BaseModel):
    strategy: Literal["manual_review_with_fixed_pipeline_fallback"]
    reason: str
    created_by: str
    created_at: str


class RoleSpecificReport(BaseModel):
    role: Literal["technical", "decision", "management"]
    conclusion: str
    summary: str
    audit_summary: str
    risk_summary: str


class JobSubmissionResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    trait_name: str
    task_understanding: TaskUnderstandingResult
    dataset_profile: DatasetProfile
    model_pool_plan: ModelPoolPlan | None = None
    trial_strategy_plan: TrialPlanResult | None = None
    validation_protocol_plan: ValidationProtocolPlan | None = None
    badcase_advice: BadcaseAdvice | None = None
    execution_error: str | None = None
    execution_error_detail: str | None = None
    debug_diagnosis: DebugDiagnosis | None = None
    workflow_backend: str | None = None
    workflow_result_dir: str | None = None
    workflow_submission_id: str | None = None
    workflow_queue_state: str | None = None
    escalation_required: bool = False
    escalation_reason: str | None = None
    escalation_requested_at: str | None = None
    escalation_resolution: Literal["retry", "abort"] | None = None
    escalation_resolved_by: str | None = None
    escalation_resolved_at: str | None = None
    fallback_plan: FallbackPlan | None = None
    qc_override_applied: bool = False
    qc_override_by: str | None = None
    qc_override_reason: str | None = None
    qc_override_at: str | None = None
    workflow_summary: WorkflowSummary | None = None
    events: list[JobEvent] = Field(default_factory=list)
    decision_trace: list[DecisionTraceNode] = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    trait_name: str
    task_understanding: TaskUnderstandingResult
    dataset_profile: DatasetProfile
    model_pool_plan: ModelPoolPlan | None = None
    trial_strategy_plan: TrialPlanResult | None = None
    validation_protocol_plan: ValidationProtocolPlan | None = None
    badcase_advice: BadcaseAdvice | None = None
    execution_error: str | None = None
    execution_error_detail: str | None = None
    debug_diagnosis: DebugDiagnosis | None = None
    workflow_backend: str | None = None
    workflow_result_dir: str | None = None
    workflow_submission_id: str | None = None
    workflow_queue_state: str | None = None
    escalation_required: bool = False
    escalation_reason: str | None = None
    escalation_requested_at: str | None = None
    escalation_resolution: Literal["retry", "abort"] | None = None
    escalation_resolved_by: str | None = None
    escalation_resolved_at: str | None = None
    fallback_plan: FallbackPlan | None = None
    qc_override_applied: bool = False
    qc_override_by: str | None = None
    qc_override_reason: str | None = None
    qc_override_at: str | None = None
    workflow_summary: WorkflowSummary | None = None
    events: list[JobEvent] = Field(default_factory=list)
    decision_trace: list[DecisionTraceNode] = Field(default_factory=list)


class JobReportResponse(BaseModel):
    job_id: str
    trait_name: str
    status: str
    report_text: str
    top_candidates: list[RankedCandidate] = Field(default_factory=list)
    claim_evidence_map: list[ClaimEvidenceItem] = Field(default_factory=list)
    audit_checks: list[AuditCheckResult] = Field(default_factory=list)
    knowledge_citations: list[RecommendationCitation] = Field(default_factory=list)
    role_reports: list[RoleSpecificReport] = Field(default_factory=list)
    role_report_alignment_ok: bool = True
    role_report_alignment_note: str | None = None


class JobDecisionTraceResponse(BaseModel):
    job_id: str
    status: str
    decision_trace: list[DecisionTraceNode] = Field(default_factory=list)
