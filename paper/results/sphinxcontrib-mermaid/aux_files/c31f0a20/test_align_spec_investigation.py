import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.mermaid import align_spec

# Test case sensitivity
test_cases = [
    "left", "center", "right",  # lowercase (expected to work)
    "LEFT", "CENTER", "RIGHT",  # uppercase
    "Left", "Center", "Right",  # title case
    "LeFt", "CeNtEr", "RiGhT",  # mixed case
]

for test in test_cases:
    try:
        result = align_spec(test)
        print(f"'{test}' -> '{result}' (ACCEPTED)")
    except ValueError as e:
        print(f"'{test}' -> ValueError: {e} (REJECTED)")