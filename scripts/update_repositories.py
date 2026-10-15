#!/usr/bin/env python3
"""Update the README's latest-public-repositories section using GitHub's REST API."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "mohammadzakariya07")
README_PATH = Path(os.environ.get("README_PATH", "README.md"))
START = "<!-- LATEST_REPOS_START -->"
END = "<!-- LATEST_REPOS_END -->"
MAX_REPOS = int(os.environ.get("MAX_REPOS", "6"))


def request_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-profile-readme-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def safe(value):
    return str(value or "").replace("|", r"\|").replace("\r", " ").replace("\n", " ").strip()


def main():
    readme = README_PATH.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit("README is missing the LATEST_REPOS marker comments.")

    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?type=public&sort=pushed&direction=desc&per_page=100"
    )
    repos = request_json(url)
    repos = [
        repo for repo in repos
        if not repo.get("private", True)
        and not repo.get("fork", False)
        and not repo.get("archived", False)
    ]
    repos.sort(key=lambda repo: repo.get("pushed_at") or repo.get("created_at") or "", reverse=True)
    repos = repos[:MAX_REPOS]

    if not repos:
        section = "_No public non-fork repositories found yet. Add projects to your GitHub account and this section will update automatically._"
    else:
        rows = [
            "| Repository | Description | Language | Last updated |",
            "|---|---|---|---|",
        ]
        for repo in repos:
            name = safe(repo.get("name"))
            description = safe(repo.get("description")) or "—"
            language = safe(repo.get("language")) or "—"
            updated = repo.get("pushed_at") or repo.get("updated_at") or ""
            try:
                updated = datetime.fromisoformat(updated.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                updated = "—"
            html_url = repo.get("html_url", f"https://github.com/{USERNAME}/{name}")
            rows.append(f"| [{name}]({html_url}) | {description} | {language} | {updated} |")
        section = "\n".join(rows)

    start_index = readme.index(START) + len(START)
    end_index = readme.index(END)
    updated_readme = readme[:start_index] + "\n" + section + "\n" + readme[end_index:]
    if updated_readme != readme:
        README_PATH.write_text(updated_readme, encoding="utf-8")
        print(f"Updated {len(repos)} public repositories in {README_PATH}.")
    else:
        print("Repository showcase is already up to date.")


if __name__ == "__main__":
    main()
