"""Minimal reproduction of the bug found in copier._jinja_ext."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._jinja_ext import YieldEnvironment, YieldExtension

# Test case that should fail
env = YieldEnvironment(extensions=[YieldExtension])

# The minimal failing case from Hypothesis
var_name = 'A'
iterable_name = 'B'
body_content = '0'

# Create template with static body content
template_str = f"{{% yield {var_name} from {iterable_name} %}}{body_content}{{% endyield %}}"
print(f"Template: {template_str}")

template = env.from_string(template_str)

# Test 1: Empty iterable
context = {iterable_name: [], var_name: "test"}
result = template.render(context)
print(f"\nTest 1 - Empty iterable:")
print(f"  Context: {context}")
print(f"  Result: {repr(result)}")
print(f"  Expected: '' (empty string)")
print(f"  Actual result == '': {result == ''}")

# Test 2: Non-empty iterable
context2 = {iterable_name: [1, 2, 3]}
result2 = template.render(context2)
print(f"\nTest 2 - Non-empty iterable:")
print(f"  Context: {context2}")
print(f"  Result: {repr(result2)}")

# Test 3: What about with actual variable reference?
template_str2 = f"{{% yield {var_name} from {iterable_name} %}}{{{{{var_name}}}}}{{% endyield %}}"
print(f"\nTest 3 - Variable reference in body:")
print(f"  Template: {template_str2}")
template2 = env.from_string(template_str2)
result3 = template2.render({iterable_name: []})
print(f"  Result with empty iterable: {repr(result3)}")

# Check environment attributes
print(f"\nEnvironment attributes after last render:")
print(f"  yield_name: {env.yield_name}")
print(f"  yield_iterable: {env.yield_iterable}")