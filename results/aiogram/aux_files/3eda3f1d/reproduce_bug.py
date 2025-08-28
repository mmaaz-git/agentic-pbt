#!/usr/bin/env python3
"""Minimal reproduction of the JSON serialization bug in aiogram.methods"""

from aiogram.methods import SendMessage

# Create a SendMessage instance with minimal required fields
msg = SendMessage(chat_id=123456789, text="Hello World")

# This works - returns a dict with Default objects
dumped = msg.model_dump()
print(f"model_dump() works: {type(dumped)}")

# This fails - cannot serialize Default objects to JSON
try:
    json_str = msg.model_dump_json()
    print(f"model_dump_json() result: {json_str}")
except Exception as e:
    print(f"model_dump_json() failed: {e}")