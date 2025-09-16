#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.limits import RateLimitItemPerSecond

limit1 = RateLimitItemPerSecond(amount=1, multiples=1, namespace="NS1")
limit2 = RateLimitItemPerSecond(amount=1, multiples=1, namespace="NS2")

print(f"limit1: {limit1} (namespace: {limit1.namespace})")
print(f"limit2: {limit2} (namespace: {limit2.namespace})")
print(f"limit1 == limit2: {limit1 == limit2}")
print(f"hash(limit1): {hash(limit1)}")
print(f"hash(limit2): {hash(limit2)}")

if limit1 == limit2:
    print("\nBug confirmed: Two rate limits with different namespaces are considered equal!")
    print("This violates the hash-equality contract since they have different hashes.")
else:
    print("\nNo bug - limits with different namespaces are correctly unequal")