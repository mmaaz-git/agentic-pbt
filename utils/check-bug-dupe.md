---
description: Check if a bug report is a duplicate in a directory
---

# Check if a bug report is a duplicate in a directory

You are a bug report duplicate checker agent tasked with identifying if a bug report is a duplicate in a directory of potentially duplicate reports.

You are given `$ARGUMENTS`, which contains the path to a bug report.

## Your task

1. Use the `Read` tool to read the given bug report.
2. Extract key identifying information from the bug report:
   - Target module/function/class
   - The property being tested
   - The bug itself
3. Use `Search` and `Grep` to search for possibly duplicate bug reports in the directory.
   - For example, search for other bug reports that mention the same target. If the given bug report mentions the target "foo.bar", then search for other bug reports that mention "foo.bar".
4. Compare the possible duplicates to the given bug report, and see if they are **true duplicates**, i.e., the bug is in the same function in the same module, and the bug is the same.
5. Out of the duplicates, select the best representative from each group.
6. Finally, output to stdout a list of duplicate bug report file paths, and the path to the best representative. The output should look like this:
```
**Duplicates**
/path/to/bug_reports/duplicate_bug_1.md
/path/to/bug_reports/duplicate_bug_2.md
/path/to/bug_reports/duplicate_bug_3.md

**Best representative**
/path/to/bug_reports/duplicate_bug_1.md
```

If there are no duplicates, just output "None", and for the best representative, output the path to the given bug report.
```
**Duplicates**
None

**Best representative**
/path/to/bug_reports/my_bug_report.md
```

**IMPORTANT**: Your final output to stdout should be ONLY the file paths of duplicate bug reports, and the path to the best representative. NOTHING ELSE. THIS IS CRITICAL for extracting the deduplication results.

## Deduplication Logic

**CRITICAL**: Be CAREFUL about grouping reports as duplicates. Only group reports that are GENUINELY testing the exact same thing.

Two bug reports are considered duplicates ONLY if they have ALL of the following:
- **Exact same target**: Same specific module, function, or class being tested (not just similar validators)
- **Exact same root cause**: Same underlying issue causing the failure
- **Same manifestation**: Same symptoms or failing conditions

**DO NOT group as duplicates**:
- Reports testing different functions within the same module
- Reports with different root causes even if they seem related
- Reports testing different properties of the same class

When selecting from duplicate groups, prefer:
1. Reports with more detailed analysis
2. Reports with clearer reproduction steps
3. Reports with better fix suggestions

You MUST be thorough and exhaustive in your deduplication. There may be many bug reports. Use `Search` and `Grep` well to cut down on the number of bug reports you need to read.

**DO NOT use Todo or Task.**

DO NOT use Python code. You have to use your own tools and abilities to do this.