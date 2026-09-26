"""Read and validate the canonical Git tree."""

from dataclasses import dataclass, field
import hashlib
from pathlib import Path

import yaml
from pydantic import ValidationError

from .ids import validate_id
from .models import (
    Artifact,
    Baseline,
    Claim,
    DIRECTORIES,
    InfrastructureProvider,
    Program,
    PublicationManifest,
    Record,
    Relation,
    ResourceProfile,
    Result,
    Run,
    Study,
)


SEMANTIC = {
    "supports",
    "weakens",
    "contradicts",
    "tests",
    "investigates",
    "answers",
    "refines",
    "generalizes",
    "specializes",
    "contextualizes",
    "motivates",
    "produces",
    "reproduces",
    "related_to",
    "implements",
    "uses",
}
PROVENANCE = {"derived_from", "inspired_by", "informed_by", "independently_convergent_with"}
ENDPOINTS = {
    "supports": ({"RES"}, {"C"}),
    "weakens": ({"RES"}, {"C"}),
    "contradicts": ({"RES"}, {"C"}),
    "tests": ({"M"}, {"C"}),
    "investigates": ({"M"}, {"Q"}),
    "answers": ({"C"}, {"Q"}),
    "refines": ({"C"}, {"C"}),
    "generalizes": ({"C"}, {"C"}),
    "specializes": ({"C"}, {"C"}),
    "motivates": ({"C"}, {"Q"}),
    "produces": ({"M", "RUN"}, {"RES", "ART"}),
}


@dataclass
class Catalog:
    root: Path
    program: Program | None = None
    objects: dict[str, Record] = field(default_factory=dict)
    paths: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def of_type(self, cls):
        return [obj for obj in self.objects.values() if isinstance(obj, cls)]

    def get(self, object_id: str, cls=None):
        obj = self.objects.get(object_id)
        if obj is None or (cls and not isinstance(obj, cls)):
            raise ValueError(f"missing {cls.__name__ if cls else 'object'}: {object_id}")
        return obj


