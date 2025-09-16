#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiogram_env/lib/python3.13/site-packages')

import inspect
import aiogram.loggers

print("Module file:", aiogram.loggers.__file__)
print("\nModule members:")
members = inspect.getmembers(aiogram.loggers)
for name, obj in members:
    if not name.startswith('__'):
        print(f"  {name}: {type(obj)}")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"    Doc: {obj.__doc__[:100]}...")

print("\nLogger objects:")
print(f"  dispatcher: {aiogram.loggers.dispatcher}")
print(f"  event: {aiogram.loggers.event}")
print(f"  middlewares: {aiogram.loggers.middlewares}")
print(f"  webhook: {aiogram.loggers.webhook}")
print(f"  scene: {aiogram.loggers.scene}")

print("\nChecking logger properties:")
for logger_name in ['dispatcher', 'event', 'middlewares', 'webhook', 'scene']:
    logger = getattr(aiogram.loggers, logger_name)
    print(f"\n{logger_name} logger:")
    print(f"  Name: {logger.name}")
    print(f"  Level: {logger.level}")
    print(f"  Effective level: {logger.getEffectiveLevel()}")
    print(f"  Handlers: {logger.handlers}")
    print(f"  Parent: {logger.parent}")
    print(f"  Propagate: {logger.propagate}")