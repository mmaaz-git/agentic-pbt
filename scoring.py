import asyncio
import glob
import time
from pathlib import Path
import re
import csv
import argparse
from anthropic import AsyncAnthropic

# Your scoring prompt constant
SCORING_PROMPT = """
You are a bug report evaluator tasked with scoring and prioritizing bug reports to help maintainers focus on the most impactful issues.

## Scoring Rubric

Evaluate the bug report on these dimensions (0-5 scale each):

**Obviousness Score (0-5)** - How clear is it that this is actually a bug?
- 5: Elementary math/logic violation (e.g., `mean([1,2,3]) ≠ 2`)
- 4: Clear documented property violation (inverse functions don't invert)
- 3: Inconsistent with similar functions (numpy vs scipy behavior differences)
- 2: Edge case with reasonable user expectation of different behavior
- 1: Debatable design choice where both behaviors could be valid
- 0: Could reasonably be "working as intended" by the maintainers

**Input Reasonableness (0-5)** - How realistic and expected are the inputs that trigger this bug?
- 5: Common, everyday inputs expected by the library (`[1, 2, 3]`, `"hello"`, `0.5`)
- 4: Normal use cases within expected domains (dates in 2024, temperatures in Celsius)
- 3: Uncommon but entirely valid inputs (empty lists, negative numbers where allowed)
- 2: Edge cases that could occur in practice (very large numbers, Unicode edge cases)
- 1: Extreme edge cases unlikely in real usage (10^-309, subnormal floats)
- 0: Adversarial or nonsensical inputs that no reasonable user would try

Notes:
* Treat type hints as implicit documentation. If a user-facing class annotates
  one of its arguments as accepting `x: str`, you should assume the user will
  respect that and only pass strings.

**Maintainer Defensibility (0-5)** - How hard would it be for maintainers to dismiss this report?
- 5: Mathematically/logically indefensible (violates basic math)
- 4: Very hard to defend current behavior
- 3: Could go either way depending on interpretation
- 2: Maintainer has reasonable counter-arguments for current behavior
- 1: Easy to defend as "working by design" or "documented limitation"
- 0: Obviously intentional behavior that shouldn't change

Notes:
* Reports against private APIs are more likely to be dimssed by maintainers.
  The codebase may rely on implicit assumptions about internal helpers. Consider
  whether a potential bug in a private API has measurable impact on the user.

## Instructions

1. **Think step by step** about the bug report. Consider:
   - What property was tested and why it should hold
   - What input caused the failure and whether it's reasonable
   - How the code actually behaved vs expected behavior
   - The evidence supporting that this is actually a bug

2. **Apply the scoring rubric systematically** to each dimension

3. **Provide your reasoning** for each score, explaining your thought process

4. **Calculate the total score** (sum of all 3 dimensions, max 15)

## Output Format

Structure your response as follows:

**ANALYSIS:**
[Your step-by-step thinking about the bug report]

**SCORING:**
- Obviousness: X/5 - [reasoning]
- Input Reasonableness: X/5 - [reasoning]
- Maintainer Defensibility: X/5 - [reasoning]

**TOTAL SCORE: X/15**

---

Bug report to evaluate:
{report_content}
"""

async def score_bug_report(client, report_path, model):
    try:
        # Read the bug report
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()

        # Make API call
        response = await client.messages.create(
            model=model,
            max_tokens=10000,
            messages=[{
                "role": "user",
                "content": SCORING_PROMPT.format(report_content=report_content)
            }]
        )

        score_text = response.content[0].text

        # Parse rubric numbers from the model output
        patterns = {
            'obviousness': r'Obviousness:\s*(\d+)\s*/\s*5',
            'input_reasonableness': r'Input\s*Reasonableness:\s*(\d+)\s*/\s*5',
            'impact_clarity': r'Impact\s*Clarity:\s*(\d+)\s*/\s*5',
            'fix_simplicity': r'Fix\s*Simplicity:\s*(\d+)\s*/\s*5',
            'maintainer_defensibility': r'Maintainer\s*Defensibility:\s*(\d+)\s*/\s*5',
            'total': r'TOTAL\s*SCORE:\s*(\d+)\s*/\s*25',
        }

        parsed_scores = {}
        for key, pattern in patterns.items():
            m = re.search(pattern, score_text, flags=re.IGNORECASE)
            parsed_scores[key] = int(m.group(1)) if m else None

        # Determine a numeric score to use for sorting/printing
        if parsed_scores.get('total') is not None:
            score = parsed_scores['total']
        else:
            # Fallback: sum available dimensions if present
            dims = [parsed_scores.get('obviousness'), parsed_scores.get('input_reasonableness'),
                    parsed_scores.get('maintainer_defensibility')]
            if any(v is not None for v in dims):
                score = sum(v for v in dims if v is not None)
            else:
                # Last resort: first integer in the text
                score_match = re.search(r'(\d+)', score_text)
                score = int(score_match.group(1)) if score_match else 0

        return {
            'file': report_path,
            'score': score,
            'parsed_scores': parsed_scores,
            'response': score_text,
        }

    except Exception as e:
        return {
            'file': report_path,
            'score': -1,
            'response': f"ERROR: {e}",
        }




