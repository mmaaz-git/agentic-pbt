#!/usr/bin/env python3
"""Investigate the Awaitable import issue"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import limits.typing
import typing
from collections.abc import Awaitable as AbcAwaitable, Callable as AbcCallable, Iterable as AbcIterable

print("Investigation of import inconsistency in limits.typing")
print("=" * 60)

# Check Awaitable
print("\n1. Awaitable:")
limits_awaitable = getattr(limits.typing, 'Awaitable', None)
typing_awaitable = getattr(typing, 'Awaitable', None)
print(f"   limits.typing.Awaitable: {limits_awaitable}")
print(f"   typing.Awaitable: {typing_awaitable}")
print(f"   collections.abc.Awaitable: {AbcAwaitable}")
print(f"   Are they the same?")
print(f"     limits vs typing: {limits_awaitable is typing_awaitable}")
print(f"     limits vs abc: {limits_awaitable is AbcAwaitable}")

# Check Callable
print("\n2. Callable:")
limits_callable = getattr(limits.typing, 'Callable', None)
typing_callable = getattr(typing, 'Callable', None)
print(f"   limits.typing.Callable: {limits_callable}")
print(f"   typing.Callable: {typing_callable}")
print(f"   collections.abc.Callable: {AbcCallable}")
print(f"   Are they the same?")
print(f"     limits vs typing: {limits_callable is typing_callable}")
print(f"     limits vs abc: {limits_callable is AbcCallable}")

# Check Iterable
print("\n3. Iterable:")
limits_iterable = getattr(limits.typing, 'Iterable', None)
typing_iterable = getattr(typing, 'Iterable', None)
print(f"   limits.typing.Iterable: {limits_iterable}")
print(f"   typing.Iterable: {typing_iterable}")
print(f"   collections.abc.Iterable: {AbcIterable}")
print(f"   Are they the same?")
print(f"     limits vs typing: {limits_iterable is typing_iterable}")
print(f"     limits vs abc: {limits_iterable is AbcIterable}")

print("\n" + "=" * 60)
print("Analysis:")
print("-" * 60)

# Check the actual imports in the file
print("\nFrom limits/typing.py line 4:")
print("from collections.abc import Awaitable, Callable, Iterable")
print("\nFrom limits/typing.py __all__ list (lines 102-127):")
print("Exports include: 'Awaitable', 'Callable', 'Iterable'")

print("\nThe issue:")
print("- limits.typing imports from collections.abc")
print("- But typing module also has Awaitable, Callable, Iterable")
print("- These are different objects in Python 3.9+")
print("\nThis is not necessarily a bug - it's a design choice.")
print("The module is correctly exporting what it imports.")