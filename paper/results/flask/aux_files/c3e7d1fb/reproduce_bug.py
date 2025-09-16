import logging
import flask.logging

# Simulate what pytest does - add handlers with level 0 to root
root = logging.getLogger()
root_handler = logging.StreamHandler()
root_handler.setLevel(0)  # NOTSET
root.addHandler(root_handler)

# Create a test logger with a handler that won't handle WARNING messages
logger = logging.getLogger('test_logger')
logger.handlers.clear()

# Add a handler at ERROR level
handler = logging.StreamHandler()
handler.setLevel(logging.ERROR)  # 40
logger.addHandler(handler)

# Logger's effective level is WARNING (30) from root
effective_level = logger.getEffectiveLevel()
print(f"Logger effective level: {effective_level} ({logging.getLevelName(effective_level)})")
print(f"Logger handler level: {handler.level} ({logging.getLevelName(handler.level)})")
print(f"Root handler level: {root_handler.level} ({logging.getLevelName(root_handler.level)})")

# has_level_handler should return False because:
# - The logger's handler is at ERROR (40) which won't handle WARNING (30) messages  
# - The root's handler at NOTSET (0) will pass messages through but that doesn't mean
#   the logger's ERROR handler will handle them
result = flask.logging.has_level_handler(logger)
print(f"\nhas_level_handler result: {result}")
print(f"Expected: False (handler at ERROR won't handle WARNING messages)")

if result:
    print("\nBUG: has_level_handler incorrectly returns True!")
    print("The function is checking if root handler level (0) <= effective level (30)")
    print("But a NOTSET handler doesn't actually 'handle' messages - it passes them through")