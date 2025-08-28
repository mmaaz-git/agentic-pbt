#!/usr/bin/env python3
import sys
sys.path.append('/root/hypothesis-llm/envs/slack_env/lib/python3.13/site-packages')

import slack

container = slack.Container()
container.register("test", 42)
print(f"Registered value: 42")
result = container.provide("test")
print(f"Retrieved value: {result}")