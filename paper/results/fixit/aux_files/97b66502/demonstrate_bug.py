import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import fixit.ftypes as ftypes

print("DEMONSTRATION OF BUG IN LintIgnoreRegex")
print("="*60)
print()

# The regex from fixit/ftypes.py
print("The regex is supposed to parse lint directives like:")
print("  # lint-ignore")
print("  # lint-ignore: RuleName")
print("  # lint-ignore: Rule1, Rule2")
print()

test_cases = [
    ("# lint-ignore: MyRule", "Working correctly"),
    ("# lint-ignore: MyRule, OtherRule", "Working correctly"),
    ("# lint-ignore: [MyRule", "BUG: Typo with '[' bracket"),
    ("# lint-ignore: (MyRule)", "BUG: Parentheses around rule"),
    ("# lint-ignore: My-Rule", "BUG: Hyphen in rule name"),
    ("# lint-ignore: My Rule", "BUG: Space in rule name"),
]

print("Test Results:")
print("-" * 60)

for comment, description in test_cases:
    match = ftypes.LintIgnoreRegex.search(comment)
    
    print(f"\nInput:  {repr(comment)}")
    print(f"        ({description})")
    
    if match:
        directive, rule_names = match.groups()
        print(f"Output: directive={repr(directive)}, rules={repr(rule_names)}")
        
        # Analyze the result
        if ":" in comment:
            expected_rules = comment.split(":", 1)[1].strip()
            if rule_names is None:
                print(f"  ⚠️  BUG: Expected to capture '{expected_rules}' but got None")
                print(f"       This will cause ALL rules to be ignored!")
            elif rule_names != expected_rules:
                print(f"  ⚠️  BUG: Captured '{rule_names}' instead of '{expected_rules}'")
    else:
        print(f"Output: No match")

print("\n" + "="*60)
print("BUG SUMMARY:")
print("-" * 60)
print("""
When the LintIgnoreRegex encounters rule names that start with 
non-word characters (anything except a-z, A-Z, 0-9, _), it fails 
to capture the rule names and returns None for the second group.

This causes the ignore_lint method to treat it as if NO specific 
rules were listed, which means ALL rules get ignored.

Example impact:
  '# lint-ignore: [TestRule'  (typo with bracket)
  
  Expected: Directive is ignored (malformed) or raises error
  Actual:   ALL lint rules are ignored for this line
  
This is dangerous because a simple typo can accidentally disable
all linting rules, and the user has no indication this happened.
""")