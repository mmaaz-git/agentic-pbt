#!/usr/bin/env python3
"""
Deduplicate bug reports using the Anthropic API.
Takes a folder of bug reports and identifies unique ones by grouping duplicates.
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict, Any

import anthropic


def read_bug_reports(folder_path: Path) -> List[Dict[str, str]]:
    """Read all .md files from the folder and return their contents with filenames."""
    reports = []
    for md_file in sorted(folder_path.rglob("*.md")):
        try:
            content = md_file.read_text(encoding='utf-8')
            reports.append({
                "filename": md_file.name,
                "content": content
            })
        except Exception as e:
            print(f"Warning: Could not read {md_file}: {e}", file=sys.stderr)
    return reports


def create_deduplication_prompt(reports: List[Dict[str, str]]) -> str:
    """Create a prompt for the Anthropic API to deduplicate bug reports."""

    prompt = """You are a bug report deduplication expert. You need to identify groups of duplicate bug reports and select the best representative from each group.

**CRITICAL DEDUPLICATION RULES:**
Two bug reports are considered duplicates ONLY if they have ALL of the following:
- **IDENTICAL target function/method**: Must be testing the exact same function or method (e.g., `validators.integer()` vs `validators.boolean()` are NOT duplicates even if both are validators)
- **Exact same root cause**: Same underlying issue causing the failure
- **Same manifestation**: Same symptoms or failing conditions

**BE EXTREMELY STRICT - DO NOT group as duplicates:**
- Reports testing different functions within the same module (e.g., `integer()` vs `boolean()` validators)
- Reports testing different methods of the same class (e.g., different validation methods)
- Reports with different root causes even if they seem related
- Reports testing different properties of the same class
- Reports that only share similar validation logic but test different functions

**EXAMPLES OF WHAT ARE NOT DUPLICATES:**
- `validators.integer()` bug vs `validators.boolean()` bug (different functions)
- `BaseAWSObject.__init__()` vs `SomeOtherClass.__init__()` (different classes)
- Different modules even if they have similar bugs (e.g., `troposphere.ec2` vs `troposphere.s3`)

When selecting the best representative from duplicate groups, prefer:
1. Reports with more detailed analysis
2. Reports with clearer reproduction steps
3. Reports with better fix suggestions

**INPUT:** Bug reports with their filenames:

"""

    for i, report in enumerate(reports, 1):
        prompt += f"\n--- REPORT {i} ---\n"
        prompt += f"FILENAME: {report['filename']}\n"
        prompt += f"CONTENT:\n{report['content']}\n"

    prompt += """

**TASK:**
1. Carefully analyze each bug report to extract:
   - Target module/function/class
   - The property being tested
   - The bug itself and its root cause

2. Group reports that are true duplicates (same target, same root cause, same manifestation)

3. For each group of duplicates, select the best representative

4. Output your analysis in this EXACT JSON format:
```json
{
  "duplicate_groups": [
    {
      "group_id": 1,
      "best_representative": "best_report.md",
      "duplicates": [
        "report1.md",
        "report2.md",
        "report3.md"
      ],
      "reasoning": "Brief explanation of why these are duplicates and why this representative was chosen"
    }
  ],
  "unique_reports": [
    "unique1.md",
    "unique2.md"
  ]
}
```

