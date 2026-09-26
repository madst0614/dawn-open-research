from pathlib import Path
from types import SimpleNamespace
import hashlib

import pytest
import yaml

from open_research import runner
from open_research.models import Method, Result, Run, Study
from open_research.resolver import resolve
from open_research.store import load_catalog, validate_catalog
from conftest import read_yaml, write_yaml


PINNED = "30165201e68897d75f0586805d321393159550c3"


def prepared(research_tree, tmp_path, monkeypatch, returncode=0):
    catalog = load_catalog(research_tree)
    study = next(obj for obj in catalog.of_type(Study) if obj.entrypoint)
    environment_path = catalog.paths[catalog.get(study.profile_ids[0]).environment_ids[0]]
    environment = read_yaml(environment_path)
    lock = research_tree / "test.lock"
    lock.write_bytes(b"pinned fixture dependencies")
    environment["lockfile"] = "test.lock"
    environment["lock_digest"] = "sha256:" + hashlib.sha256(lock.read_bytes()).hexdigest()
    write_yaml(environment_path, environment)
    catalog = load_catalog(research_tree)

    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "data").write_bytes(b"tiny fixture, not a model checkpoint")
    artifact_id = study.requires.artifacts[0]
    artifact_paths = {artifact_id: checkpoint}
    implementation = tmp_path / "implementation"
    implementation.mkdir()
    monkeypatch.setattr(
        runner,
        "_git_identity",
        lambda path: (PINNED if path == implementation else "b" * 40, False),
    )

    def fake_evaluator(command, **kwargs):
        if returncode == 0:
            output_dir = Path(command[command.index("--output-dir") + 1])
            (output_dir / "run_manifest.json").write_text(
                '{"dawn_git_commit":"'
                + PINNED
                + '","working_tree_clean":true,"tasks":["lambada_openai","hellaswag","piqa","arc_easy","arc_challenge","winogrande"],"limit":32,"smoke_test_only":true,"global_device_count":4,"local_device_count":4,"host_count":1,"software_versions":{"jax":"fixture"},"dataset_fingerprints_revisions":{"task":{"fingerprint":"fixture"}}}',
                encoding="utf-8",
            )
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(runner.subprocess, "run", fake_evaluator)
    return catalog, study, implementation, artifact_paths


def test_manifest_generation_without_automatic_result(research_tree, tmp_path, monkeypatch):
    catalog, study, implementation, artifacts = prepared(research_tree, tmp_path, monkeypatch)
    study.method_ids.reverse()
    plan = resolve(catalog, study.id, study.profile_ids[0], artifacts)
    assert plan["ready"]
    run = runner.execute(
        catalog,
        study.id,
        study.profile_ids[0],
        implementation,
        artifacts,
        "github:test",
        32,
    )
    assert run.status == "completed"
    manifest = research_tree / "runs" / run.id / "manifest.yaml"
    stored = Run.model_validate(yaml.safe_load(manifest.read_text(encoding="utf-8")))
    assert stored.input_artifacts[0].digest.startswith("sha256:")
    assert stored.implementations[0].revision == PINNED
    assert stored.method_id == study.entrypoint_method_id
    assert stored.study_id == study.id
    assert stored.command[3].startswith("artifact:")
    assert stored.config_digest.startswith("sha256:")
    assert stored.software_versions == {"jax": "fixture"}
    assert stored.dataset_provenance
    assert (manifest.parent / "config.json").exists()
    reloaded = load_catalog(research_tree)
    assert not reloaded.of_type(Result)
    assert validate_catalog(reloaded) == []


def test_failed_run_is_preserved_and_identity_cannot_be_reused(research_tree, tmp_path, monkeypatch):
    catalog, study, implementation, artifacts = prepared(
        research_tree, tmp_path, monkeypatch, returncode=7
    )
    run = runner.execute(
        catalog,
        study.id,
        study.profile_ids[0],
        implementation,
        artifacts,
        "github:test",
        32,
    )
    assert run.status == "failed"
    manifest = research_tree / "runs" / run.id / "manifest.yaml"
    original = manifest.read_bytes()
    assert "exited 7" in run.error
    assert (manifest.parent / "stderr.log").exists()
    monkeypatch.setattr(runner, "new_id", lambda *args: run.id)
    with pytest.raises(FileExistsError):
        runner.execute(
            catalog,
            study.id,
            study.profile_ids[0],
            implementation,
            artifacts,
            "github:test",
            32,
        )
    assert manifest.read_bytes() == original
    duplicate = research_tree / "runs" / f"{run.id}.yaml"
    duplicate.write_bytes(original)
    assert any("duplicate ID" in error for error in load_catalog(research_tree).errors)


def test_artifact_digest_changes_with_bytes(tmp_path):
    file = tmp_path / "asset.bin"
    file.write_bytes(b"a")
    first = runner.hash_path(file)
    file.write_bytes(b"b")
    assert runner.hash_path(file) != first


def test_dirty_implementation_is_rejected_before_run_creation(research_tree, tmp_path, monkeypatch):
    catalog, study, implementation, artifacts = prepared(research_tree, tmp_path, monkeypatch)
    monkeypatch.setattr(runner, "_git_identity", lambda path: (PINNED, path == implementation))
    with pytest.raises(ValueError, match="clean research and implementation"):
        runner.execute(
            catalog,
            study.id,
            study.profile_ids[0],
            implementation,
            artifacts,
            "github:test",
            32,
        )
    assert list((research_tree / "runs").glob("DAWN-RUN-*")) == []


def test_unpinned_implementation_commit_is_rejected(research_tree, tmp_path, monkeypatch):
    catalog, study, implementation, artifacts = prepared(research_tree, tmp_path, monkeypatch)
    monkeypatch.setattr(
        runner,
        "_git_identity",
        lambda path: ("c" * 40 if path == implementation else "b" * 40, False),
    )
    with pytest.raises(ValueError, match="differs from pinned"):
        runner.execute(
            catalog,
            study.id,
            study.profile_ids[0],
            implementation,
            artifacts,
            "github:test",
            32,
        )
    assert list((research_tree / "runs").glob("DAWN-RUN-*")) == []


def test_interrupted_run_preserves_terminal_manifest(research_tree, tmp_path, monkeypatch):
    catalog, study, implementation, artifacts = prepared(research_tree, tmp_path, monkeypatch)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(runner.subprocess, "run", interrupt)
    run = runner.execute(
        catalog,
        study.id,
        study.profile_ids[0],
        implementation,
        artifacts,
        "github:test",
        32,
    )
    assert run.status == "cancelled"
    manifest = research_tree / "runs" / run.id / "manifest.yaml"
    assert yaml.safe_load(manifest.read_text(encoding="utf-8"))["status"] == "cancelled"


def test_run_method_must_belong_to_study(research_tree, tmp_path, monkeypatch):
    catalog, study, implementation, artifacts = prepared(research_tree, tmp_path, monkeypatch)
    run = runner.execute(
        catalog,
        study.id,
        study.profile_ids[0],
        implementation,
        artifacts,
        "github:test",
        32,
    )
    manifest = research_tree / "runs" / run.id / "manifest.yaml"
    value = read_yaml(manifest)
    value["method_id"] = next(
        method.id for method in catalog.of_type(Method) if method.id not in study.method_ids
    )
    write_yaml(manifest, value)
    errors = validate_catalog(load_catalog(research_tree))
    assert any("Method is not part of Study" in error for error in errors)
