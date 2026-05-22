from animal_gs_agent.schemas.dataset_profile import DatasetPathChecks, DatasetProfile
from animal_gs_agent.schemas.jobs import (
    DecisionTraceNode,
    JobEvent,
    JobStatusResponse,
    RankedCandidate,
    WorkflowSummary,
)
from animal_gs_agent.schemas.task_understanding import TaskUnderstandingResult
from animal_gs_agent.services.report_service import build_job_report
from animal_gs_agent.services.html_report_service import export_gs_html_report


def _job(result_dir: str) -> JobStatusResponse:
    return JobStatusResponse(
        job_id="job-html",
        status="completed",
        trait_name="daily_gain",
        task_understanding=TaskUnderstandingResult(
            request_scope="supported_gs",
            trait_name="daily_gain",
            user_goal="rank candidates for genomic selection",
            candidate_fixed_effects=["sex", "batch"],
            population_description="commercial pig population",
            missing_inputs=[],
            confidence=0.91,
            clarification_needed=False,
        ),
        dataset_profile=DatasetProfile(
            phenotype_path="/tmp/pheno.csv",
            genotype_path="/tmp/geno.vcf",
            path_checks=DatasetPathChecks(phenotype_exists=True, genotype_exists=True),
            phenotype_format="csv",
            genotype_format="vcf",
            phenotype_headers=["animal_id", "daily_gain"],
            trait_column_present=True,
            validation_flags=[],
        ),
        workflow_backend="native_nextflow",
        workflow_result_dir=result_dir,
        events=[
            JobEvent(phase="queued", timestamp="2026-05-22T10:00:00Z", message="job accepted"),
            JobEvent(
                phase="completed",
                timestamp="2026-05-22T10:08:00Z",
                message="workflow completed",
            ),
        ],
        decision_trace=[
            DecisionTraceNode(
                decision_id="intake_accept_job",
                feature_id="F-P0-01-02",
                story_id="S-P0-01-03",
                agent_id="supervisor",
                action="accept_job",
                rationale="request passed intake parsing and was admitted to job queue",
                status="success",
                duration_ms=5,
                confidence=0.95,
                evidence=["trait=daily_gain"],
                input_summary="Run genomic selection for daily_gain and return candidate individuals",
                output_summary="job status=queued",
                timestamp="2026-05-22T10:00:00Z",
            ),
            DecisionTraceNode(
                decision_id="workflow_completed_success",
                feature_id="F-P0-01-02",
                story_id="S-P0-01-03",
                agent_id="supervisor",
                action="finalize_completed",
                rationale="workflow and parser both completed successfully",
                status="success",
                duration_ms=420,
                confidence=0.97,
                evidence=["backend=native_nextflow"],
                output_summary="job status=completed",
                timestamp="2026-05-22T10:08:00Z",
            ),
        ],
        workflow_summary=WorkflowSummary(
            trait_name="daily_gain",
            total_candidates=100,
            top_candidates=[
                RankedCandidate(individual_id="A1001", gebv=1.2345, rank=1),
                RankedCandidate(individual_id="A1099", gebv=1.1023, rank=2),
                RankedCandidate(individual_id="A0818", gebv=0.9844, rank=3),
            ],
            model_metrics={"metric::pearson": "0.71", "metric::rmse": "0.18"},
            source_files=["gblup/gebv_predictions.csv", "gblup/model_summary.txt"],
        ),
    )


def test_export_gs_html_report_writes_standalone_candidate_report(tmp_path) -> None:
    result_dir = tmp_path / "result"

    artifact = export_gs_html_report(
        job=_job(str(result_dir)),
        report_text="Agent and workflow summary.",
    )

    assert artifact.format == "html"
    assert artifact.artifact_path.endswith("reports/gs_report.html")

    html = (result_dir / "reports" / "gs_report.html").read_text(encoding="utf-8")
    assert "<!doctype html>" in html
    assert "GS Candidate Decision Report" in html
    assert "Candidate GEBV Ranking" in html
    assert "<svg" in html
    assert "A1001" in html
    assert "A1099" in html
    assert "Priority selection candidate" in html
    assert "User Input" in html
    assert "AI Task Plan" in html
    assert "Execution Log" in html
    assert "Execution Steps" in html
    assert "GS Results" in html
    assert "AI Reflection" in html
    assert "Run genomic selection for daily_gain and return candidate individuals" in html
    assert "workflow completed" in html
    assert "workflow_completed_success" in html
    assert "report-layout" in html
    assert "01 用户输入 / User Input" in html
    assert "02 AI 任务规划 / AI Task Plan" in html
    assert "03 执行日志 / Execution Log" in html
    assert "04 执行步骤 / Execution Steps" in html
    assert "05 GS 结果 / GS Results" in html
    assert "06 AI 反思 / AI Reflection" in html
    assert "Candidate Recommendation" in html
    assert "Model & Data Snapshot" in html


def test_build_job_report_exposes_html_report_artifact(tmp_path) -> None:
    result_dir = tmp_path / "result"

    report = build_job_report(_job(str(result_dir)))

    assert report.html_report_artifact is not None
    assert report.html_report_artifact.format == "html"
    assert report.html_report_artifact.artifact_path.endswith("reports/gs_report.html")
    assert (result_dir / "reports" / "gs_report.html").exists()


def test_build_job_report_uses_ai_report_text_when_llm_is_configured(
    monkeypatch, tmp_path
) -> None:
    result_dir = tmp_path / "result"
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_API_KEY", "secret-key")
    monkeypatch.setenv("ANIMAL_GS_AGENT_LLM_MODEL", "deepseek-chat")

    def fake_request_json(self, system_prompt: str, user_prompt: str) -> dict:
        assert "report_text" in user_prompt
        return {"report_text": "AI 生成：A1001 是优先候选个体。"}

    monkeypatch.setattr(
        "animal_gs_agent.llm.client.OpenAICompatibleLLMClient.request_json",
        fake_request_json,
    )

    report = build_job_report(_job(str(result_dir)))

    assert report.report_text == "AI 生成：A1001 是优先候选个体。"
    html = (result_dir / "reports" / "gs_report.html").read_text(encoding="utf-8")
    assert "AI 生成：A1001 是优先候选个体。" in html


def test_build_job_report_shows_simple_not_connected_message_when_llm_is_missing(
    monkeypatch, tmp_path
) -> None:
    result_dir = tmp_path / "result"
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_API_KEY", raising=False)
    monkeypatch.delenv("ANIMAL_GS_AGENT_LLM_MODEL", raising=False)

    report = build_job_report(_job(str(result_dir)))

    assert report.report_text == "AI 未接入：当前报告未调用大模型生成摘要。"
    html = (result_dir / "reports" / "gs_report.html").read_text(encoding="utf-8")
    assert "AI 未接入：当前报告未调用大模型生成摘要。" in html
