#!/bin/bash
export PYTHONPATH=/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages:$PYTHONPATH
cd /root/hypothesis-llm/worker_/1
/root/hypothesis-llm/envs/troposphere_env/bin/python3 -m pytest test_billingconductor_properties.py -v --tb=short