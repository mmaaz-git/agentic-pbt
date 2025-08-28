import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from docutils.parsers.rst import directives

# Test directives.choice behavior
test_cases = [
    "left", "center", "right",  # lowercase
    "LEFT", "CENTER", "RIGHT",  # uppercase
    "Left", "Center", "Right",  # title case
    "invalid", "foo", "",       # invalid values
]

choices = ["left", "center", "right"]

for test in test_cases:
    try:
        result = directives.choice(test, choices)
        print(f"'{test}' -> '{result}' (type: {type(result)})")
    except ValueError as e:
        print(f"'{test}' -> ValueError: {e}")