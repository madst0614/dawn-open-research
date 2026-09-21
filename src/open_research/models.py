"""Strict v1 manifests. Cross-object constraints live in store.py."""

from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Program(StrictModel):
    id: str
    namespace: str = Field(pattern=r"^[A-Z][A-Z0-9]{1,15}$")
    schema_version: Literal[1]
    title: str
    mission: str
    repository: str
    views: list[str]
    id_scheme: str
    review_policy: str
    default_baseline_id: str | None = None
    citation_convention: str


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


class Claim(Record):
    title: str
    proposition: str
    scope: str = Field(min_length=1)
    status: Literal["proposed", "tentative", "supported", "robust", "disputed", "limited", "contradicted", "superseded"]


class Question(Record):
    title: str
    question: str
    status: Literal["proposed", "open", "scoped", "active", "partially_resolved", "resolved", "blocked", "superseded"]


class Insight(Record):
    title: str
    interpretation: str
    scope: str


class Probe(Record):
    title: str
    method: str
    protocol: str
    status: Literal["proposed", "specified", "validated", "deprecated"]


class Evidence(Record):
    title: str
    observation: str
    scope: str
    limitations: str
    run_ids: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    authors: list[str]
    reviewers: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_provenance(self):
        if not (self.run_ids or self.source_ids):
            raise ValueError("Evidence requires a Run or Source")
        return self


class Source(Record):
    title: str
    source_type: Literal["paper", "book", "dataset", "repository", "documentation", "benchmark", "other"]
    uri: str
    source_statement: str


class Relation(Record):
    source_id: str
    target_id: str
    relation_class: Literal["semantic", "provenance"]
    relation_type: str
    status: Literal["proposed", "accepted", "disputed", "rejected", "superseded"]
    asserted_by: str
    asserted_at: datetime
    rationale: str = Field(min_length=1)
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


class Exploration(Record):
    title: str
    lifecycle: Literal["draft", "planned", "active", "completed", "blocked", "superseded"]
    graph_context: list[str] = Field(default_factory=list)
    targets: list[str] = Field(default_factory=list)
    goal: str
    motivation: str
    probe_ids: list[str] = Field(default_factory=list)
    requires: Requirements = Field(default_factory=Requirements)
    profile_ids: list[str] = Field(default_factory=list)
    entrypoint: str | None = None
    entrypoint_probe_id: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    completion_criteria: str
    known_limitations: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    declared_readiness: Literal["draft", "local", "public", "blocked"] | None = None

    @model_validator(mode="after")
    def executable_probe_is_explicit(self):
        if self.entrypoint and self.entrypoint_probe_id not in self.probe_ids:
            raise ValueError("entrypoint_probe_id must name a Probe in probe_ids")
        if self.entrypoint_probe_id and not self.entrypoint:
            raise ValueError("entrypoint_probe_id requires an entrypoint")
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
    exploration_id: str
    probe_id: str
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
    "graph/claims": ("C", Claim), "graph/questions": ("Q", Question),
    "graph/insights": ("I", Insight), "graph/probes": ("P", Probe),
    "graph/evidence": ("E", Evidence), "graph/sources": ("S", Source),
    "graph/relations": ("R", Relation), "explorations": ("X", Exploration),
    "infra/repositories": ("REPO", RepositoryRef),
    "infra/providers": ("INFRA", InfrastructureProvider),
    "infra/environments": ("ENV", Environment),
    "infra/profiles": ("PROFILE", ResourceProfile),
    "artifacts/registry": ("ART", Artifact), "runs": ("RUN", Run),
    "baselines": ("BL", Baseline), "publications": ("PUB", PublicationManifest),
}