async def main():
    parser = argparse.ArgumentParser(description="Score bug reports")
    parser.add_argument("--retry-failures", action="store_true", help="Retry only failures from existing CSV (removes them first and re-runs)")
    parser.add_argument("reports_dir", type=str, help="Base directory to search recursively for bug reports")
    parser.add_argument("--max-workers", type=int, default=20, help="Maximum number of concurrent API calls (default: 20)")
    parser.add_argument("--model", type=str, default="claude-opus-4-1", help="Model name for scoring (default: claude-opus-4-1)")
    parser.add_argument("--csv-path", type=str, default="scoring_results.csv", help="Path to write/read the CSV results (default: scoring_results.csv)")
    args = parser.parse_args()
    # Initialize client
    client = AsyncAnthropic()

    # CSV path and schema
    csv_path = args.csv_path
    fieldnames = [
        'file', 'score',
        'obviousness', 'input_reasonableness', 'maintainer_defensibility', 'response'
    ]

    # Build file list depending on mode
    if args.retry_failures and Path(csv_path).exists():
        existing_rows = []
        retry_files = []
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        s = int(row.get('score', -1))
                    except ValueError:
                        s = -1
                    if s < 0 and row.get('file'):
                        retry_files.append(row['file'])
                    else:
                        existing_rows.append(row)
        except Exception:
            existing_rows = []
            retry_files = []

        report_files = retry_files
        print(f"Retrying {len(report_files)} failed bug reports from CSV")
    else:
        # Fresh discovery
        base_dir = str(Path(args.reports_dir).expanduser().resolve())
        # Search recursively for any bug_report*.md under the base directory
        pattern = str(Path(base_dir) / "**" / "bug_report*.md")
        report_files = glob.glob(pattern, recursive=True)
        print(f"Searching under {base_dir}")
        print(f"Found {len(report_files)} bug reports to score")

    # Semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(max(1, int(args.max_workers)))

    start_time = time.time()

    # Wrapper to bound concurrency without passing semaphore around
    async def _run(path):
        async with semaphore:
            return await score_bug_report(client, path, args.model)

    total = len(report_files)
    completed = 0
    # Create tasks for all reports
    tasks = [asyncio.create_task(_run(report_path)) for report_path in report_files]

    # Run tasks and report progress as each finishes
    results = []
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)
        completed += 1
        if result and 'file' in result:
            file_name = Path(result['file']).name
            if result.get('score', -1) == -1:
                print(f"❌ {file_name}: {result.get('response')} ({completed}/{total})")
            else:
                print(f"✅ {file_name}: {result['score']}/25 ({completed}/{total})")
        else:
            print(f"✅ Completed {completed}/{total}")

    # Calculate totals
    total_duration = time.time() - start_time
    successful = len([r for r in results if r and r['score'] > -1])

    print(f"\n🎉 COMPLETE!")
    print(f"📊 Scored {successful}/{len(report_files)} reports successfully")
    print(f"⏱️  Total duration: {total_duration:.1f} seconds")

    # Save results to CSV
    def result_to_row(res: dict) -> dict:
        parsed = res.get('parsed_scores') or {}
        return {
            'file': res.get('file'),
            'score': res.get('score'),
            'obviousness': parsed.get('obviousness'),
            'input_reasonableness': parsed.get('input_reasonableness'),
            'maintainer_defensibility': parsed.get('maintainer_defensibility'),
            'response': res.get('response'),
        }

    if args.retry_failures and Path(csv_path).exists():
        # Merge existing successes with newly retried results
        merged_rows = existing_rows + [result_to_row(r) for r in results if r]
        # Optionally sort by score desc then file
        try:
            merged_rows.sort(key=lambda x: (int(x.get('score', -1)), x.get('file', '')), reverse=True)
        except Exception:
            pass
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(merged_rows)
        print(f"📄 CSV updated with retried results: {csv_path}")
    else:
        # Fresh write of all results
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for result in sorted(results, key=lambda x: x['score'] if x else 0, reverse=True):
                if not result:
                    continue
                writer.writerow(result_to_row(result))
        print(f"📄 CSV saved to {csv_path}")

if __name__ == "__main__":
    asyncio.run(main())
