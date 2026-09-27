"""Small Git-tree CLI. Views are derived, never canonical."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

from .ids import KINDS, new_id
from .models import Claim, InfrastructureProvider, Question, Relation, Run, Study
from .resolver import readiness, resolve
from .runner import execute
from .store import load_catalog, validate_catalog
from .views import build_export, build_view


def _root(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "program.yaml").exists():
            return candidate
    raise ValueError("program.yaml not found; pass --root")


def _emit(value, as_json: bool = False):
    if as_json:
        print(json.dumps(value, indent=2, sort_keys=True, default=str))
    else:
        print(yaml.safe_dump(value, sort_keys=False, allow_unicode=True).rstrip())


def _artifact_options(values: list[str]) -> dict[str, Path]:
    paths = {}
    for value in values:
        if "=" not in value:
            raise ValueError("--artifact must be ID=PATH")
        artifact_id, path = value.split("=", 1)
        if artifact_id in paths:
            raise ValueError(f"duplicate artifact path: {artifact_id}")
        paths[artifact_id] = Path(path)
    return paths


def _status(catalog):
    claims = dict(sorted(Counter(item.status for item in catalog.of_type(Claim)).items()))
    questions = [
        {"id": item.id, "title": item.title, "status": item.status}
        for item in catalog.of_type(Question)
        if item.status not in {"resolved", "superseded"}
    ]
    studies = []
    for item in catalog.of_type(Study):
        state, blockers = readiness(catalog, item)
        studies.append(
            {
                "id": item.id,
                "title": item.title,
                "lifecycle": item.lifecycle,
                "readiness": state,
                "blockers": blockers,
            }
        )
    capabilities = {}
    for provider in catalog.of_type(InfrastructureProvider):
        for capability in provider.capabilities:
            capabilities.setdefault(capability, []).append({"id": provider.id, "status": provider.status})
    runs = sorted(catalog.of_type(Run), key=lambda run: run.started_at, reverse=True)
    return {
        "claims_by_status": claims,
        "open_questions": sorted(questions, key=lambda item: item["id"]),
        "studies": sorted(studies, key=lambda item: item["id"]),
        "capabilities": dict(sorted(capabilities.items())),
        "recent_runs": [
            {"id": run.id, "status": run.status, "study_id": run.study_id} for run in runs[:10]
        ],
    }


def _show(catalog, object_id: str):
    obj = catalog.get(object_id)
    inbound = [
        relation.model_dump(mode="json")
        for relation in catalog.of_type(Relation)
        if relation.target_id == object_id
    ]
    outbound = [
        relation.model_dump(mode="json")
        for relation in catalog.of_type(Relation)
        if relation.source_id == object_id
    ]
    runs = [
        run.id
        for run in catalog.of_type(Run)
        if run.study_id == object_id or run.method_id == object_id
    ]
    return {
        "object": obj.model_dump(mode="json"),
        "path": str(catalog.paths[object_id].relative_to(catalog.root)),
        "inbound_connections": inbound,
        "outbound_connections": outbound,
        "related_runs": runs,
    }


def _studies(catalog, query: str | None):
    rows = []
    for item in catalog.of_type(Study):
        text = " ".join(
            [item.title, item.goal, item.motivation, *item.question_ids, *item.claim_ids, *item.method_ids]
        ).lower()
        if query and query.lower() not in text:
            continue
        state, blockers = readiness(catalog, item)
        profile_ids = sorted(
            {profile_id for plan in item.execution.plans for profile_id in plan.profile_ids}
        )
        rows.append(
            {
                "id": item.id,
                "title": item.title,
                "goal": item.goal,
                "questions": item.question_ids,
                "claims": item.claim_ids,
                "methods": item.method_ids,
                "readiness": state,
                "profiles": [catalog.get(ref).name for ref in profile_ids],
                "blockers": blockers,
            }
        )
    return sorted(rows, key=lambda row: row["title"])


def build_parser():
    parser = argparse.ArgumentParser(prog="dawn")
    parser.add_argument("--root", type=Path, help="research repository root")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    for name in ("status", "show", "studies"):
        sub = commands.add_parser(name)
        sub.add_argument("--json", action="store_true")
        if name == "show":
            sub.add_argument("id")
        if name == "studies":
            sub.add_argument("query", nargs="?")
    sub = commands.add_parser("resolve")
    sub.add_argument("id")
    sub.add_argument("--method")
    sub.add_argument("--profile", required=True)
    sub.add_argument("--artifact", action="append", default=[], metavar="ID=PATH")
    sub.add_argument("--json", action="store_true")
    sub = commands.add_parser("view")
    sub.add_argument("id")
    sub.add_argument("--mode", choices=("compact", "research", "execution"), default="compact")
    sub.add_argument("--method")
    sub.add_argument("--profile")
    sub.add_argument("--json", action="store_true")
    sub = commands.add_parser("export")
    sub.add_argument("id")
    sub.add_argument("--json", action="store_true")
    sub = commands.add_parser("run")
    sub.add_argument("id")
    sub.add_argument("--method")
    sub.add_argument("--profile", required=True)
    sub.add_argument("--implementation-repo", type=Path, required=True)
    sub.add_argument("--artifact", action="append", default=[], metavar="ID=PATH")
    sub.add_argument("--executor", required=True)
    sub.add_argument("--limit", type=int, default=32)
    identity = commands.add_parser("id")
    identity_sub = identity.add_subparsers(dest="id_command", required=True)
    create = identity_sub.add_parser("new")
    create.add_argument("kind", choices=KINDS)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        catalog = load_catalog(args.root or _root(Path.cwd()))
        if catalog.errors:
            for error in catalog.errors:
                print(error, file=sys.stderr)
            return 1
        errors = validate_catalog(catalog) if args.command != "id" else []
        if args.command == "validate":
            if errors:
                for error in errors:
                    print(error, file=sys.stderr)
                return 1
            print(f"valid: {len(catalog.objects)} objects")
        elif errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        elif args.command == "id":
            print(new_id(catalog.program.namespace, args.kind))
        elif args.command == "status":
            _emit(_status(catalog), args.json)
        elif args.command == "show":
            _emit(_show(catalog, args.id), args.json)
        elif args.command == "studies":
            _emit(_studies(catalog, args.query), args.json)
        elif args.command == "resolve":
            _emit(
                resolve(
                    catalog,
                    args.id,
                    args.profile,
                    _artifact_options(args.artifact),
                    method_id=args.method,
                ),
                args.json,
            )
        elif args.command == "view":
            _emit(build_view(catalog, args.id, args.mode, args.profile, args.method), args.json)
        elif args.command == "export":
            _emit(build_export(catalog, args.id), args.json)
        elif args.command == "run":
            if args.limit <= 0:
                raise ValueError("--limit must be positive")
            run = execute(
                catalog,
                args.id,
                args.profile,
                args.implementation_repo,
                _artifact_options(args.artifact),
                args.executor,
                args.limit,
                method_id=args.method,
            )
            _emit(
                {
                    "run_id": run.id,
                    "status": run.status,
                    "manifest": f"runs/{run.id}/manifest.yaml",
                    "error": run.error,
                }
            )
            return 0 if run.status == "completed" else 1
        return 0
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
