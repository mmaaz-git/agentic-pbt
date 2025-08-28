#!/bin/bash

# Test the module inline
/root/hypothesis-llm/envs/troposphere_env/bin/python3 -c "
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Import and test
import troposphere.greengrassv2 as ggv2
from troposphere.validators import boolean

# Test boolean validator
print('Testing boolean validator...')
try:
    assert boolean(True) == True
    assert boolean('true') == True
    assert boolean(1) == True
    assert boolean(0) == False
    print('✓ Boolean validator works')
except Exception as e:
    print(f'✗ Boolean validator failed: {e}')

# Test object creation
print('Testing ComponentPlatform...')
try:
    p = ggv2.ComponentPlatform(Name='Linux', Attributes={'os': 'linux'})
    d = p.to_dict()
    print('✓ ComponentPlatform works')
except Exception as e:
    print(f'✗ ComponentPlatform failed: {e}')

# Test required properties
print('Testing IoTJobAbortCriteria...')
try:
    c = ggv2.IoTJobAbortCriteria(
        Action='CANCEL',
        FailureType='FAILED',
        MinNumberOfExecutedThings=1,
        ThresholdPercentage=50.0
    )
    d = c.to_dict()
    print('✓ IoTJobAbortCriteria works')
except Exception as e:
    print(f'✗ IoTJobAbortCriteria failed: {e}')

print('Basic tests complete')
"