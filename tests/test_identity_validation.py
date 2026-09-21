from pathlib import Path

import pytest
from pydantic import ValidationError

from open_research.ids import new_id, validate_id
from open_research.models import Claim, Evidence, Run
from open_research.store import load_catalog, validate_catalog
from conftest import read_yaml, write_yaml


def only(root: Path, directory: str):
    return next((root / directory).glob("*.yaml"))


def test_offline_ids_are_unique_and_namespace_specific():
    ids = {new_id("OTHER", "Q") for _ in range(300)}
    assert len(ids) == 300
    assert all(validate_id(value, "OTHER", "Q") == "Q" for value in ids)
    with pytest.raises(ValueError):
        validate_id(next(iter(ids)), "DAWN", "Q")
    with pytest.raises(ValueError):
        new_id("DAWN", "UNKNOWN")


def test_duplicate_id_detected(research_tree):
    path = only(research_tree, "graph/claims")
    (path.parent / "duplicate.yaml").write_bytes(path.read_bytes())
    assert any("duplicate ID" in error for error in load_catalog(research_tree).errors)


def test_invalid_claim_status_is_rejected(research_tree):
    path = only(research_tree, "graph/claims")
    value = read_yaml(path)
    value["status"] = "proven"
    write_yaml(path, value)
    assert any("status" in error for error in load_catalog(research_tree).errors)


def test_supported_claim_requires_reviewed_evidence(research_tree):
    path = only(research_tree, "graph/claims")
    value = read_yaml(path)
    value["status"] = "supported"
    write_yaml(path, value)
    assert any("requires accepted supporting Evidence" in error for error in validate_catalog(load_catalog(research_tree)))


def test_missing_evidence_provenance_rejected():
    with pytest.raises(ValidationError, match="requires a Run or Source"):
        Evidence(id=new_id("DAWN", "E"), created_by="github:test",
                 created_at="2026-09-21T00:00:00Z", title="Observation",
                 observation="Measured value", scope="one setting", limitations="small sample", authors=["github:test"])


def test_run_requires_implementation_and_environment():
    base = {"id": new_id("DAWN", "RUN"), "created_by": "github:test",
            "created_at": "2026-09-21T00:00:00Z", "exploration_id": new_id("DAWN", "X"),
            "probe_id": new_id("DAWN", "P"), "research_revision": "a" * 40,
            "research_dirty": False, "implementations": [], "profile_id": new_id("DAWN", "PROFILE"),
            "hardware_class": "CPU", "input_artifacts": [],
            "config_digest": "sha256:" + "a" * 64, "config_path": "config.json",
            "command": ["python"], "executor": "github:test",
            "started_at": "2026-09-21T00:00:00Z", "status": "created"}
    with pytest.raises(ValidationError) as exc:
        Run.model_validate(base)
    message = str(exc.value)
    assert "implementations" in message
    assert "environment_id" in message
    assert "environment_lock_digest" in message


def test_dangling_and_invalid_relation_endpoints(research_tree):
    relation = only(research_tree, "graph/relations")
    value = read_yaml(relation)
    value["target_id"] = new_id("DAWN", "Q")
    write_yaml(relation, value)
    assert any("missing object" in error for error in validate_catalog(load_catalog(research_tree)))
    value["source_id"] = next((research_tree / "graph/sources").glob("*.yaml")).stem
    value["target_id"] = next((research_tree / "graph/claims").glob("*.yaml")).stem
    value["relation_type"] = "tests"
    write_yaml(relation, value)
    assert any("invalid endpoints" in error for error in validate_catalog(load_catalog(research_tree)))


def test_relation_class_and_type_are_strict(research_tree):
    path = only(research_tree, "graph/relations")
    value = read_yaml(path)
    value["relation_class"] = "causal_magic"
    write_yaml(path, value)
    assert load_catalog(research_tree).errors
    value["relation_class"] = "provenance"
    value["relation_type"] = "supports"
    write_yaml(path, value)
    assert any("invalid provenance relation type" in error for error in validate_catalog(load_catalog(research_tree)))


def test_invalid_artifact_reference_and_readiness_claim(research_tree):
    exploration = next(path for path in (research_tree / "explorations").glob("*.yaml")
                       if read_yaml(path).get("entrypoint"))
    value = read_yaml(exploration)
    value["requires"]["artifacts"] = [new_id("DAWN", "ART")]
    value["declared_readiness"] = "local"
    write_yaml(exploration, value)
    errors = validate_catalog(load_catalog(research_tree))
    assert any("missing Artifact" in error for error in errors)


def test_readiness_claim_rejected_with_missing_dependency(research_tree):
    exploration = next(path for path in (research_tree / "explorations").glob("*.yaml")
                       if read_yaml(path).get("entrypoint"))
    value = read_yaml(exploration)
    value["declared_readiness"] = "local"
    write_yaml(exploration, value)
    assert any("declared local with missing dependencies" in error
               for error in validate_catalog(load_catalog(research_tree)))
