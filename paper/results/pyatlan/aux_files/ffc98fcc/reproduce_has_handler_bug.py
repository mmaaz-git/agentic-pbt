#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

import logging
from pyatlan.pkg.utils import has_handler

# Create a logger hierarchy
parent_logger = logging.getLogger("test.parent")
child_logger = logging.getLogger("test.parent.child")

# Add a StreamHandler to parent
handler = logging.StreamHandler()
parent_logger.addHandler(handler)

print(f"Parent logger handlers: {parent_logger.handlers}")
print(f"Child logger handlers: {child_logger.handlers}")

# Check if child finds the handler
print(f"Child has StreamHandler (expected True): {has_handler(child_logger, logging.StreamHandler)}")

# Remove the handler from parent
parent_logger.removeHandler(handler)

print(f"\nAfter removing handler:")
print(f"Parent logger handlers: {parent_logger.handlers}")
print(f"Child logger handlers: {child_logger.handlers}")

# Check again - should be False
result = has_handler(child_logger, logging.StreamHandler)
print(f"Child has StreamHandler (expected False): {result}")

if result:
    print("\nBUG: The function still finds a handler after it was removed!")
    print("This might be due to other StreamHandlers in the logger hierarchy")