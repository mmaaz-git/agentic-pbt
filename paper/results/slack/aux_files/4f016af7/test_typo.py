#!/usr/bin/env python3
import sys
sys.path.append('/root/hypothesis-llm/envs/slack_env/lib/python3.13/site-packages')

import slack
import inspect

# Fix the getargspec issue temporarily to test the typo
original_getargspec = lambda fn: inspect.getfullargspec(fn)
inspect.getargspec = original_getargspec

# Now test the typo in exception name
try:
    def test_func(required_param):
        return required_param
    
    slack.invoke(test_func, {})
    print("ERROR: Should have raised exception")
except slack.ParamterMissingError as e:
    print(f"Caught ParamterMissingError (note the typo): {e}")
except Exception as e:
    print(f"Caught unexpected exception: {type(e).__name__}: {e}")