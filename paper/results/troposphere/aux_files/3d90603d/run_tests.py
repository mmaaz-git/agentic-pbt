#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["-xvs", "test_pcaconnectorscep.py"]))