**IMPORTANT:**
- Include the best representative in both the "best_representative" field AND the "duplicates" list
- Only group reports that are genuinely testing the exact same thing
- Be conservative - when in doubt, don't group reports as duplicates
- Output ONLY the JSON, no other text
"""

    return prompt


async def call_anthropic_api_async(prompt: str) -> str:
    """Call the Anthropic API asynchronously with the deduplication prompt using streaming."""
    client = anthropic.AsyncAnthropic()

    try:
        stream = await client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=64000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            betas=["context-1m-2025-08-07"]
        )

        response_text = ""
        async for event in stream:
            if event.type == "content_block_delta":
                response_text += event.delta.text

        return response_text
    except Exception as e:
        raise Exception(f"Anthropic API call failed: {e}")


def call_anthropic_api(prompt: str) -> str:
    """Call the Anthropic API with the deduplication prompt using streaming."""
    client = anthropic.Anthropic()

    try:
        stream = client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=64000, # this is the output limit even for 1M context
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
            betas=["context-1m-2025-08-07"], # set this to get 1M context
            stream=True,
        )

        response_text = ""
        for event in stream:
            if event.type == "content_block_delta":
                response_text += event.delta.text

        return response_text
    except Exception as e:
        raise Exception(f"Anthropic API call failed: {e}")


def create_dedupe_folder(folder_path: Path, results: Dict[str, Any]) -> None:
    """Create a dedupe folder with symlinks to unique and best representative reports."""
    # Create bug_reports_dedupe folder in parent directory
    dedupe_folder = folder_path.parent / "bug_reports_dedupe"

    # Remove existing dedupe folder if it exists
    if dedupe_folder.exists():
        shutil.rmtree(dedupe_folder)

    dedupe_folder.mkdir()

    # Add unique reports
    for filename in results.get("unique_reports", []):
        source_path = folder_path / filename
        target_path = dedupe_folder / filename

        # Create relative symlink
        relative_source = Path("..") / "bug_reports" / filename
        target_path.symlink_to(relative_source)

    # Add best representatives from duplicate groups
    for group in results.get("duplicate_groups", []):
        filename = group["best_representative"]
        source_path = folder_path / filename
        target_path = dedupe_folder / filename

        # Create relative symlink
        relative_source = Path("..") / "bug_reports" / filename
        target_path.symlink_to(relative_source)


def parse_response(response: str) -> Dict[str, Any]:
    """Parse the JSON response from the Anthropic API."""
    try:
        # Extract JSON from response if it's wrapped in markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse API response as JSON: {e}")


async def process_single_folder(folder_path: Path, verbose: bool = False) -> tuple[Path, int, int]:
    """Process a single bug reports folder asynchronously."""
    # Read bug reports
    reports = read_bug_reports(folder_path)
    if not reports:
        print(f"Done {folder_path} (0 -> 0)")
        return folder_path, 0, 0

    original_count = len(reports)

    # Create prompt and call API
    prompt = create_deduplication_prompt(reports)
    response = await call_anthropic_api_async(prompt)

    # Parse results
    results = parse_response(response)

    # Create dedupe folder with symlinks
    create_dedupe_folder(folder_path, results)

    # Output JSON if verbose
    if verbose:
        print(f"\n=== Results for {folder_path} ===")
        print(json.dumps(results, indent=2))

    # Calculate final count
    num_unique = len(results.get("unique_reports", []))
    num_groups = len(results.get("duplicate_groups", []))
    final_count = num_unique + num_groups

    print(f"Done {folder_path} ({original_count} -> {final_count})")

    return folder_path, original_count, final_count


async def process_results_dir(results_dir: Path, max_workers: int, verbose: bool = False) -> None:
    """Process all bug_reports folders in subdirectories of results_dir."""
    # Find all bug_reports folders
    bug_reports_folders = []
    for subdir in results_dir.iterdir():
        if subdir.is_dir():
            bug_reports_path = subdir / "bug_reports"
            if bug_reports_path.exists() and bug_reports_path.is_dir():
                bug_reports_folders.append(bug_reports_path)

    if not bug_reports_folders:
        print(f"No bug_reports folders found in {results_dir}")
        return

    # Process folders in parallel with semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_workers)

    async def process_with_semaphore(folder_path):
        async with semaphore:
            return await process_single_folder(folder_path, verbose)

    # Process all folders concurrently
    tasks = [process_with_semaphore(folder) for folder in bug_reports_folders]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Calculate totals
    total_original = 0
    total_final = 0
    for result in results:
        if isinstance(result, Exception):
            print(f"Error processing folder: {result}")
        else:
            folder_path, original_count, final_count = result
            total_original += original_count
            total_final += final_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate bug reports using Claude"
    )

    # Mutually exclusive group for input modes
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--reports-dir",
        type=Path,
        help="Single folder containing bug report .md files"
    )
    input_group.add_argument(
        "--results-dir",
        type=Path,
        help="Directory containing subdirectories with bug_reports folders"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print JSON results to stdout"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=20,
        help="Maximum number of parallel workers for results-dir mode (default: 20)"
    )

    args = parser.parse_args()

    try:
        if args.reports_dir:
            # Single folder mode
            if not args.reports_dir.exists() or not args.reports_dir.is_dir():
                print(f"Error: {args.reports_dir} is not a valid directory")
                return 1

            # Process single folder synchronously
            reports = read_bug_reports(args.reports_dir)
            if not reports:
                print("No .md files found in the specified folder")
                return 1

            original_count = len(reports)

            # Create prompt and call API
            prompt = create_deduplication_prompt(reports)
            response = call_anthropic_api(prompt)

            # Parse results
            results = parse_response(response)

            # Create dedupe folder with symlinks
            create_dedupe_folder(args.reports_dir, results)

            # Output JSON if verbose
            if args.verbose:
                print(json.dumps(results, indent=2))

            # Calculate final count
            num_unique = len(results.get("unique_reports", []))
            num_groups = len(results.get("duplicate_groups", []))
            final_count = num_unique + num_groups

            print(f"Done {args.reports_dir} ({original_count} -> {final_count})")

        else:
            # Results directory mode
            if not args.results_dir.exists() or not args.results_dir.is_dir():
                print(f"Error: {args.results_dir} is not a valid directory")
                return 1

            # Process all subdirectories asynchronously
            asyncio.run(process_results_dir(args.results_dir, args.max_workers, args.verbose))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())