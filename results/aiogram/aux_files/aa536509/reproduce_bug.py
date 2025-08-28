"""Minimal reproduction of the whitespace normalization bug"""

from aiogram.filters.command import Command

# User sends a command with double space (common when typing fast)
user_input = "/start  John"

# Parse the command
cmd_filter = Command("start")
cmd_obj = cmd_filter.extract_command(user_input)

# Try to reconstruct the original
reconstructed = cmd_obj.text

print(f"Original:      {user_input!r}")
print(f"Reconstructed: {reconstructed!r}")
print(f"Match:         {reconstructed == user_input}")

assert reconstructed == user_input, "CommandObject.text fails to preserve original whitespace"