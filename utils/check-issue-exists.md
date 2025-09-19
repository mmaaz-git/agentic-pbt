---
description: Check if a bug has already been reported
---

# Check if a bug has already been reported

You are a bug report evaluator tasked with checking if a bug has already been reported to a given project.

You are given `$ARGUMENTS`, which contains:
- The GitHub URL or the slug of the project
- The path to the bug report

## Your task

1. Read the bug report.
2. Extract key information from it, like the module, the function, the actual bug itself.
3. Use the `gh` CLI tool to search for issues/PRs in the GitHub repository. Construct search queries based on the key information. For example, look for issues/PRs that mention the function name.
4. If you find a possibly matching issue/PR, analyze the reported issue/PR and compare it to the bug report. Be careful to check the details of each.
5. If you find a matching issue/PR, output to stdout the issue/PR number, in the format `issue:<number>` or `pr:<number>`. DO NOT output anything else. If you do not find a matching issue/PR, output `None`.

**IMPORTANT**: Your final output to stdout should be a SINGLE LINE, either `issue:<number>` or `pr:<number>`, or `None`. NOTHING ELSE. THIS IS CRITICAL for extracting key information.

### Example

Input: github.com/numpy/numpy my_bug_report.md
Claude turn 1: reads bug report
Claude turn 2,3,4...: searches for issues/PRs, compares them, etc.
Claude final turn: `issue:123` (NO OTHER TEXT)

## Searching for issues

You must search for issues/PRs using the `gh` CLI tool. Only search for issues/PRs within the given GitHub repository. Issues may be closed or open, so do not unnecessarily limit your search to open issues/PRs.

## Using `gh` CLI to search for issues/PRs

The basic commands are `gh issue list` and `gh pr list`. Use the `--search` flag to search for issues/PRs. You must then use the `gh issue view` or `gh pr view` command to view the issue/PR.

Build your search query by combining the following:
- `repo:<slug>` -- search within the given GitHub repository
- `in:title`, `in:body`, `in:comments` -- search in the title, body, or comments
    - Example: `in:title "abs"`
- `state:open`, `state:closed` -- filter for open or closed

## Dealing with rate limits

The `gh` CLI tool has rate limits on searches. **You must be efficient with your searches to to avoid hitting rate limits!**

Make sure to:
- think carefully about what you are searching for before you spam a bunch of queries
- use OR between search queries, e.g., "abs OR absolute"
- paginate fewer times

If you hit the rate limit, you **MUST** wait a few seconds and try again, the bash `sleep` command. You should NEVER stop searching for issues/PRs just because you hit the rate limit. It is INADEQUATE to just output that you hit the rate limit.

You can check the rate limit using the `gh api rate_limit --jq '.resources.search'` command, which will tell you the remaining requests and when the limit will reset.
