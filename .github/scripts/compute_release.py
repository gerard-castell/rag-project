"""Compute the next SemVer tag and release notes from Conventional Commits.

Reads commits between the last `vX.Y.Z` tag and HEAD (each one is a squash-merge
commit whose subject is a PR title, enforced by pr-title.yml). Writes GitHub Actions
outputs describing whether a release is needed, the next version, and a path to a
generated release-notes file.
"""

from __future__ import annotations

import os
import re
import subprocess

COMMIT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<subject>.+)$"
)
SECTION_TITLES = {
    "breaking": "Breaking Changes",
    "feat": "Features",
    "fix": "Bug Fixes",
}


def run(*args: str) -> str:
    """Run a command and return its trimmed stdout."""
    return subprocess.run(
        args, check=True, capture_output=True, text=True
    ).stdout.strip()


def last_tag() -> str | None:
    """Return the highest existing `vX.Y.Z` tag, or None if there isn't one."""
    result = subprocess.run(
        ["git", "tag", "-l", "v*.*.*", "--sort=-v:refname"],
        check=True,
        capture_output=True,
        text=True,
    )
    tags = [t for t in result.stdout.splitlines() if t]
    return tags[0] if tags else None


def commit_log(commit_range: str | None) -> list[tuple[str, str]]:
    """Return (sha, subject) pairs for commits in `commit_range` (or all history)."""
    args = ["git", "log", "--pretty=format:%H%x01%s%x02"]
    if commit_range:
        args.insert(2, commit_range)
    output = run(*args)
    if not output:
        return []
    commits = []
    for chunk in output.split("\x02"):
        chunk = chunk.strip()
        if not chunk:
            continue
        sha, _, subject = chunk.partition("\x01")
        commits.append((sha, subject))
    return commits


def classify(commits: list[tuple[str, str]]) -> tuple[str, dict[str, list[str]]]:
    """Derive the SemVer bump and per-section notes from commit subjects."""
    bump = "none"
    sections: dict[str, list[str]] = {}
    for sha, subject in commits:
        match = COMMIT_RE.match(subject)
        if not match:
            continue
        commit_type = match.group("type")
        breaking = bool(match.group("breaking"))
        entry = f"- {match.group('subject')} ({sha[:7]})"

        if breaking:
            bump = "major"
            sections.setdefault("breaking", []).append(entry)
        elif commit_type == "feat":
            if bump != "major":
                bump = "minor"
            sections.setdefault("feat", []).append(entry)
        elif commit_type == "fix":
            if bump not in ("major", "minor"):
                bump = "patch"
            sections.setdefault("fix", []).append(entry)
    return bump, sections


def bump_version(current: str, bump: str) -> str:
    """Apply a major/minor/patch bump to a `vX.Y.Z` version string."""
    major, minor, patch = (int(part) for part in current.lstrip("v").split("."))
    if bump == "major":
        return f"v{major + 1}.0.0"
    if bump == "minor":
        return f"v{major}.{minor + 1}.0"
    return f"v{major}.{minor}.{patch + 1}"


def write_notes(path: str, sections: dict[str, list[str]]) -> None:
    """Write grouped release notes (Breaking/Features/Fixes) to `path`."""
    lines = []
    for key in ("breaking", "feat", "fix"):
        if key in sections:
            lines.append(f"## {SECTION_TITLES[key]}")
            lines.extend(sections[key])
            lines.append("")
    with open(path, "w") as f:
        f.write("\n".join(lines).strip() + "\n")


def main() -> None:
    """Compute the next release version and write it to GitHub Actions outputs."""
    github_output = os.environ["GITHUB_OUTPUT"]
    notes_path = os.environ.get("NOTES_PATH", "release-notes.md")

    previous = last_tag()

    if previous is None:
        # No tags yet: seed the v0.1.0 baseline (phase-0, boots and runs).
        with open(github_output, "a") as f:
            f.write("release=true\n")
            f.write("previous=(none)\n")
            f.write("version=v0.1.0\n")
            f.write(f"notes_path={notes_path}\n")
        write_notes(notes_path, {})
        with open(notes_path, "a") as f:
            f.write("Initial tagged release.\n")
        return

    commits = commit_log(f"{previous}..HEAD")
    bump, sections = classify(commits)

    with open(github_output, "a") as f:
        if bump == "none":
            f.write("release=false\n")
            return
        next_version = bump_version(previous, bump)
        f.write("release=true\n")
        f.write(f"previous={previous}\n")
        f.write(f"version={next_version}\n")
        f.write(f"notes_path={notes_path}\n")
    write_notes(notes_path, sections)


if __name__ == "__main__":
    main()
