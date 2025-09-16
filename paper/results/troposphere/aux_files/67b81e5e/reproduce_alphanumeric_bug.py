#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.devopsguru import NotificationChannel, NotificationChannelConfig, SnsChannelConfig

# Minimal reproduction of the bug
config = NotificationChannelConfig(Sns=SnsChannelConfig(TopicArn="arn:aws:sns:us-east-1:123456789012:test"))

# This title IS alphanumeric according to Python
title = 'µ'  # Greek letter mu

print(f"Testing title: '{title}'")
print(f"Python's isalnum(): {title.isalnum()}")  # Returns True

try:
    nc = NotificationChannel(title, Config=config)
    nc.to_dict()
    print("Result: Title accepted")
except ValueError as e:
    print(f"Result: {e}")
    
print("\nBUG: The error says 'not alphanumeric' but 'µ' IS alphanumeric!")
print("The validation uses regex ^[a-zA-Z0-9]+$ which only accepts ASCII.")