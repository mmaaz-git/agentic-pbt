#!/usr/bin/env python3
"""Minimal reproduction of the AsyncCoRedisClient export bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

# Direct import works
import limits.typing
print(f"Direct access works: {hasattr(limits.typing, 'AsyncCoRedisClient')}")

# Star import fails to get AsyncCoRedisClient
namespace = {}
exec("from limits.typing import *", namespace)
print(f"Star import includes AsyncCoRedisClient: {'AsyncCoRedisClient' in namespace}")

# Show the issue
print(f"\nAsyncCoRedisClient is defined: {hasattr(limits.typing, 'AsyncCoRedisClient')}")
print(f"AsyncCoRedisClient in __all__: {'AsyncCoRedisClient' in limits.typing.__all__}")
print("\nThis means star imports will miss this public type alias!")