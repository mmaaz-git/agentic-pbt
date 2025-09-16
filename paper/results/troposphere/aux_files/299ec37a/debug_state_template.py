#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.iotfleetwise as iotfleetwise

# Minimal test case
print("Testing StateTemplate with None description...")
try:
    st = iotfleetwise.StateTemplate(
        title="TestStateTemplate",
        Name="test",
        SignalCatalogArn="arn:test",
        StateTemplateProperties=["prop1"],
        Description=None  # Explicitly setting to None
    )
    print("Creation succeeded")
    print(f"Description value: {st.Description}")
except Exception as e:
    print(f"Failed to create: {e}")

print("\nTesting StateTemplate without Description...")
try:
    st2 = iotfleetwise.StateTemplate(
        title="TestStateTemplate2",
        Name="test2",
        SignalCatalogArn="arn:test2",
        StateTemplateProperties=["prop2"]
        # Not providing Description at all
    )
    print("Creation succeeded")
    print(f"Has Description attr: {hasattr(st2, 'Description')}")
except Exception as e:
    print(f"Failed to create: {e}")

print("\nTesting StateTemplate with empty string description...")
try:
    st3 = iotfleetwise.StateTemplate(
        title="TestStateTemplate3",
        Name="test3",
        SignalCatalogArn="arn:test3",
        StateTemplateProperties=["prop3"],
        Description=""  # Empty string
    )
    print("Creation succeeded")
    print(f"Description value: '{st3.Description}'")
except Exception as e:
    print(f"Failed to create: {e}")