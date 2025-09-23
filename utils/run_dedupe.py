#!/usr/bin/env python3
"""
Dedupes bug reports by using `check-bug-dupe` agent.

Two modes:
- --reports-dir: run anchored dedupe within a single bug_reports directory
- --results-dir: discover <results-dir>/<pkg>/bug_reports dirs and process them in parallel

Flow per directory:
- If ≤1 report: create <reports_dir>_dedupe with a symlink to the sole report and log X -> X
- Else: iterate over reports; for each report call `/check-bug-dupe <report>` (Claude)
  - Parse "**Duplicates**" list and "**Best representative**" path
  - Build a cluster = {report} \\cup duplicates \\cup {best}
  - Keep only best; remove the whole cluster from remaining
- Write symlinks for kept reports into sibling `<reports_dir>_dedupe`
"""

import argparse
import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
from typing import Iterable, List, Tuple, Dict


def discover_bug_report_dirs(results_dir: Path) -> Iterable[Path]:
    """Find all bug_reports directories in the results directory."""
    for bug_reports_dir in results_dir.glob("*/bug_reports"):
        if bug_reports_dir.is_dir() and list(bug_reports_dir.glob("bug_report_*.md")):
            yield bug_reports_dir


def list_reports(reports_dir: Path) -> List[Path]:
    return sorted(reports_dir.glob("bug_report_*.md"))


def parse_check_bug_dupe_output(raw: str, reports_dir: Path) -> Tuple[List[Path], Path | None]:
    """Parse the output of check-bug-dupe.

    Expected format:
    **Duplicates**\n
    <path or None> (one per line)\n
    \n
    **Best representative**\n
    <path>\n
    Returns (duplicates, best_rep) where duplicates excludes "None" and invalid lines.
    """
    raw = (raw or "").strip()
    if not raw:
        return ([], None)
    lines = [ln.strip() for ln in raw.splitlines()]
    dups: List[Path] = []
    best: Path | None = None
    section = None
    for ln in lines:
        if ln == "**Duplicates**":
            section = "dups"
            continue
        if ln == "**Best representative**":
            section = "best"
            continue
        if not ln:
            continue
        if section == "dups":
            if ln.lower() == "none":
                continue
            p = Path(ln)
            if p.is_absolute() and reports_dir in p.parents and p.suffix == ".md":
                dups.append(p)
        elif section == "best":
            p = Path(ln)
            if p.is_absolute() and reports_dir in p.parents and p.suffix == ".md":
                best = p
    return (dups, best)


def call_check_bug_dupe(report: Path, model: str) -> Tuple[str, List[Path] | None, Path | None, str | None]:
    """Call the duplicate checker for one report; returns (status, duplicates, best, msg)."""
    reports_dir = report.parent
    cmd = [
        "claude",
        "-p",
        "--model",
        model,
        f"/check-bug-dupe {report}",
        "--allowedTools",
        "Search",
        "Read",
        "Grep",
        "--add-dir",
        str(reports_dir),
        "--output-format",
        "json",
    ]
    try:
        pr = subprocess.run(cmd, text=True, capture_output=True, timeout=900)
        if pr.returncode != 0:
            return ("error", None, None, pr.stderr.strip() or pr.stdout.strip() or f"exit {pr.returncode}")
        try:
            obj = json.loads(pr.stdout)
        except Exception:
            return ("error", None, None, "invalid_json")
        if not isinstance(obj, dict):
            return ("error", None, None, "unexpected_response")
        if obj.get("is_error") is True or obj.get("subtype") != "success":
            return ("error", None, None, str(obj.get("error") or obj.get("result") or "claude_error"))
        raw = (obj.get("result") or "").strip()
        dups, best = parse_check_bug_dupe_output(raw, reports_dir)
        return ("success", dups, best, None)
    except Exception as e:
        return ("error", None, None, str(e))



