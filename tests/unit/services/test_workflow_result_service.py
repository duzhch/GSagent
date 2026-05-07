from animal_gs_agent.services.workflow_result_service import parse_workflow_outputs


def test_parse_workflow_outputs_extracts_top_candidates_and_metrics(tmp_path) -> None:
    result_dir = tmp_path / "run001"
    gblup_dir = result_dir / "gblup"
    gblup_dir.mkdir(parents=True)

    (gblup_dir / "gebv_predictions.csv").write_text(
        "\n".join(
            [
                "individual_id,trait,gebv,gebv_rank,gebv_sd",
                "ID_01,daily_gain,100.5,1,",
                "ID_02,daily_gain,98.3,2,",
                "ID_03,daily_gain,95.1,3,",
            ]
        ),
        encoding="utf-8",
    )
    (gblup_dir / "model_summary.txt").write_text(
        "\n".join(
            [
                "=== GBLUP 模型摘要 ===",
                "h²: 0.4615 ",
                "预测准确度 r: 0.9349 ",
            ]
        ),
        encoding="utf-8",
    )

    summary = parse_workflow_outputs(result_dir=result_dir, trait_name="daily_gain", top_n=2)

    assert summary.trait_name == "daily_gain"
    assert summary.total_candidates == 3
    assert len(summary.top_candidates) == 2
    assert summary.top_candidates[0].individual_id == "ID_01"
    assert summary.top_candidates[0].rank == 1
    assert summary.model_metrics["h²"] == "0.4615"
    assert summary.model_metrics["预测准确度 r"] == "0.9349"


def test_parse_workflow_outputs_raises_when_gebv_file_missing(tmp_path) -> None:
    result_dir = tmp_path / "run001"
    gblup_dir = result_dir / "gblup"
    gblup_dir.mkdir(parents=True)

    try:
        parse_workflow_outputs(result_dir=result_dir, trait_name="daily_gain")
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected FileNotFoundError")


def test_parse_workflow_outputs_merges_rds_metrics_when_rscript_available(tmp_path, monkeypatch) -> None:
    result_dir = tmp_path / "run001"
    gblup_dir = result_dir / "gblup"
    gblup_dir.mkdir(parents=True)

    (gblup_dir / "gebv_predictions.csv").write_text(
        "\n".join(
            [
                "individual_id,trait,gebv,gebv_rank,gebv_sd",
                "ID_01,daily_gain,100.5,1,",
            ]
        ),
        encoding="utf-8",
    )
    (gblup_dir / "accuracy_metrics.rds").write_text("placeholder", encoding="utf-8")

    monkeypatch.setattr(
        "animal_gs_agent.services.workflow_result_service.shutil.which",
        lambda _: "/usr/bin/Rscript",
    )

    class _Completed:
        returncode = 0
        stdout = '{"r":0.88,"rmse":1.5}'

    monkeypatch.setattr(
        "animal_gs_agent.services.workflow_result_service.subprocess.run",
        lambda *args, **kwargs: _Completed(),
    )

    summary = parse_workflow_outputs(result_dir=result_dir, trait_name="daily_gain")

    assert summary.model_metrics["accuracy::r"] == "0.88"
    assert summary.model_metrics["accuracy::rmse"] == "1.5"
