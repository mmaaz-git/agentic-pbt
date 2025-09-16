#!/usr/bin/env python3
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages")

# Execute the tests inline
exec(open("/root/hypothesis-llm/worker_/1/run_jax_tests.py").read())