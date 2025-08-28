#!/bin/bash
echo "Running simple property tests for google.oauth2..."
echo "============================================="

echo -e "\n>>> Running simple_test.py"
/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/bin/python3 simple_test.py

echo -e "\n>>> Running test_expiry.py"
/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/bin/python3 test_expiry.py

echo -e "\n>>> Running test_sts.py"
/root/hypothesis-llm/envs/google-cloud-recaptcha-enterprise_env/bin/python3 test_sts.py