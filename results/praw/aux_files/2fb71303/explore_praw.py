#!/root/hypothesis-llm/envs/praw_env/bin/python

import praw
import praw.models
import inspect
import os

print("praw version:", praw.__version__)
print("praw.models file:", praw.models.__file__)
print()

# Get all members of praw.models
print("Members of praw.models:")
members = inspect.getmembers(praw.models)
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  {name}: {obj_type}")