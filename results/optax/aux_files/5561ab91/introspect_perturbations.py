#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/optax_env/lib/python3.13/site-packages')

import inspect
import optax.perturbations as pert

# Get all public functions and classes
members = inspect.getmembers(pert, lambda x: not x.__name__.startswith('_') if hasattr(x, '__name__') else False)

print("=== Module Overview ===")
print(f"Module file: {pert.__file__}")
print(f"Module docstring: {pert.__doc__}")

print("\n=== Public Members ===")
for name, obj in members:
    print(f"\n{name}: {type(obj)}")
    if hasattr(obj, '__doc__') and obj.__doc__:
        print(f"  Docstring (first line): {obj.__doc__.split(chr(10))[0]}")
    
    if inspect.isfunction(obj) or inspect.ismethod(obj):
        try:
            sig = inspect.signature(obj)
            print(f"  Signature: {sig}")
        except:
            pass
    
    if inspect.isclass(obj):
        methods = [m for m in dir(obj) if not m.startswith('_')]
        print(f"  Public methods: {methods}")
        for method_name in methods:
            method = getattr(obj, method_name)
            if callable(method):
                try:
                    sig = inspect.signature(method)
                    print(f"    {method_name}{sig}")
                except:
                    pass

# Check specific properties
print("\n=== Specific Analysis ===")

# Analyze Normal class
print("\nNormal class:")
n = pert.Normal()
print(f"  sample method: {inspect.signature(n.sample)}")
print(f"  log_prob method: {inspect.signature(n.log_prob)}")

# Analyze Gumbel class  
print("\nGumbel class:")
g = pert.Gumbel()
print(f"  sample method: {inspect.signature(g.sample)}")
print(f"  log_prob method: {inspect.signature(g.log_prob)}")

# Analyze make_perturbed_fun
print("\nmake_perturbed_fun:")
print(f"  Signature: {inspect.signature(pert.make_perturbed_fun)}")
print(f"  Defaults: num_samples={1000}, sigma={0.1}, noise=Gumbel(), use_baseline={True}")

# Check for any hidden implementation details
print("\n=== Implementation Module ===")
import optax.perturbations._make_pert as impl
impl_members = [m for m in dir(impl) if not m.startswith('__')]
print(f"Implementation members: {impl_members}")