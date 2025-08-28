import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import fixit.rule
import fixit.ftypes as ftypes
from libcst import Name
from libcst.metadata import ParentNodeProvider

# Create a test rule
class TestRule(fixit.rule.LintRule):
    def __init__(self):
        super().__init__()
        self.name = "TestRule"

# Simulate the ignore_lint logic from rule.py
def test_ignore_lint_behavior(comment, rule_name="TestRule"):
    """Test how ignore_lint behaves with different comment formats."""
    
    print(f"\nComment: {repr(comment)}")
    print(f"Rule name: {rule_name}")
    
    # This simulates the logic from rule.py lines 169-183
    rule_names = (rule_name, rule_name.lower())
    
    match = ftypes.LintIgnoreRegex.search(comment)
    if match:
        _style, names = match.groups()
        print(f"  Regex matched: directive='{_style}', names='{names}'")
        
        # directive with no rules specified
        if names is None:
            print(f"  → Result: IGNORED (all rules)")
            return True
        
        # directive with specific rules
        for name in (n.strip() for n in names.split(",")):
            if name.endswith("Rule"):
                name = name[:-4]
            if name in rule_names:
                print(f"  → Result: IGNORED (matched '{name}')")
                return True
        
        print(f"  → Result: NOT IGNORED (no matching rule name)")
        return False
    else:
        print(f"  → Result: NOT IGNORED (regex didn't match)")
        return False

print("="*60)
print("Testing ignore_lint behavior with malformed rule names")
print("="*60)

# Test cases showing the bug's impact
test_cases = [
    ("# lint-ignore: TestRule", True),      # Should ignore
    ("# lint-ignore: OtherRule", False),    # Should not ignore
    ("# lint-ignore", True),                # Should ignore (all rules)
    ("# lint-ignore: [TestRule", True),     # BUG: Should NOT ignore, but does!
    ("# lint-ignore: [", True),              # BUG: Should NOT ignore, but does!
    ("# lint-ignore: Test[Rule", False),    # Partially captures "Test", doesn't match
    ("# lint-ignore: TestRule]", True),     # Captures "TestRule", matches correctly
]

for comment, expected in test_cases:
    result = test_ignore_lint_behavior(comment)
    status = "✓" if result == expected else "✗ BUG"
    print(f"  Expected ignore={expected}, Got ignore={result} [{status}]")

print("\n" + "="*60)
print("IMPACT ANALYSIS:")
print("="*60)
print("""
The bug causes the LintIgnoreRegex to fail capturing rule names that:
1. Start with non-word characters (like '[', '(', etc.)
2. Contain non-word characters after commas

When this happens, the regex captures names=None, which causes the
ignore_lint method to ignore ALL rules instead of none or specific ones.

This is a LOGIC BUG with MEDIUM severity because:
- It silently changes behavior based on typos
- A typo like '# lint-ignore: [MyRule' ignores ALL rules
- This could cause important lint violations to be missed
- Users might not realize their directive is malformed

The expected behavior would be to either:
1. Not match at all (treat as regular comment)
2. Raise a warning about malformed directive
3. Be more permissive in what characters are allowed
""")