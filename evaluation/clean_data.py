#!/usr/bin/env python3
"""
Simple script to clean up an agent run directory.
Creates a clean copy and keeps only the most recent successful run per module.
"""

import argparse
import json
import shutil
from collections import defaultdict
from pathlib import Path


def clean_package(package_path):
    """Clean a single package directory in place."""
    package_name = package_path.name
    mappings_file = package_path / "call_mappings.jsonl"

    if not mappings_file.exists():
        return

    print(f"  Cleaning {package_name}...")

    # Read all mappings and group by module
    all_runs = []
    module_runs = defaultdict(list)

    with open(mappings_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            all_runs.append(data)
            module_runs[data["module"]].append(data)

    # Track modules before
    modules_before = set(module_runs.keys())

    # For each module, find the best run (most recent successful)
    best_runs = {}
    for module, runs in module_runs.items():
        # Sort by timestamp (most recent first)
        runs.sort(key=lambda x: x["timestamp"], reverse=True)

        # Find the most recent successful run
        best_run = None
        for run in runs:
            log_file = package_path / "logs" / f"claude_call_{run['call_id']}.json"
            if log_file.exists():
                with open(log_file) as f:
                    log_data = json.load(f)
                    # Accept if is_error is false or null
                    if not log_data.get("is_error", False):
                        best_run = run
                        break

        # If no successful run, keep the most recent one
        if best_run is None:
            best_run = runs[0]

        best_runs[module] = best_run

    # Track modules after
    modules_after = set(best_runs.keys())

    # Verify module preservation
    if modules_before != modules_after:
        print(f"    ERROR: Module set changed in {package_name}!")
        print(f"    Lost: {modules_before - modules_after}")
        print(f"    Added: {modules_after - modules_before}")
        return

    # Collect IDs to keep
    keep_ids = {run["call_id"] for run in best_runs.values()}

    # Clean up logs directory - remove all files not in keep_ids
    logs_dir = package_path / "logs"
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.json"):
            call_id = log_file.stem.replace("claude_call_", "")
            if call_id not in keep_ids:
                log_file.unlink()

    # Clean up aux_files - remove directories not in keep_ids
    aux_dir = package_path / "aux_files"
    if aux_dir.exists():
        for aux_subdir in aux_dir.iterdir():
            if aux_subdir.is_dir() and aux_subdir.name not in keep_ids:
                shutil.rmtree(aux_subdir)

    # Collect all referenced bug reports
    referenced_reports = set()
    for run in best_runs.values():
        referenced_reports.update(run.get("bug_reports", []))

    # Clean up bug_reports - remove unreferenced files
    bug_dir = package_path / "bug_reports"
    if bug_dir.exists():
        for bug_file in bug_dir.glob("*.md"):
            if bug_file.name not in referenced_reports:
                bug_file.unlink()

    # Write cleaned mappings file
    with open(mappings_file, "w") as f:
        for module in sorted(best_runs.keys()):
            json.dump(best_runs[module], f)
            f.write("\n")

    print(f"    ✓ Kept {len(best_runs)}/{len(all_runs)} runs")


def count_files(results_dir):
    """Count various file types in a results directory."""
    stats = {"total_runs": 0, "json_logs": 0, "aux_dirs": 0, "bug_reports": 0}

    if not results_dir.exists():
        return stats

    for package_path in results_dir.iterdir():
        if not package_path.is_dir():
            continue

        # Count runs in mappings
        mappings_file = package_path / "call_mappings.jsonl"
        if mappings_file.exists():
            with open(mappings_file) as f:
                stats["total_runs"] += sum(1 for line in f if line.strip())

        # Count JSON logs
        logs_dir = package_path / "logs"
        if logs_dir.exists():
            stats["json_logs"] += sum(1 for _ in logs_dir.glob("*.json"))

        # Count aux directories
        aux_dir = package_path / "aux_files"
        if aux_dir.exists():
            stats["aux_dirs"] += sum(1 for d in aux_dir.iterdir() if d.is_dir())

        # Count bug reports
        bug_dir = package_path / "bug_reports"
        if bug_dir.exists():
            stats["bug_reports"] += sum(1 for _ in bug_dir.glob("*.md"))

    return stats


def verify_no_orphans(results_dir):
    """Verify that there are no orphaned files within a results directory."""
    mismatches = []

    for package_path in results_dir.iterdir():
        if not package_path.is_dir():
            continue

        package_name = package_path.name

        # Count mappings
        mappings_file = package_path / "call_mappings.jsonl"
        mapping_count = 0
        if mappings_file.exists():
            with open(mappings_file) as f:
                mapping_count = sum(1 for line in f if line.strip())

        # Count JSON logs
        logs_dir = package_path / "logs"
        json_count = 0
        if logs_dir.exists():
            json_count = sum(1 for _ in logs_dir.glob("*.json"))

        if json_count != mapping_count:
            mismatches.append(
                f"{package_name}: {json_count} JSON files vs {mapping_count} mappings"
            )

    return mismatches


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Clean an agent run directory by keeping only the most recent "
            "successful run per module."
        )
    )
    parser.add_argument(
        "results_dir",
        type=Path,
        help=("Path to the results directory"),
    )
    args = parser.parse_args()

    # Use the provided results directory directly
    results_dir = args.results_dir

    # Create clean_results alongside the provided results directory
    clean_dir = results_dir.parent / "clean_results"
    if not results_dir.exists() or not results_dir.is_dir():
        print(f"Error: {results_dir} does not exist or is not a directory")
        return

    print("=" * 70)
    print("AGENT RUN DATA CLEANING SCRIPT")
    print("=" * 70)

    # Count files before cleaning
    print("\nCounting original files...")
    stats_before = count_files(results_dir)

    # Remove existing clean directory if it exists
    if clean_dir.exists():
        print("Removing existing clean directory...")
        shutil.rmtree(clean_dir)

    # Copy the entire results directory
    print(f"Copying {results_dir.name} to {clean_dir.name}...")
    shutil.copytree(results_dir, clean_dir)

    # Clean each package
    if not clean_dir.exists():
        print("Error: No results directory found!")
        return

    print("\nCleaning packages...")
    package_count = 0

    for package_path in sorted(clean_dir.iterdir()):
        if package_path.is_dir():
            clean_package(package_path)
            package_count += 1

    # Count files after cleaning
    print("\nCounting cleaned files...")
    stats_after = count_files(clean_dir)

    # Verify no orphans
    print("\nVerifying file consistency...")
    orphan_issues = verify_no_orphans(clean_dir)

    # Print comprehensive summary
    print("\n" + "=" * 70)
    print("CLEANING SUMMARY")
    print("=" * 70)

    print(f"\nBefore cleaning ({results_dir.name}):")
    print(f"  Total runs:           {stats_before['total_runs']:,}")
    print(f"  Total JSON logs:      {stats_before['json_logs']:,}")
    print(f"  Total aux directories: {stats_before['aux_dirs']:,}")
    print(f"  Total bug reports:    {stats_before['bug_reports']:,}")

    print(f"\nAfter cleaning ({clean_dir.name}):")
    print(f"  Total runs:           {stats_after['total_runs']:,}")
    print(f"  Total JSON logs:      {stats_after['json_logs']:,}")
    print(f"  Total aux directories: {stats_after['aux_dirs']:,}")
    print(f"  Total bug reports:    {stats_after['bug_reports']:,}")

    print("\nReduction:")
    runs_removed = stats_before["total_runs"] - stats_after["total_runs"]
    if stats_before["total_runs"] > 0:
        reduction_pct = (runs_removed / stats_before["total_runs"]) * 100
        print(
            f"  Removed {runs_removed:,} duplicate/failed runs ({reduction_pct:.1f}% reduction)"
        )

    print("\nPackage verification:")
    print(f"  Packages processed: {package_count}")

    # Verify package preservation
    packages_before = sum(1 for _ in results_dir.glob("*/call_mappings.jsonl"))
    packages_after = sum(1 for _ in clean_dir.glob("*/call_mappings.jsonl"))

    if packages_before == packages_after:
        print(f"  ✓ All {packages_before} packages preserved!")
    else:
        print(
            f"  ⚠ Warning: Package count changed from {packages_before} to {packages_after}"
        )

    # Check for orphaned files
    print("\nFile consistency check:")
    if orphan_issues:
        print("  ⚠ Found orphaned files:")
        for issue in orphan_issues:
            print(f"    - {issue}")
    else:
        print(
            f"  ✓ Perfect match! {stats_after['json_logs']} JSON logs = {stats_after['total_runs']} mappings"
        )
        print("  ✓ No orphaned files found")

    print("\n" + "=" * 70)
    print("✓ CLEANING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
