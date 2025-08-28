"""Further investigation of the yield tag behavior."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._jinja_ext import YieldEnvironment, YieldExtension

print("=== Investigation of YieldExtension behavior ===\n")

# Test 1: Static content with empty iterable
print("Test 1: Static content '0' with empty iterable")
env1 = YieldEnvironment(extensions=[YieldExtension])
template1 = env1.from_string("{% yield item from items %}0{% endyield %}")
result1 = template1.render({"items": []})
print(f"  Template: {{% yield item from items %}}0{{% endyield %}}")
print(f"  Context: {{'items': []}}")
print(f"  Result: {repr(result1)}")
print(f"  Expected: '' (based on empty iterable)")
print(f"  BUG?: {result1 != ''}\n")

# Test 2: Static content with non-empty iterable
print("Test 2: Static content '0' with non-empty iterable [1, 2]")
env2 = YieldEnvironment(extensions=[YieldExtension])
template2 = env2.from_string("{% yield item from items %}0{% endyield %}")
result2 = template2.render({"items": [1, 2]})
print(f"  Result: {repr(result2)}")
print(f"  Note: yield_name={env2.yield_name}, yield_iterable={env2.yield_iterable}\n")

# Test 3: Variable reference with empty iterable
print("Test 3: Variable reference {{item}} with empty iterable")
env3 = YieldEnvironment(extensions=[YieldExtension])
template3 = env3.from_string("{% yield item from items %}{{item}}{% endyield %}")
result3 = template3.render({"items": []})
print(f"  Result: {repr(result3)}")
print(f"  yield_name={env3.yield_name}, yield_iterable={env3.yield_iterable}\n")

# Test 4: Mixed content
print("Test 4: Mixed static and variable content")
env4 = YieldEnvironment(extensions=[YieldExtension])
template4 = env4.from_string("{% yield x from xs %}prefix_{{x}}_suffix{% endyield %}")
result4 = template4.render({"xs": []})
print(f"  Template: {{% yield x from xs %}}prefix_{{{{x}}}}_suffix{{% endyield %}}")
print(f"  Result with empty list: {repr(result4)}")

env5 = YieldEnvironment(extensions=[YieldExtension])
template5 = env5.from_string("{% yield x from xs %}prefix_{{x}}_suffix{% endyield %}")
result5 = template5.render({"xs": [1]})
print(f"  Result with [1]: {repr(result5)}\n")

# Test 5: Understanding the actual behavior
print("Test 5: What is the intended behavior?")
print("  Looking at the code comment: 'Note that this extension just sets the attributes'")
print("  'but renders templates as usual.'")
print("  This suggests the body IS rendered, just the attributes are set.\n")

# Test 6: Check if it's about iteration
print("Test 6: Is this actually about iteration?")
env6 = YieldEnvironment(extensions=[YieldExtension])
template6 = env6.from_string("""
{%- for item in items -%}
  Item: {{ item }}
{%- endfor -%}
""")
result6 = template6.render({"items": []})
print(f"  Standard for loop with empty list result: {repr(result6)}")
print(f"  (Empty as expected)\n")

# Conclusion
print("=== Analysis ===")
print("The YieldExtension does NOT iterate over the iterable.")
print("It simply:")
print("1. Sets env.yield_name and env.yield_iterable attributes")
print("2. Renders the body content ONCE")
print("3. Returns the rendered content (or empty string on UndefinedError)")
print("")
print("This is NOT a bug - it's the intended behavior per the docstring:")
print("'It is the caller's responsibility to use the yield_context attribute'")
print("'in the template to generate the desired output.'")