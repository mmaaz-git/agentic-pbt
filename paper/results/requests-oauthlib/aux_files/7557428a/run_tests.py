import sys
import os

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

# Import and run the tests
import pytest

# Run pytest on our test file
sys.exit(pytest.main(['test_oauth1_auth_properties.py', '-v']))