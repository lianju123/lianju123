"""Sync private repo summaries into README.md between REPOS markers.

Reads repo metadata (name, description, language, last push) via the GitHub
API using REPO_TOKEN. Code contents are never read or published.
"""
import json
import os
import re
import sys
import urllib.request

LOGIN = "lianju123"
SKIP = set()  # repo names to hide from the public summary
README = os.path.join(os.path.dirname(__file__), "..", "README.md")
MARK_RE = re.compile(
    r"(<!-- REPOS:START -->).*?(<!-- REPOS:END -->)", re.DOTALL
)


def fetch_repos(token: str) -> list[dict]:
    url = (
        "https://api.github.com/user/repos"
        "?visibility=private&affiliation=owner&sort=pushed&per_page=100"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-repo-summary",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def esc(text: str) -> str:
    return (text or "—").replace("|", "\\|").replace("\n", " ").strip()


def build_table(repos: list[dict]) -> str:
    rows = [
        "| 仓库 | 内容 | 语言 | 最近更新 |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for r in repos:
        if r["name"] in SKIP:
            continue
        rows.append(
            f"| 🔒 `{r['name']}` | {esc(r.get('description'))} "
            f"| {r.get('language') or '—'} | {r['pushed_at'][:10]} |"
        )
    return "\n".join(rows)


def main() -> int:
    token = os.environ.get("REPO_TOKEN", "")
    if not token:
        print("REPO_TOKEN not set; leaving README unchanged.")
        return 0

    repos = fetch_repos(token)
    table = build_table(repos)
    with open(README, encoding="utf-8") as f:
        content = f.read()

    updated = MARK_RE.sub(
        lambda m: m.group(1) + "\n" + table + "\n" + m.group(2),
        content,
        count=1,
    )
    if updated != content:
        with open(README, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
        print(f"Updated summary for {len(repos)} repos.")
    else:
        print("No changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
