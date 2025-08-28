"""Reproduce the HTTPMethodNotAllowed template bug"""

import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.httpexceptions as httpexc

print("=== Bug Reproduction: HTTPMethodNotAllowed Template Issue ===\n")

# Create HTTPMethodNotAllowed instance
exc = httpexc.HTTPMethodNotAllowed(detail='Test detail')

print(f"Exception class: {exc.__class__.__name__}")
print(f"Body template: {exc.body_template_obj.template[:100]}...")

# Check what variables the template expects
import re
template_vars = re.findall(r'\$\{?(\w+)\}?', exc.body_template_obj.template)
print(f"\nTemplate variables found: {set(template_vars)}")

# Try to substitute with minimal variables
print("\nTest 1: Substitute with basic variables")
try:
    result = exc.body_template_obj.substitute(
        explanation=exc.explanation,
        detail='test',
        html_comment='',
        br='<br/>'
    )
    print(f"Success: {result[:100]}...")
except KeyError as e:
    print(f"KeyError: Missing variable '{e}'")

# Let's check the actual template for HTTPMethodNotAllowed
print("\n=== Checking HTTPMethodNotAllowed specifically ===")
print(f"Has custom body_template: {hasattr(httpexc.HTTPMethodNotAllowed, 'body_template_obj')}")

# Read the source to see the template
src = inspect.getsource(httpexc.HTTPMethodNotAllowed)
print("\nClass source snippet:")
for line in src.split('\n')[:20]:
    if 'template' in line.lower() or 'REQUEST_METHOD' in line:
        print(f"  {line}")