#!/usr/bin/env python3
"""Minimal reproduction of the title validation bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.applicationinsights as appinsights

# This character is considered alphanumeric by Python's isalnum()
title = '¹'

print(f"Character '{title}' is alphanumeric according to Python: {title.isalnum()}")

# But troposphere rejects it as "not alphanumeric"
try:
    app = appinsights.Application(
        title,
        ResourceGroupName="TestGroup"
    )
    print("Application created successfully")
except ValueError as e:
    print(f"Error: {e}")
    
# The error message incorrectly claims the character is "not alphanumeric"
# when it actually IS alphanumeric according to Python's definition