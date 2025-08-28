import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages/')

from hypothesis import settings
import pytest

# Import all tests
from test_dagster_pandas_properties import *
from test_edge_cases import *

if __name__ == "__main__":
    # Run with more examples
    settings.register_profile("thorough", max_examples=500)
    settings.load_profile("thorough")
    
    pytest.main(["-v", "--tb=short", "-k", "not extreme_numeric"])