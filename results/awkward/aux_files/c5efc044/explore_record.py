#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import inspect
import awkward as ak

# Get info about Record class
print('=== Record Class Methods ===')
for name, method in inspect.getmembers(ak.record.Record):
    if not name.startswith('_') and callable(method):
        try:
            sig = inspect.signature(method)
            print(f'{name}: {sig}')
        except:
            print(f'{name}: (cannot get signature)')

print('\n=== Record Class Properties ===')
for name, prop in inspect.getmembers(ak.record.Record):
    if not name.startswith('_') and isinstance(prop, property):
        docline = prop.fget.__doc__.splitlines()[0] if prop.fget and prop.fget.__doc__ else ""
        print(f'{name}: {docline[:80]}')

# Check what RecordArray is
print('\n=== RecordArray ===')
print(f"RecordArray type: {type(ak.contents.RecordArray)}")
print(f"RecordArray docstring first line: {ak.contents.RecordArray.__doc__.splitlines()[0] if ak.contents.RecordArray.__doc__ else ''}")