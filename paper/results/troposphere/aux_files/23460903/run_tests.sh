#!/bin/bash
cd /root/hypothesis-llm/worker_/12
export PYTHONPATH=/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages:$PYTHONPATH
/root/hypothesis-llm/envs/troposphere_env/bin/python3 -m pytest test_iotcoredeviceadvisor.py -v --tb=short