def create_symlink_structure(representatives: List[Path], output_dir: Path) -> int:
    """Create symlinked directory with only representative reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created_count = 0
    for report_path in representatives:
        if report_path.exists():
            target_path = output_dir / report_path.name
            try:
                if target_path.exists() or target_path.is_symlink():
                    target_path.unlink(missing_ok=True)
                target_path.symlink_to(report_path.absolute())
                created_count += 1
            except Exception as e:
                print(f"Warning: Failed to create symlink for {report_path}: {e}")
    return created_count


def get_targets_mapping(reports_dir: Path) -> Dict[str, List[Path]]:
    mapping: Dict[str, List[Path]] = {}
    # Iterate bug reports inside the directory
    for report in sorted(reports_dir.glob("bug_report_*.md")):
        if not report.is_file():
            continue
        try:
            text = report.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Match a single-line "Target:" or "Targets:" (case-insensitive, optional ** **)
        m = re.search(r"(?im)^\s*(?:\*\*)?targets?(?:\*\*)?\s*:\s*(.+)$", text)
        if not m:
            continue
        line = m.group(1).strip()
        # Extract backticked items on that line only
        items = re.findall(r"`([^`]+)`", line)
        for it in items:
            t = it.strip()
            if not t:
                continue
            mapping.setdefault(t, []).append(report)
    return mapping

def dedupe_one_dir(reports_dir: Path, model: str) -> Tuple[int, int]:
    """Loops over reports in a single reports dir and checks for duplicates.
    Returns (original_count, kept_count)."""
    files = list_reports(reports_dir)
    print(f"Processing {len(files)} reports in {reports_dir}")
    if len(files) <= 1:
        # just write a dedupe dir with the sole report if present
        out_dir = reports_dir.parent / f"{reports_dir.name}_dedupe"
        kept = create_symlink_structure(files, out_dir)
        return (len(files), kept)

    representatives: List[Path] = []
    targets_mapping = get_targets_mapping(reports_dir)

    # if a target has >=2 reports, we put those reports into `possibly_duplicate` (accounting for duplicates)
    # if a target has 1 report, we put that report into `orphans` (accounting for duplicates)
    possibly_duplicate = set()
    orphans = set()
    for target, reports in targets_mapping.items():
        if len(reports) >= 2:
            possibly_duplicate |= set(reports)
        else:
            orphans.add(reports[0])

    #print(f"Reports to check: {len(possibly_duplicate)}")

    while possibly_duplicate:
        report = possibly_duplicate.pop()
        status, dups, best, _ = call_check_bug_dupe(report, model)
        cluster = {report} | set(dups or [])
        if status == "success" and best:
            representatives.append(best)
            cluster.add(best)
        else:
            representatives.append(report)

        possibly_duplicate -= cluster
        #print(f"Remaining reports to check: {len(possibly_duplicate)}")

    final_reports = representatives + list(orphans)

    out_dir = reports_dir.parent / f"{reports_dir.name}_dedupe"
    kept = create_symlink_structure(final_reports, out_dir)
    return (len(files), kept)


def main() -> int:
    ap = argparse.ArgumentParser(description="Anchored dedupe over bug reports")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--reports-dir", help="Path to a single bug_reports directory")
    grp.add_argument("--results-dir", help="Root with <pkg>/bug_reports subdirectories")
    ap.add_argument("--max-workers", type=int, default=20, help="Maximum number of workers to use when using results_dir mode")
    ap.add_argument("--model", default="sonnet")
    args = ap.parse_args()

    # copy the check-bug-dupe command prompt for Claude
    claude_code_path = Path(".claude/commands/check-bug-dupe.md")
    claude_code_path.parent.mkdir(parents=True, exist_ok=True)
    src = Path("utils/check-bug-dupe.md")
    if src.exists():
        shutil.copy(src, claude_code_path)

    if args.reports_dir:
        reports_dir = Path(args.reports_dir).resolve()
        if not reports_dir.exists():
            print(f"reports dir not found: {reports_dir}", file=sys.stderr)
            return 2
        orig, kept = dedupe_one_dir(reports_dir, args.model)
        print(f"done {reports_dir.name}: {orig} -> {kept} reps ({orig - kept} removed)")
        return 0

    # results root mode
    results_root = Path(args.results_dir).resolve()
    if not results_root.exists():
        print(f"results root not found: {results_root}", file=sys.stderr)
        return 2
    bug_dirs = list(discover_bug_report_dirs(results_root))
    if not bug_dirs:
        print("No bug_reports directories found", file=sys.stderr)
        return 1
    print(f"Found {len(bug_dirs)} bug report directories to process")
    total = len(bug_dirs)
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, int(args.max_workers))) as ex:
        futs = {ex.submit(dedupe_one_dir, bd, args.model): bd for bd in bug_dirs}
        for fut in as_completed(futs):
            bd = futs[fut]
            try:
                orig, kept = fut.result()
            except Exception as e:
                done += 1
                print(f"done {bd.parent.name} ({done}/{total}): error {e}", flush=True)
                continue
            done += 1
            print(f"done {bd.parent.name} ({done}/{total}): {orig} -> {kept} reps ({orig - kept} removed)", flush=True)
    print("Deduplication complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())