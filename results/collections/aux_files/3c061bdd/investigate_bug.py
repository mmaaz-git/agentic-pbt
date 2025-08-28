#!/usr/bin/env python3

from flask import Flask, Blueprint
from flask.blueprints import BlueprintSetupState

# Reproduce the bug
app = Flask(__name__)
bp = Blueprint('test', __name__)

# Create a BlueprintSetupState with no URL prefix
state = BlueprintSetupState(bp, app, {"url_prefix": None}, True)

# Try to add a URL rule with an empty string
try:
    state.add_url_rule("", endpoint="test", view_func=lambda: "test")
    print("SUCCESS: Empty rule with no prefix was accepted")
except ValueError as e:
    print(f"ERROR: {e}")

# Let's check the source code logic
print("\nAnalyzing the logic in BlueprintSetupState.add_url_rule:")
print("Lines 98-102 handle the URL prefix concatenation:")
print("  if self.url_prefix is not None:")
print("      if rule:")
print("          rule = '/'.join((self.url_prefix.rstrip('/'), rule.lstrip('/')))")
print("      else:")
print("          rule = self.url_prefix")
print("\nThe issue: When url_prefix is None and rule is empty string,")
print("the rule remains empty and is passed to app.add_url_rule,")
print("which requires rules to start with '/'")

# Test more cases
print("\n\nTesting various combinations:")
test_cases = [
    (None, ""),      # Fails
    (None, "/"),     # Should work
    ("/api", ""),    # Should work (becomes /api)
    ("/api", "/"),   # Should work
]

for prefix, rule in test_cases:
    app2 = Flask(__name__)
    bp2 = Blueprint('test2', __name__)
    state2 = BlueprintSetupState(bp2, app2, {"url_prefix": prefix}, True)
    try:
        state2.add_url_rule(rule, endpoint="test", view_func=lambda: "test")
        print(f"✓ prefix={prefix!r}, rule={rule!r} -> SUCCESS")
    except ValueError as e:
        print(f"✗ prefix={prefix!r}, rule={rule!r} -> ERROR: {e}")

# Show the actual transformed rule
print("\n\nShowing actual rule transformation:")
print("When url_prefix=None and rule='', the transformation is:")
print("  Input: url_prefix=None, rule=''")
print("  After line 98-102: rule='' (unchanged because url_prefix is None)")
print("  Passed to app.add_url_rule: '' -> ValueError!")
print("\nThis violates the invariant that all URL rules must start with '/'.")