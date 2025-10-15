---
date: 2025-XX-XX
title: Finding Bugs with AI agents and Hypothesis
author: Muhammad Maaz, Liam DeVoe, Zac Hatfield-Dodds, Nicholas Carlini
---

We built an AI agent that explores Python codebases and automatically writes Hypothesis tests. We pointed it at 100+ popular packages and found real bugs in NumPy, SciPy, Pandas, and others, several of which have already been patched.

For the full details, see our [paper](https://arxiv.org/abs/2510.09907) and [code](https://github.com/mmaaz-git/agentic-pbt). You can also see all the bugs we found [here](https://github.com/mmaaz-git/agentic-pbt-site).

## The Idea

Property-based testing is highly effective at finding bugs in code as it can catch edge cases that traditional example-based testing misses. However, it can be difficult to derive good properties, and write good Hypothesis tests, i.e., specifying the input domain and assertions. Building on recent advances in large language models' understanding of code, we built an agent that can automatically write Hypothesis tests for Python codebases.

The agent is simply pointed at a directory, a module, a file, or a function. It will then read the code, pick up on hints from things like types, docstrings, and existing tests. Then, it will propose properties and write tests for them.

Crucially, it then reflects on failures and successes, and adjust the test if it thinks so. Eventually, it will generate a bug report if it thinks it has found a bug. This _self-reflection loop_ is critical for reducing false positives. For example, sometimes a test may pass, but that may just be because the test is too week. One example we observed was that the test may wrap everything in a try/except block, which would hide failures; after removing it, the test justifiably failed. If the test fails at first, it may be an issue of an inappropriate input domain or an incorrect property. For example, a test may fail because the input domain allows inputs which are assumed to be invalid by the code.

Throughout, we emphasize to the agent that properties should be _high-value_ and _strongly supported_ by evidence. In the prompt, we provide a basic Hypothesis reference guide, and some basic guidelines on how to write good tests, such as:

```
- Use `math.isclose()` or `pytest.approx()` for float comparisons
- Focus on properties that reveal genuine bugs when violated
- Use `@settings(max_examples=1000)` to increase testing power
- Constrain inputs intelligently rather than defensive programming
- Do not constrain strategies unnecessarily. Prefer e.g. `st.lists(st.integers())` to `st.lists(st.integers(), max_size=100)`, unless the code itself requires `len(lst) <= 100`.
```

## Usage

The agent is operationalized as a [Claude Code command](https://www.claude.com/product/claude-code). You can get the agent by getting the `hypo.md` file from the [code](https://github.com/mmaaz-git/agentic-pbt), or directly getting it from this [link](https://github.com/mmaaz-git/agentic-pbt/blob/main/hypo.md). Then, copy it into the `<project_root>/.claude/commands/` or `~/.claude/commands/`. Now, you can invoke it inside Claude Code with `/hypo <target>`. For example:

```
/hypo requests
/hypo numpy.abs
/hypo your_code.py
```

Because the agent is essentially a markdown file, you can also use it with other coding agent software, with appropriate modifications.

## A Real Example

Let's walk through what happened when we pointed the agent at `numpy.random.wald`.

The agent starts by investigating the function. It reads the signature, the docstring, and the source code. It searches for existing tests in NumPy's test suite. From the existing tests, it discovers that `mean` must be greater than 0, and `scale` must be greater than 0.

It also realizes that the function ought to only produce positive values, which is a mathematical fact of the Wald distribution.

Based on this understanding, the agent proposes several properties to test:

1. All outputs must be positive (mathematical guarantee of the Wald distribution)
2. No NaN or Inf values should appear with valid inputs
3. Output shape should match the size parameter
4. Mean and scale arrays should broadcast correctly
5. Same seed should produce deterministic results

The agent then writes Hypothesis tests. Here's the test it writes for the positivity property:

```python
from hypothesis import given, strategies as st, settings
import numpy as np

positive_floats = st.floats(min_value=1e-10, max_value=1e6, allow_nan=False, allow_infinity=False)

@given(
    mean=positive_floats,
    scale=positive_floats,
    size=st.integers(min_value=1, max_value=1000)
)
@settings(max_examples=1000)
def test_wald_all_outputs_positive(mean, scale, size):
    """Test that all Wald distribution samples are positive."""
    samples = np.random.wald(mean, scale, size)
    assert np.all(samples > 0), f"Found non-positive values: {samples[samples <= 0]}"

```

Observe for example that the agent does constrain the mean and scale to be positive, as the docstring instructs.

The test runs. And it fails!

The agent reflects on this failure. It writes a minimal reproduction of the bug, and finds that it is indeed a real bug. It generates a bug report, which you can read [here](https://github.com/mmaaz-git/agentic-pbt/blob/main/paper/reported_bugs/numpy.md).

We traced the bug to a catastrophic cancellation in NumPy's implementation. We wrote a more numerically stable formulation and submitted it as a pull request. The NumPy maintainers confirmed the bug and merged our fix. Their analysis showed our reformulation has nearly ten orders of magnitude lower relative error than the previous algorithm. See the [pull request](https://github.com/numpy/numpy/pull/29609).

## Our Large-Scale Experiment

We ran the agent on over 100 popular Python packages spanning numerical computing, web frameworks, parsers, databases, and more. After filtering for the highest-priority reports and extensive manual validation, we (manually) reported bugs to maintainers.

Here are some of the bugs we found and reported:

1. **`numpy`** (`numpy.random.wald`): Returns zero or negative values for certain parameter combinations, violating the mathematical definition of the Wald distribution. [Agent's report](https://github.com/mmaaz-git/agentic-pbt/blob/main/paper/reported_bugs/numpy.md) | [Patch merged](https://github.com/numpy/numpy/pull/29609)

2. **`aws-lambda-powertools`** (`slice_dictionary`): Returns the first chunk repeatedly because the iterator is never incremented. The agent caught this by testing that slicing and reconstructing should return the original dictionary. [Agent's report](https://github.com/mmaaz-git/agentic-pbt/blob/main/paper/reported_bugs/aws.md) | [Patch submitted](https://github.com/aws-powertools/powertools-lambda-python/pull/7246)

3. **`cloudformation-cli-java-plugin`** (`item_hash`): Produces the same hash value for all lists, i.e., `hash(None)`, because it uses the in-place `.sort()` method, which returns `None`. The agent tested that hashes of different inputs should be different. [Agent's report](https://github.com/mmaaz-git/agentic-pbt/blob/main/paper/reported_bugs/cloudformation.md) | [Patch merged](https://github.com/aws-cloudformation/cloudformation-cli/pull/1106)

4. **`tokenizers`** (`EncodingVisualizer.calculate_label_colors`): Missing a closing parenthesis, producing invalid HSL CSS. The agent tested that the output should match the regex for a valid HSL color code. [Agent's report](https://github.com/mmaaz-git/agentic-pbt/blob/main/paper/reported_bugs/tokenizers.md) | [Patch merged](https://github.com/huggingface/tokenizers/pull/1853)

5. **`python-dateutil`** (`easter`): Returns a non-Sunday date for some years when using the Julian calendar. We reported this as a bug, but the maintainers clarified that this is actually intended behavior due to differences between calendar systems. They acknowledged the semantics are subtle. [Agent's report](https://github.com/mmaaz-git/agentic-pbt/blob/main/paper/reported_bugs/dateutil.md) | [Issue closed as invalid](https://github.com/dateutil/dateutil/issues/1437)

The `python-dateutil` case is instructive. It shows a key limitation of the agent: when code has complex or subtle semantics, the "obvious" property might not be the right one. The agent inferred "Easter should be on Sunday" from the Gregorian calendar behavior, but missed the nuance that Julian calendar dates work differently.

You can browse all the bug reports, validated and unvalidated, at our [bug database](https://github.com/mmaaz-git/agentic-pbt-site).

## Caveats

Of course, bug reports that the agent writes are not always correct. It is still up to the developer to validate the report. In order to make the tool more useful to developers, we emphasize to:
1. only write a few high-value properties -- we often experienced that the LLM could be "overeager" and propose dozens of properties, e.g., testing various mathematical theorems, and so had to guide it to stop doing that
2. self-reflect very carefully on failures -- this is to keep the false positive rate low

Note that as a secondary measure against false positives, we also developed a rubric that can score bug reports. We found that this rubric effectively surfaces good bugs: of the top-scoring reports, more than 80% were valid. As an alternative measure, we created another agent that reads the code again and the bug report together in order to validate it. In our real-world evaluation, we got three experts to validate the bugs that the agent marked as critical before we reported them to the maintainers.

While explicit properties, like mathematical ones stated in the docstring or known by the LLM's knowledge base, are great, we found that implicit properties, like the fact that `python-dateutil` uses different calendars and hence possibly non-Sunday Easter dates, are difficult for the agent to capture. Hence, one of the key challenges in automated property-based testing is intent ambiguity. We hope that a developer using a coding agent interactively can provide additional guidance and context to the agent by, e.g., stopping it if it's going down an incorrect path and giving it additional hints.

## Conclusion

As LLMs continue to demonstrate strong code reasoning, we can use them to autonomously generate property-based tests. This could be a powerful tool for developers to use to find bugs in their codebases. We hope that you'll give it a try!