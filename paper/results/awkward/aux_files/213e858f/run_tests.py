#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

# Import the test module
import test_awkward_types_properties

# Run the tests
test_awkward_types_properties.run_all_tests()