"""Read-only Git identity used by Runs and generated exports."""

import subprocess
from pathlib import Path


def _git(repo: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise ValueError("git executable is unavailable") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "git command failed").strip().splitlines()[0]
        raise ValueError(f"cannot inspect research Git revision: {detail}") from exc
    return completed.stdout.strip()


def git_identity(repo: Path) -> tuple[str, bool]:
    """Return the current commit and whether tracked or untracked state is dirty."""

    root = repo.resolve()
    return _git(root, "rev-parse", "HEAD"), bool(_git(root, "status", "--porcelain"))
