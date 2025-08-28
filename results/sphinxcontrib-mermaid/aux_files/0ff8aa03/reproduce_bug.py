#!/usr/bin/env python3
"""Reproduce the split_index_entry bug."""

from qthelp_module import split_index_entry, _idpattern

# Minimal failing case from Hypothesis
test_title = '\n'
test_id = 'A'
entry = f"{test_title} ({test_id})"

print(f"Input entry: {repr(entry)}")
print(f"Expected title: {repr(test_title)}")
print(f"Expected id: {repr(test_id)}")

result_title, result_id = split_index_entry(entry)
print(f"\nActual title: {repr(result_title)}")
print(f"Actual id: {repr(result_id)}")

# Let's check the regex pattern
print(f"\nRegex pattern: {_idpattern.pattern}")
match = _idpattern.match(entry)
if match:
    print(f"Regex matched!")
    print(f"Match groups: {match.groups()}")
    print(f"Match groupdict: {match.groupdict()}")
else:
    print(f"Regex did not match - returning entry as-is")

# Test with more edge cases
edge_cases = [
    (" ", "A"),
    ("  ", "A"),
    ("\t", "A"),
    ("\n\n", "A"),
    ("", "A"),  # Empty title
]

print("\n--- Testing more edge cases ---")
for title, id_part in edge_cases:
    entry = f"{title} ({id_part})"
    result_title, result_id = split_index_entry(entry)
    matches = result_title == title and result_id == id_part
    print(f"Entry: {repr(entry):20} -> Title: {repr(result_title):10} ID: {repr(result_id):10} {'✓' if matches else 'FAIL'}")