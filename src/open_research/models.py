"""Strict research-grammar v1 manifests.

Object-local shape constraints live here. Cross-object and repository constraints
live in :mod:`open_research.store`.
"""

from datetime import datetime
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Program(StrictModel):
    id: str
    namespace: str = Field(pattern=r"^[A-Z][A-Z0-9]{1,15}$")
    schema_version: Literal[1]
    title: NonEmptyStr
    mission: NonEmptyStr
    repository: NonEmptyStr
    views: list[str]
    id_scheme: NonEmptyStr
    review_policy: NonEmptyStr
    default_baseline_id: str | None = None
    citation_convention: NonEmptyStr


class Record(StrictModel):
    id: str
    schema_version: Literal[1] = 1
    created_by: str = Field(pattern=r"^[a-z]+:[A-Za-z0-9_.-]+$")
    created_at: datetime
    contributors: list[str] = Field(default_factory=list)

    @field_validator("created_at")
    @classmethod
    def aware_time(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value


class Question(Record):
    title: NonEmptyStr
    question: NonEmptyStr
    rationale: NonEmptyStr
    scope: NonEmptyStr
    status: Literal[
        "open", "active", "partially_resolved", "resolved", "blocked", "superseded"
    ]


class Claim(Record):
    title: NonEmptyStr
    statement: NonEmptyStr
    claim_type: Literal["proposition", "interpretation", "definition"]
    scope: NonEmptyStr
    status: Literal[
        "proposed", "tentative", "supported", "robust", "disputed", "limited", "contradicted", "superseded"
    ]


class Method(Record):
    title: NonEmptyStr
    description: NonEmptyStr
    protocol: NonEmptyStr
    status: Literal["proposed", "specified", "validated", "deprecated"]


class Result(Record):
    title: NonEmptyStr
    statement: NonEmptyStr
    scope: NonEmptyStr
    limitations: NonEmptyStr
    grounding_ids: list[str] = Field(min_length=1)
    authors: list[str] = Field(min_length=1)
    reviewers: list[str] = Field(default_factory=list)


class Source(Record):
    title: NonEmptyStr
    source_type: Literal["paper", "book", "dataset", "repository", "documentation", "benchmark", "other"]
    uri: NonEmptyStr
    source_statement: NonEmptyStr


class Relation(Record):
    source_id: str
    target_id: str
    relation_class: Literal["semantic", "provenance"]
    relation_type: NonEmptyStr
    status: Literal["proposed", "accepted", "disputed", "rejected", "superseded"]
    asserted_by: NonEmptyStr
    asserted_at: datetime
    rationale: NonEmptyStr
    reviewers: list[str] = Field(default_factory=list)
    review_notes: str | None = None

    @model_validator(mode="after")
    def accepted_requires_review(self):
        if self.status == "accepted" and not self.reviewers:
            raise ValueError("accepted Relation requires a reviewer")
        return self


class Requirements(StrictModel):
    capabilities: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)


class ExecutionPlan(StrictModel):
    """Method-specific execution configuration embedded in a Study."""

    method_id: str
    entrypoint: NonEmptyStr | None = None
    requires: Requirements = Field(default_factory=Requirements)
    profile_ids: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    declared_readiness: Literal["draft", "local", "public", "blocked"] | None = None


class StudyExecution(StrictModel):
    plans: list[ExecutionPlan] = Field(default_factory=list)


class Study(Record):
    title: NonEmptyStr
    lifecycle: Literal["draft", "planned", "active", "completed", "blocked", "superseded"]
    goal: NonEmptyStr
    motivation: NonEmptyStr
    question_ids: list[str] = Field(default_factory=list)
    claim_ids: list[str] = Field(default_factory=list)
    method_ids: list[str] = Field(default_factory=list)
    result_ids: list[str] = Field(default_factory=list)
    artifact_ids: list[str] = Field(default_factory=list)
    completion_criteria: NonEmptyStr
    known_limitations: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    execution: StudyExecution = Field(default_factory=StudyExecution)

    @model_validator(mode="after")
    def execution_methods_are_explicit(self):
        plan_methods = [plan.method_id for plan in self.execution.plans]
        if len(plan_methods) != len(set(plan_methods)):
            raise ValueError("Study execution plans must have unique method_id values")
        missing = sorted(set(plan_methods) - set(self.method_ids))
        if missing:
            raise ValueError(f"execution plan Methods must be listed in method_ids: {missing}")
        return self


