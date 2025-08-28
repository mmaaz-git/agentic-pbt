#!/bin/bash
cd /root/hypothesis-llm/worker_/8
/root/hypothesis-llm/envs/yq_env/bin/python3 -m pytest test_yq_properties.py -v --tb=short