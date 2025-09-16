#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.inspectorv2 import *
from troposphere import Template
import inspect

# Explore the classes in the module
classes = []
initial_globals = list(globals().items())
for name, obj in initial_globals:
    if inspect.isclass(obj) and hasattr(obj, 'props'):
        classes.append((name, obj))
        
print("Classes found in troposphere.inspectorv2:")
for name, cls in classes:
    print(f"\n{name}:")
    print(f"  props: {cls.props}")
    if hasattr(cls, 'resource_type'):
        print(f"  resource_type: {cls.resource_type}")
    
# Test instantiation
print("\n\nTesting instantiation:")

# Try creating a Time object
try:
    t = Time(TimeOfDay="12:00", TimeZone="UTC")
    print(f"Time object created: {t}")
    print(f"Time properties: {t.properties}")
except Exception as e:
    print(f"Error creating Time: {e}")

# Try creating a DateFilter
try:
    df = DateFilter(StartInclusive=1, EndInclusive=10)
    print(f"DateFilter created: {df}")
    print(f"DateFilter properties: {df.properties}")
except Exception as e:
    print(f"Error creating DateFilter: {e}")

# Try creating a NumberFilter
try:
    nf = NumberFilter(LowerInclusive=1.5, UpperInclusive=10.5)
    print(f"NumberFilter created: {nf}")
    print(f"NumberFilter properties: {nf.properties}")
except Exception as e:
    print(f"Error creating NumberFilter: {e}")

# Try PortRangeFilter
try:
    prf = PortRangeFilter(BeginInclusive=80, EndInclusive=443)
    print(f"PortRangeFilter created: {prf}")
    print(f"PortRangeFilter properties: {prf.properties}")
except Exception as e:
    print(f"Error creating PortRangeFilter: {e}")

# Test validation behavior
print("\n\nTesting validation behavior:")

# Test with invalid integer
try:
    prf = PortRangeFilter(BeginInclusive="not_an_int", EndInclusive=443)
    print(f"PortRangeFilter with invalid int created: {prf.properties}")
except Exception as e:
    print(f"Error with invalid int: {type(e).__name__}: {e}")

# Test with invalid double
try:
    nf = NumberFilter(LowerInclusive="not_a_double", UpperInclusive=10.5)
    print(f"NumberFilter with invalid double created: {nf.properties}")
except Exception as e:
    print(f"Error with invalid double: {type(e).__name__}: {e}")

# Test required properties
print("\n\nTesting required properties:")
try:
    # CisTargets requires AccountIds and TargetResourceTags
    ct = CisTargets()
    print(f"CisTargets without required props: {ct.properties}")
except Exception as e:
    print(f"Error creating CisTargets without required: {type(e).__name__}: {e}")

try:
    # StringFilter requires Comparison and Value
    sf = StringFilter(Comparison="EQUALS")
    print(f"StringFilter with only Comparison: {sf.properties}")
except Exception as e:
    print(f"Error creating StringFilter with missing required: {type(e).__name__}: {e}")