def _read_yaml(path: Path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_catalog(root: Path) -> Catalog:
    root = root.resolve()
    catalog = Catalog(root)
    try:
        catalog.program = Program.model_validate(_read_yaml(root / "program.yaml"))
        validate_id(catalog.program.id, catalog.program.namespace, "PROGRAM")
    except (OSError, ValueError, ValidationError, yaml.YAMLError) as exc:
        catalog.errors.append(f"program.yaml: {exc}")
        return catalog

    for relative, (kind, model) in DIRECTORIES.items():
        directory = root / relative
        files = sorted(directory.glob("*.yaml"))
        if relative == "runs":
            files += sorted(directory.glob("*/manifest.yaml"))
        for path in files:
            try:
                obj = model.model_validate(_read_yaml(path))
                validate_id(obj.id, catalog.program.namespace, kind)
                if obj.id in catalog.objects:
                    raise ValueError(f"duplicate ID also in {catalog.paths[obj.id]}")
                nested_run = relative == "runs" and path.name == "manifest.yaml" and path.parent.name == obj.id
                if path.stem != obj.id and not nested_run:
                    raise ValueError("file name must match object ID")
                catalog.objects[obj.id] = obj
                catalog.paths[obj.id] = path
            except (OSError, ValueError, ValidationError, yaml.YAMLError) as exc:
                catalog.errors.append(f"{path.relative_to(root)}: {exc}")
    return catalog


def validate_catalog(catalog: Catalog) -> list[str]:
    errors = list(catalog.errors)
    if not catalog.program:
        return errors
    ns = catalog.program.namespace

    def check_ref(source: Record, target_id: str, expected=None):
        try:
            validate_id(target_id, ns)
            return catalog.get(target_id, expected)
        except ValueError as exc:
            errors.append(f"{source.id}: {exc}")
            return None

    if catalog.program.default_baseline_id and catalog.program.default_baseline_id not in catalog.objects:
        errors.append("program.yaml: default baseline does not exist")

    for obj in catalog.objects.values():
        if isinstance(obj, Relation):
            source = check_ref(obj, obj.source_id)
            target = check_ref(obj, obj.target_id)
            allowed = SEMANTIC if obj.relation_class == "semantic" else PROVENANCE
            if obj.relation_type not in allowed:
                errors.append(f"{obj.id}: invalid {obj.relation_class} relation type {obj.relation_type}")
            if source and target and obj.relation_type in ENDPOINTS:
                left, right = ENDPOINTS[obj.relation_type]
                source_kind = validate_id(source.id, ns)
                target_kind = validate_id(target.id, ns)
                if source_kind not in left or target_kind not in right:
                    errors.append(f"{obj.id}: invalid endpoints for {obj.relation_type}")
            if obj.asserted_at.tzinfo is None:
                errors.append(f"{obj.id}: asserted_at requires timezone")

        elif isinstance(obj, Result):
            from .models import Source

            for ref in obj.run_ids:
                check_ref(obj, ref, Run)
            for ref in obj.source_ids:
                check_ref(obj, ref, Source)

        elif isinstance(obj, Study):
            from .models import Method, Question

            for ref in obj.question_ids:
                check_ref(obj, ref, Question)
            for ref in obj.claim_ids:
                check_ref(obj, ref, Claim)
            for ref in obj.method_ids:
                check_ref(obj, ref, Method)
            for ref in obj.requires.artifacts:
                check_ref(obj, ref, Artifact)
            for ref in obj.profile_ids:
                check_ref(obj, ref, ResourceProfile)
            if obj.declared_readiness in {"local", "public"}:
                from .resolver import resolve

                plans = []
                for profile_id in obj.profile_ids:
                    try:
                        plans.append(resolve(catalog, obj.id, profile_id))
                    except ValueError as exc:
                        errors.append(f"{obj.id}: cannot resolve profile {profile_id}: {exc}")
                if not obj.profile_ids:
                    errors.append(f"{obj.id}: declared readiness without a resource profile")
                readiness_key = "ready" if obj.declared_readiness == "local" else "publicly_reproducible"
                if plans and not any(plan[readiness_key] for plan in plans):
                    errors.append(
                        f"{obj.id}: declared {obj.declared_readiness} with missing dependencies: "
                        f"{[plan['blockers'] for plan in plans]}"
                    )

        elif isinstance(obj, InfrastructureProvider):
            from .models import Environment, RepositoryRef

            check_ref(obj, obj.repository_id, RepositoryRef)
            for ref in obj.environment_ids:
                check_ref(obj, ref, Environment)
            for ref in obj.profile_ids:
                check_ref(obj, ref, ResourceProfile)
            for ref in obj.verification_run_ids:
                verification = check_ref(obj, ref, Run)
                if verification and verification.status != "completed":
                    errors.append(f"{obj.id}: verification Run must be completed")
                if verification and not any(
                    frozen.provider_id == obj.id for frozen in verification.implementations
                ):
                    errors.append(f"{obj.id}: verification Run does not use this provider")
            if obj.status == "validated" and not obj.verification_run_ids:
                errors.append(f"{obj.id}: validated provider needs verification Run")

        elif isinstance(obj, ResourceProfile):
            from .models import Environment

            for ref in obj.environment_ids:
                check_ref(obj, ref, Environment)

        elif isinstance(obj, Artifact):
            from .models import RepositoryRef

            if obj.repository_id:
                check_ref(obj, obj.repository_id, RepositoryRef)
            if obj.produced_by_run_id:
                check_ref(obj, obj.produced_by_run_id, Run)
            if obj.availability == "public" and not (obj.uri and obj.digest):
                errors.append(f"{obj.id}: public artifact requires URI and digest")

        elif isinstance(obj, Run):
            from .models import Environment, Method, RepositoryRef

            study = check_ref(obj, obj.study_id, Study)
            check_ref(obj, obj.method_id, Method)
            environment = check_ref(obj, obj.environment_id, Environment)
            profile = check_ref(obj, obj.profile_id, ResourceProfile)
            if study and obj.method_id not in study.method_ids:
                errors.append(f"{obj.id}: Method is not part of Study")
            if study and study.entrypoint_method_id and obj.method_id != study.entrypoint_method_id:
                errors.append(f"{obj.id}: Run Method differs from Study entrypoint Method")
            if study and obj.profile_id not in study.profile_ids:
                errors.append(f"{obj.id}: profile is not supported by Study")
            if profile and environment and environment.id not in profile.environment_ids:
                errors.append(f"{obj.id}: profile/environment incompatibility")
            covered = set()
            for frozen in obj.implementations:
                provider = check_ref(obj, frozen.provider_id, InfrastructureProvider)
                check_ref(obj, frozen.repository_id, RepositoryRef)
                if provider:
                    covered.update(provider.capabilities)
                    if (
                        provider.interface_version != frozen.interface_version
                        or provider.repository_id != frozen.repository_id
                    ):
                        errors.append(f"{obj.id}: frozen provider interface/repository mismatch")
                    if obj.environment_id not in provider.environment_ids or obj.profile_id not in provider.profile_ids:
                        errors.append(f"{obj.id}: provider incompatible with Run environment/profile")
            if study and set(study.requires.capabilities) - covered:
                errors.append(f"{obj.id}: Run does not cover all required capabilities")
            for frozen in obj.input_artifacts:
                artifact = check_ref(obj, frozen.artifact_id, Artifact)
                if artifact and artifact.digest and frozen.digest != artifact.digest:
                    errors.append(f"{obj.id}: input Artifact digest differs from registry")
            if study and set(study.requires.artifacts) != {item.artifact_id for item in obj.input_artifacts}:
                errors.append(f"{obj.id}: Run input Artifacts differ from Study")
            for ref in obj.produced_artifact_ids:
                check_ref(obj, ref, Artifact)
            config_relative = Path(obj.config_path)
            if config_relative.is_absolute() or ".." in config_relative.parts:
                errors.append(f"{obj.id}: config_path must be relative to Run directory")
            else:
                config_file = catalog.paths[obj.id].parent / config_relative
                if not config_file.is_file():
                    errors.append(f"{obj.id}: config snapshot is missing")
                elif "sha256:" + hashlib.sha256(config_file.read_bytes()).hexdigest() != obj.config_digest:
                    errors.append(f"{obj.id}: config snapshot digest mismatch")
            if obj.status in {"completed", "failed", "cancelled", "invalidated"} and obj.ended_at is None:
                errors.append(f"{obj.id}: terminal Run requires ended_at")
            if obj.status == "failed" and not obj.error:
                errors.append(f"{obj.id}: failed Run requires error")
            if obj.status == "invalidated" and not obj.invalidation:
                errors.append(f"{obj.id}: invalidated Run requires reason")
            if obj.status == "completed" and study and study.entrypoint == "dawn_srw.zero_shot_eval_jax@1":
                if not (obj.native_manifest_digest and obj.software_versions and obj.dataset_provenance):
                    errors.append(f"{obj.id}: completed zero-shot Run lacks native software/dataset provenance")

        elif isinstance(obj, Baseline):
            for ref in obj.run_ids:
                check_ref(obj, ref, Run)

        elif isinstance(obj, PublicationManifest):
            for ref in obj.object_ids + obj.run_ids + obj.artifact_ids:
                check_ref(obj, ref)

    for claim in catalog.of_type(Claim):
        if claim.status in {"supported", "robust"} and not any(
            isinstance(rel, Relation)
            and rel.relation_type == "supports"
            and rel.status == "accepted"
            and rel.target_id == claim.id
            and isinstance(catalog.objects.get(rel.source_id), Result)
            for rel in catalog.objects.values()
        ):
            errors.append(f"{claim.id}: {claim.status} Claim requires accepted supporting Result relation")
    return errors
