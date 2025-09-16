#!/usr/bin/env python3
import sys
import inspect

# Add the dagster-postgres environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-postgres_env/lib/python3.13/site-packages')

import dagster_postgres.storage
import dagster_postgres.utils

def analyze_module(module, name):
    print(f"\n### Analyzing {name} ###")
    print(f"Module file: {module.__file__}")
    
    # Get all members
    members = inspect.getmembers(module)
    
    print("\nClasses:")
    for member_name, member_obj in members:
        if inspect.isclass(member_obj) and member_obj.__module__ == module.__name__:
            print(f"  - {member_name}")
            if member_obj.__doc__:
                first_line = member_obj.__doc__.strip().split('\n')[0]
                print(f"    Doc: {first_line[:80]}...")
            
            # Get methods
            methods = [m for m in inspect.getmembers(member_obj) if inspect.ismethod(m[1]) or inspect.isfunction(m[1])]
            public_methods = [m for m in methods if not m[0].startswith('_')]
            print(f"    Public methods: {[m[0] for m in public_methods[:5]]}")
    
    print("\nFunctions:")
    for member_name, member_obj in members:
        if inspect.isfunction(member_obj) and member_obj.__module__ == module.__name__:
            print(f"  - {member_name}")
            sig = inspect.signature(member_obj)
            print(f"    Signature: {sig}")
            if member_obj.__doc__:
                first_line = member_obj.__doc__.strip().split('\n')[0]
                print(f"    Doc: {first_line[:80]}...")

# Analyze both modules
analyze_module(dagster_postgres.storage, "dagster_postgres.storage")
analyze_module(dagster_postgres.utils, "dagster_postgres.utils")

# Check imports
print("\n### Key Imports in storage.py ###")
print("- DagsterStorage (base class)")
print("- PostgresEventLogStorage")
print("- PostgresRunStorage")
print("- PostgresScheduleStorage")
print("- ConfigurableClass")

# Analyze DagsterPostgresStorage specifically
print("\n### DagsterPostgresStorage Details ###")
dps = dagster_postgres.storage.DagsterPostgresStorage
print(f"Signature: {inspect.signature(dps.__init__)}")
print("\nProperties:")
for prop_name in ['inst_data', 'event_log_storage', 'run_storage', 'schedule_storage', 
                   'event_storage_data', 'run_storage_data', 'schedule_storage_data']:
    if hasattr(dps, prop_name):
        prop = getattr(dps, prop_name)
        if isinstance(prop, property):
            print(f"  - {prop_name}: property")