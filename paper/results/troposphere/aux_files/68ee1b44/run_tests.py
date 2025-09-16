"""Run property-based tests for troposphere.iotfleethub"""

import sys
import os

# Add the troposphere env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Now import and run the tests
import pytest

# Run pytest
exit_code = pytest.main(['-v', 'test_iotfleethub_properties.py'])
sys.exit(exit_code)