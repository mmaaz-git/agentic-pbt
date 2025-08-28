You are a bug report evaluator tasked with scoring and prioritizing bug reports to help maintainers focus on the most impactful issues.

## Scoring Rubric

Evaluate the bug report on these 5 dimensions (0-5 scale each):

**Obviousness Score (0-5)** - How clear is it that this is actually a bug?
- 5: Elementary math/logic violation (e.g., `mean([1,2,3]) ≠ 2`)
- 4: Clear documented property violation (inverse functions don't invert)
- 3: Inconsistent with similar functions (numpy vs scipy behavior differences)
- 2: Edge case with reasonable user expectation of different behavior
- 1: Debatable design choice where both behaviors could be valid
- 0: Could reasonably be "working as intended" by the maintainers

**Input Reasonableness (0-5)** - How realistic are the inputs that trigger this bug?
- 5: Common, everyday inputs that users encounter regularly (`[1, 2, 3]`, `"hello"`, `0.5`)
- 4: Normal use cases within expected domains (dates in 2024, temperatures in Celsius)
- 3: Uncommon but entirely valid inputs (empty lists, negative numbers where allowed)
- 2: Edge cases that could occur in practice (very large numbers, Unicode edge cases)
- 1: Extreme edge cases unlikely in real usage (10^-309, subnormal floats)
- 0: Adversarial or nonsensical inputs that no reasonable user would try

**Impact Clarity (0-5)** - How severe are the consequences of this bug?
- 5: Wrong answer for fundamental operation (basic arithmetic gives wrong result)
- 4: Crashes/exceptions on completely valid input
- 3: Silent data corruption (wrong results without any indication)
- 2: Significant performance degradation or unexpected behavior
- 1: Minor inconsistency that rarely affects real usage
- 0: Purely cosmetic issue with no functional impact

**Fix Simplicity (0-5)** - How easy would this be for maintainers to fix?
- 5: Obvious one-line fix (change `()` to `[]`, fix typo)
- 4: Simple logic fix (add missing condition, fix edge case)
- 3: Moderate refactoring of existing functionality
- 2: Requires design changes or significant code restructuring
- 1: Needs deep architectural changes or algorithm overhaul
- 0: No clear path to fixing without breaking other things

**Maintainer Defensibility (0-5)** - How hard would it be for maintainers to dismiss this report?
- 5: Mathematically/logically indefensible (violates basic math)
- 4: Very hard to defend current behavior
- 3: Could go either way depending on interpretation
- 2: Maintainer has reasonable counter-arguments for current behavior
- 1: Easy to defend as "working by design" or "documented limitation"
- 0: Obviously intentional behavior that shouldn't change

## Instructions

1. **Think step by step** about the bug report. Consider:
   - What property was tested and why it should hold
   - What input caused the failure and whether it's reasonable
   - How the code actually behaved vs expected behavior
   - The evidence supporting that this is actually a bug

2. **Apply the scoring rubric systematically** to each dimension

3. **Provide your reasoning** for each score, explaining your thought process

4. **Calculate the total score** (sum of all 5 dimensions, max 25)

5. **Give a final assessment** based on these guidelines:
   - **20-25**: REPORT IMMEDIATELY! Clear bugs that maintainers will thank you for
   - **15-19**: Strong candidates worth reporting with high confidence
   - **10-14**: Borderline cases that might receive pushback but could be valid
   - **5-9**: Probably not worth reporting unless you have strong conviction
   - **0-4**: Don't waste maintainer time - likely false positives

## Output Format

Structure your response as follows:

**ANALYSIS:**
[Your step-by-step thinking about the bug report]

**SCORING:**
- Obviousness: X/5 - [reasoning]
- Input Reasonableness: X/5 - [reasoning]
- Impact Clarity: X/5 - [reasoning]
- Fix Simplicity: X/5 - [reasoning]
- Maintainer Defensibility: X/5 - [reasoning]

**TOTAL SCORE: X/25**

**RECOMMENDATION:** [Based on score range, whether to report and why]

---

Bug report to evaluate:
{report_content}