class RepositoryRef(Record):
    name: str
    url: str
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    status: Literal["public", "private", "unknown"]
    license: str | None = None


class InfrastructureProvider(Record):
    name: str
    interface_version: str
    repository_id: str
    source_path: str
    capabilities: list[str]
    environment_ids: list[str]
    profile_ids: list[str]
    verification_run_ids: list[str] = Field(default_factory=list)
    status: Literal["experimental", "available", "validated", "deprecated", "broken"]


class Environment(Record):
    name: str
    python: str
    specification: str
    lockfile: str | None = None
    lock_digest: str | None = None
    runtime: str
    status: Literal["experimental", "available", "validated", "broken"]

    @field_validator("lock_digest")
    @classmethod
    def valid_lock_digest(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            raise ValueError("lock_digest must be sha256:<64 hex characters>")
        return value


class ResourceProfile(Record):
    name: str
    hardware_class: str
    accelerator: str
    environment_ids: list[str]
    status: Literal["experimental", "available", "validated"]


class Artifact(Record):
    kind: str
    name: str
    semantic_version: str | None = None
    producer: str | None = None
    uri: str | None = None
    repository_id: str | None = None
    revision: str | None = None
    digest: str | None = None
    media_type: str | None = None
    license: str | None = None
    availability: Literal["public", "local", "private", "missing"]
    compatible_with: list[str] = Field(default_factory=list)
    produced_by_run_id: str | None = None
    validation_status: Literal["unknown", "experimental", "validated"] = "unknown"

    @field_validator("digest")
    @classmethod
    def valid_digest(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
            raise ValueError("digest must be sha256:<64 hex characters>")
        return value


class FrozenProvider(StrictModel):
    provider_id: str
    interface_version: str
    repository_id: str
    revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    dirty: bool


class FrozenArtifact(StrictModel):
    artifact_id: str
    digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    location: str


class Run(Record):
    study_id: str
    method_id: str
    research_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    research_dirty: bool
    implementations: list[FrozenProvider] = Field(min_length=1)
    environment_id: str
    environment_lock_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    profile_id: str
    hardware_class: str
    hardware_verified: bool = False
    hardware_observation: dict[str, int] = Field(default_factory=dict)
    software_versions: dict[str, str] = Field(default_factory=dict)
    dataset_provenance: dict[str, dict] = Field(default_factory=dict)
    native_manifest_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    params_hash: str | None = None
    input_artifacts: list[FrozenArtifact]
    config_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    config_path: str
    seed: int | None = None
    command: list[str] = Field(min_length=1)
    executor: str
    started_at: datetime
    ended_at: datetime | None = None
    status: Literal["created", "running", "completed", "failed", "cancelled", "invalidated"]
    outputs: list[str] = Field(default_factory=list)
    produced_artifact_ids: list[str] = Field(default_factory=list)
    error: str | None = None
    invalidation: str | None = None

    @field_validator("started_at", "ended_at")
    @classmethod
    def aware_run_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Run timestamps must include a timezone")
        return value


class Baseline(Record):
    title: str
    protocol: str
    run_ids: list[str]
    status: Literal["proposed", "validated", "superseded"]


class PublicationManifest(Record):
    title: str
    research_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    object_ids: list[str]
    run_ids: list[str]
    artifact_ids: list[str]
    status: Literal["draft", "released"]


DIRECTORIES = {
    "graph/questions": ("Q", Question),
    "graph/claims": ("C", Claim),
    "graph/methods": ("M", Method),
    "graph/results": ("RES", Result),
    "graph/relations": ("REL", Relation),
    "graph/sources": ("SRC", Source),
    "studies": ("ST", Study),
    "infra/repositories": ("REPO", RepositoryRef),
    "infra/providers": ("INFRA", InfrastructureProvider),
    "infra/environments": ("ENV", Environment),
    "infra/profiles": ("PROFILE", ResourceProfile),
    "artifacts/registry": ("ART", Artifact),
    "runs": ("RUN", Run),
    "baselines": ("BL", Baseline),
    "publications": ("PUB", PublicationManifest),
}
