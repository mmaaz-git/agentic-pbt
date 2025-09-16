#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.mediaconvert as mc
from troposphere import AWSObject, AWSProperty

# Get all classes in the module
classes = inspect.getmembers(mc, inspect.isclass)

print("Classes in troposphere.mediaconvert:")
for name, cls in classes:
    if issubclass(cls, (AWSObject, AWSProperty)):
        print(f"\n{name}: {cls}")
        print(f"  Base classes: {cls.__bases__}")
        print(f"  Props: {cls.props}")
        if hasattr(cls, 'resource_type'):
            print(f"  Resource type: {cls.resource_type}")
        
# Let's test instantiation
print("\n\n=== Testing instantiation ===")

# Test AccelerationSettings
print("\nAccelerationSettings:")
try:
    acc = mc.AccelerationSettings(Mode="ENABLED")
    print(f"  Success with Mode='ENABLED': {acc.to_dict()}")
except Exception as e:
    print(f"  Failed with Mode='ENABLED': {e}")

try:
    acc_invalid = mc.AccelerationSettings()
    print(f"  Created without required Mode: {acc_invalid}")
except Exception as e:
    print(f"  Expected failure without Mode: {e}")

# Test HopDestination
print("\nHopDestination:")
try:
    hop = mc.HopDestination(Priority=1, Queue="test-queue", WaitMinutes=5)
    print(f"  Success with all params: {hop.to_dict()}")
except Exception as e:
    print(f"  Failed: {e}")

# Test JobTemplate
print("\nJobTemplate:")
try:
    jt = mc.JobTemplate("MyJobTemplate", SettingsJson={"test": "value"})
    print(f"  Success with title and SettingsJson: {jt.title}")
    print(f"  to_dict(): {jt.to_dict()}")
except Exception as e:
    print(f"  Failed: {e}")

try:
    jt_no_settings = mc.JobTemplate("MyJobTemplate2")
    print(f"  Created without required SettingsJson: {jt_no_settings.title}")
    dict_result = jt_no_settings.to_dict()
    print(f"  to_dict() succeeded without required field: {dict_result}")
except Exception as e:
    print(f"  Expected failure without SettingsJson: {e}")

# Test with validation disabled
print("\nTesting with validation disabled:")
try:
    jt_no_val = mc.JobTemplate("NoVal", validation=False)
    print(f"  Created without SettingsJson (validation=False): {jt_no_val.title}")
    dict_result = jt_no_val.to_dict(validation=False)
    print(f"  to_dict(validation=False) result: {dict_result}")
except Exception as e:
    print(f"  Failed even with validation=False: {e}")