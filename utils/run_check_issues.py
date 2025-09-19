#!/usr/bin/env python3
"""
Run the `check-issue-exists` agent over many bug reports concurrently.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

VALID = re.compile(r"^(?:issue|pr):\d+$")


def infer_pkg_from_report(path: Path) -> str:
    # Expecting results/<pkg>/.../*.md
    parts = path.parts
    try:
        idx = parts.index("results")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return ""


def call_agent(slug: str, report: Path, model: str) -> tuple[str, str | None]:
    cmd = [
        "claude",
        "-p",
        "--model",
        model,
        f"/check-issue-exists {slug} {report}",
        "--allowedTools",
        "Bash(gh issue list:*)",
        "Bash(gh pr list:*)",
        "Bash(gh issue view:*)",
        "Bash(gh pr view:*)",
        "Bash(gh api rate_limit:*)",
        "Bash(sleep:*)",
        # grant read access to the reports directory
        "--add-dir",
        f"{report.parent}",
        "--output-format",
        "json",
    ]
    try:
        out = subprocess.check_output(
            cmd, text=True, stderr=subprocess.DEVNULL, timeout=600
        )
        obj = json.loads(out)
        print("result", obj)
        # Treat any non-success or error response as error
        subtype = obj.get("subtype")
        is_error = obj.get("is_error")
        if subtype != "success" or is_error is True:
            msg = obj.get("error") or obj.get("result") or "claude_error"
            return ("error", str(msg) if msg is not None else "claude_error")

        raw_result = obj.get("result", "") or ""
        if raw_result.strip() == "None":
            return ("no_match", None)

        # Extract strict token or fallback to strict full match
        m = VALID.search(raw_result)
        if m:
            return ("match", m.group(0))

        return ("no_match", None)
    except Exception as e:
        return ("error", str(e))


def iter_reports(results_dir: Path) -> Iterable[Path]:
    yield from sorted(results_dir.rglob("*.md"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Run check-issue-exists over many reports")
    ap.add_argument("--repo-map", required=True, help="Path to JSON mapping pkg -> owner/repo")
    ap.add_argument("--results-dir", default="results", help="Directory containing bug report markdown files")
    ap.add_argument("--max-workers", type=int, default=10)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--output", default="issue_matches.jsonl")
    args = ap.parse_args()

    repo_map_path = Path(args.repo_map)
    if not repo_map_path.exists():
        print(f"repo map not found: {repo_map_path}", file=sys.stderr)
        return 2

    try:
        repo_map: dict[str, str] = json.loads(repo_map_path.read_text())
    except Exception as e:
        print(f"failed to read repo map: {e}", file=sys.stderr)
        return 2

    # write claude code command to .claude/commands/check-issue-exists.md
    claude_code_path = Path(".claude/commands/check-issue-exists.md")
    claude_code_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path("check-issue-exists.md"), claude_code_path)

    results_dir = Path(args.results_dir)
    reports = list(iter_reports(results_dir))

    tasks: list[tuple[str, str, Path]] = []
    for rp in reports:
        pkg = infer_pkg_from_report(rp)
        slug = repo_map.get(pkg)
        if not slug:
            continue
        tasks.append((pkg, slug, rp))

    matches: list[dict[str, str]] = []
    total = len(tasks)
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, int(args.max_workers))) as ex:
        futs = {ex.submit(call_agent, slug, rp, args.model): (pkg, slug, rp) for pkg, slug, rp in tasks}
        for fut in as_completed(futs):
            pkg, slug, rp = futs[fut]
            status, payload = fut.result()
            done += 1
            if status == "match" and payload:
                matches.append({"repo": slug, "report": str(rp), "result": payload})
                print(f"done {pkg}/{rp} ({done}/{total}) (match {payload})", flush=True)
            elif status == "no_match":
                print(f"done {pkg}/{rp} ({done}/{total}) (no match)", flush=True)
            else:
                # error
                msg = payload or "error"
                print(f"done {pkg}/{rp} ({done}/{total}) (error {msg})", flush=True)

    out_path = Path(args.output)
    out_path.write_text("\n".join(json.dumps(m) for m in matches))
    print(f"Found {len(matches)} matches; wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
