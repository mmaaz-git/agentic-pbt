#!/usr/bin/env python3
"""Minimal reproducers for bugs found in rpdk.java"""

import sys
sys.path.append('/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.java.utils import validate_namespace, validate_codegen_model
from rpdk.java.resolver import translate_type
from rpdk.core.jsonutils.resolver import ResolvedType, ContainerType
from rpdk.core.exceptions import WizardValidationError

# Bug 1: validate_namespace accepts invalid underscore-only segments
print("Bug 1: validate_namespace accepts '__' as valid namespace")
validator = validate_namespace(("default",))
try:
    result = validator("__")
    print(f"  ERROR: Accepted '__' as valid, returned: {result}")
    print(f"  This violates the pattern [_a-z][_a-z0-9]+ which requires at least one letter")
except WizardValidationError:
    print("  OK: Correctly rejected '__'")

print()

# Bug 2: validate_namespace accepts '_0' which may not match pattern
print("Bug 2: validate_namespace accepts '_0' as valid namespace")
validator = validate_namespace(("default",))  
try:
    result = validator("_0")
    print(f"  POTENTIAL BUG: Accepted '_0' as valid, returned: {result}")
    print(f"  Pattern [_a-z][_a-z0-9]+ suggests at least 2 chars, '_0' is 2 chars but starts with underscore")
except WizardValidationError:
    print("  OK: Correctly rejected '_0'")

print()

# Bug 3: translate_type crashes with None inner type
print("Bug 3: translate_type crashes with None inner type")
resolved = ResolvedType(ContainerType.LIST, None)
try:
    result = translate_type(resolved)
    print(f"  Result: {result}")
except AttributeError as e:
    print(f"  ERROR: AttributeError raised: {e}")
    print(f"  Function should handle None gracefully, not crash")

print()

# Bug 4: validate_codegen_model accepts '1\\n' (with newline)
print("Bug 4: validate_codegen_model accepts '1\\n' (with newline)")
validator = validate_codegen_model("1")
try:
    result = validator("1\n")
    print(f"  ERROR: Accepted '1\\n' as valid, returned: {repr(result)}")
    print(f"  Pattern ^[1-2]$ should not match strings with newlines")
except WizardValidationError:
    print("  OK: Correctly rejected '1\\n'")